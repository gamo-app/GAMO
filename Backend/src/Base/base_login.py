from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from model import LoginData
import json
from supabase_config import get_supabase_config
from supabase import create_async_client
from workers import fetch

router = APIRouter()

ACCESS_COOKIE = "gamo_access" # este se encarga de la sesion actual
REFRESH_COOKIE = "gamo_refresh" # este se encarga de la sesion por dias 

# Configuración de sesión
ACCESS_MAX_AGE = 60 * 60       # 1 hora
REFRESH_MAX_AGE = 60 * 60 * 24 * 7  # 7 días

def headers_supabase(key: str, access_token: str | None = None):
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    return headers


def establecer_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int = ACCESS_MAX_AGE,
):
    # En desarrollo local (HTTP en lugar de HTTPS), SameSite debe ser "lax"
    # y Secure debe ser False.
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=True,     # False para HTTP local
        samesite="none",   # Lax permite cookies si la navegación principal o fetch lo permite en local
        path="/",
    )

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=REFRESH_MAX_AGE,
        httponly=True,
        secure=True,     
        samesite="none",
        path="/",
    )

def eliminar_cookies(response: Response):
    for nombre in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            key=nombre,
            path="/",
            secure=True,
            httponly=True,
            samesite="none",
        )

async def obtener_usuario_auth(url, key, access_token):
    respuesta = await fetch(
        f"{url}/auth/v1/user",
        headers=headers_supabase(key, access_token),
    )

    if not respuesta.ok:
        return None

    return await respuesta.json()


# ------------------------------------------
# LOGIN
# ------------------------------------------

async def login( env, datos: LoginData, response: Response, ):
    url, key = get_supabase_config(env)
    #cambiar key por access_token
    try:
        respuesta = await fetch(
            f"{url}/auth/v1/token?grant_type=password",
            headers=headers_supabase(key),
            method="POST",
            body=json.dumps({
                "email": str(datos.email),
                "password": str(datos.password),
            }),
        )

        if not respuesta.ok:
            # No revelar si falló el correo o la contraseña.
            raise HTTPException(
                status_code=401,
                detail="Correo electrónico o contraseña incorrectos.",
            )

        sesion = await respuesta.json()

        access_token = sesion.get("access_token")
        refresh_token = sesion.get("refresh_token")
        expires_in = int(sesion.get("expires_in", ACCESS_MAX_AGE))

        if not access_token or not refresh_token:
            raise HTTPException(
                status_code=502,
                detail="Supabase no devolvió una sesión válida.",
            )

        establecer_cookies(
            response,
            access_token,
            refresh_token,
            expires_in,
        )

        response.headers["Cache-Control"] = "no-store"

        return {
            "mensaje": "Inicio de sesión correcto.",
            "usuario": {
                "id": sesion.get("user", {}).get("id"),
                "email": sesion.get("user", {}).get("email"),
            },
        }

    except HTTPException:
        raise
    except Exception as error:
        print(f"Error interno en login: {type(error).__name__}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo iniciar sesión.",
        )


# ------------------------------------------
# CONSULTAR SESION
# ------------------------------------------
async def obtener_datos_usuario(env, uuid_usuario: str, access_token: str):
    url, key = get_supabase_config(env)
    cliente = await create_async_client(url, key)

    try:
        cliente.postgrest.auth(access_token)
        resultado = await (
            cliente.table("usuario")
            .select(
                "uuid_usuario,DNI,nombre,apellido,fecha_nacimiento,primer_ingreso,"
                "rol:id_rol(id_rol,nombre,permisos)"
            )
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )

        if not resultado.data:
            return None

        usuario = resultado.data[0]
        rol = usuario.get("rol")
        if isinstance(rol, list):
            usuario["rol"] = rol[0] if rol else None

        return usuario
    finally:
        await cliente.postgrest.aclose()


async def obtener_sesion(env, request: Request):
    env = request.scope["env"]
    url, key = get_supabase_config(env)

    access_token = request.cookies.get(ACCESS_COOKIE)
    refresh_token = request.cookies.get(REFRESH_COOKIE)

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión activa.",
        )

    # 1. Validar la sesión actual en Supabase Auth
    usuario_auth = await obtener_usuario_auth(
        url, key, access_token
    )

    sesion_renovada = None

    # 2. Renovar solamente si el access token no es válido
    if not usuario_auth:
        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail="La sesión expiró. Iniciá sesión nuevamente.",
            )

        respuesta = await fetch(
            f"{url}/auth/v1/token?grant_type=refresh_token",
            headers=headers_supabase(key),
            method="POST",
            body=json.dumps({
                "refresh_token": refresh_token,
            }),
        )

        if not respuesta.ok:
            raise HTTPException(
                status_code=401,
                detail="La sesión expiró. Iniciá sesión nuevamente.",
            )

        sesion_renovada = await respuesta.json()

        access_token = sesion_renovada.get("access_token")
        refresh_token = sesion_renovada.get("refresh_token")

        if not access_token or not refresh_token:
            raise HTTPException(
                status_code=502,
                detail="No se pudo renovar la sesión.",
            )

        # Validar el usuario con el token renovado
        usuario_auth = await obtener_usuario_auth(
            url, key, access_token
        )

        if not usuario_auth:
            raise HTTPException(
                status_code=401,
                detail="No se pudo validar la sesión renovada.",
            )

    # 3. Obtener el UUID del usuario autenticado
    uuid_usuario = usuario_auth.get("id")

    if not uuid_usuario:
        raise HTTPException(
            status_code=401,
            detail="No se pudo identificar al usuario autenticado.",
        )

    # 4. Obtener los datos de GAMO y su rol
    usuario_gamo = await obtener_datos_usuario(
        env,
        uuid_usuario,
        access_token,
    )

    if not usuario_gamo:
        raise HTTPException(
            status_code=404,
            detail="El usuario autenticado no tiene un registro en GAMO.",
        )

    # 5. Preparar la respuesta con la estructura exacta solicitada
    datos = {
        "usuario": {
            **usuario_gamo,
            "email": usuario_auth.get("email"),
        }
    }

    response = JSONResponse(content=datos)
    response.headers["Cache-Control"] = "no-store"

    # 6. Actualizar cookies solamente si se renovó la sesión
    if sesion_renovada:
        establecer_cookies(
            response,
            access_token,
            refresh_token,
            int(
                sesion_renovada.get(
                    "expires_in",
                    ACCESS_MAX_AGE,
                )
            ),
        )

    return response

async def logout(env, request: Request, response: Response):
    url, key = get_supabase_config(env)

    access_token = request.cookies.get(ACCESS_COOKIE)

    if access_token:
        resultado = await fetch(
            f"{url}/auth/v1/logout?scope=local",
            headers=headers_supabase(key, access_token),
            method="POST",
        )

        # Si Auth rechaza la sesión, igualmente limpiamos
        # las cookies locales del navegador.
        if not resultado.ok:
            print("Supabase no pudo revocar la sesión local.")

    eliminar_cookies(response)
    response.headers["Cache-Control"] = "no-store"

    return {"mensaje": "Sesión cerrada."}
