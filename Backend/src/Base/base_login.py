from fastapi import APIRouter, Request, Response, HTTPException
from model import LoginData
import json
from supabase_config import get_supabase_config
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

async def login( env, datos: LoginData, request: Request, response: Response, ):
    url, key = get_supabase_config(env)

    try:
        respuesta = await fetch(
            f"{url}/auth/v1/token?grant_type=password",
            headers=headers_supabase(key),
            method="POST",
            body=json.dumps({
                "email": str(datos.email),
                "password": datos.password,
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

    usuario = await obtener_usuario_auth(
        url, key, access_token
    )

    if usuario:
        return {
            "autenticado": True,
            "usuario": {
                "id": usuario.get("id"),
                "email": usuario.get("email"),
            },
        }

    # El access token pudo haber expirado.
    # Intentar renovarlo usando el refresh token.
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

    sesion = await respuesta.json()

    access_token_nuevo = sesion.get("access_token")
    refresh_token_nuevo = sesion.get("refresh_token")

    if not access_token_nuevo or not refresh_token_nuevo:
        raise HTTPException(
            status_code=502,
            detail="No se pudo renovar la sesión.",
        )

    # Verificar el usuario con el token recién renovado.
    usuario = await obtener_usuario_auth(
        url, key, access_token_nuevo
    )

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="No se pudo validar la sesión renovada.",
        )

    response = Response(
        content=json.dumps({
            "autenticado": True,
            "usuario": {
                "id": usuario.get("id"),
                "email": usuario.get("email"),
            },
        }),
        media_type="application/json",
    )

    establecer_cookies(
        response,
        access_token_nuevo,
        refresh_token_nuevo,
        int(sesion.get("expires_in", ACCESS_MAX_AGE)),
    )

    response.headers["Cache-Control"] = "no-store"
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
