
from fastapi import APIRouter, Request, Response, HTTPException
from model import LoginData
from supabase_config import get_supabase_config
from workers import fetch
from supabase import create_async_client
import json

router = APIRouter()

ACCESS_COOKIE = "gamo_access"
REFRESH_COOKIE = "gamo_refresh"

ACCESS_MAX_AGE = 60 * 60
REFRESH_MAX_AGE = 60 * 60 * 24 * 7


# ------------------------------------------
# CONFIGURACIÓN DE SUPABASE
# ------------------------------------------

def headers_supabase(key: str, access_token: str | None = None):
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    return headers


# ------------------------------------------
# COOKIES
# ------------------------------------------

def establecer_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int = ACCESS_MAX_AGE,
):
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=REFRESH_MAX_AGE,
        httponly=True,
        secure=False,
        samesite="lax",
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


# ------------------------------------------
# OBTENER USUARIO DE SUPABASE AUTH
# ------------------------------------------

async def obtener_usuario_auth(url, key, access_token):
    respuesta = await fetch(
        f"{url}/auth/v1/user",
        headers=headers_supabase(key, access_token),
    )

    if not respuesta.ok:
        return None

    return await respuesta.json()


# ------------------------------------------
# OBTENER USUARIO COMPLETO DE GAMO
# ------------------------------------------

async def obtener_usuario_gamo(
    env,
    auth_id: str,
    access_token: str,
):
    url, key = get_supabase_config(env)

    try:
        supabase = await create_async_client(url, key)

        # Ejecutar la consulta con el token del usuario.
        supabase.postgrest.auth(access_token)

        resultado = await (
            supabase
            .table("usuario")
            .select(
                "id_usuario,id_persona,id_sede,id_grupo,"
                "email,nombre_usuario,estado,"
                "persona(id_persona,dni,nombre,apellido,telefono,fecha_nacimiento),"
                "grupo_usuario(nombre,nivel,permisos),"
                "sede(id_sede,nombre)"
            )
            .eq("id_usuario", auth_id)
            .maybe_single()
            .execute()
        )

        datos = resultado.data

        if not datos:
            return None

        grupo = datos.get("grupo_usuario") or {}
        persona = datos.get("persona") or {}
        sede = datos.get("sede") or {}

        # Adaptar la estructura al formato esperado por el frontend.
        usuario = {
            "id": datos.get("id_usuario"),
            "id_persona": datos.get("id_persona"),
            "id_sede": datos.get("id_sede"),
            "id_grupo": datos.get("id_grupo"),
            "email": datos.get("email"),
            "nombre_usuario": datos.get("nombre_usuario"),
            "estado": datos.get("estado"),
            "rol": grupo.get("nombre"),
            "nivel": grupo.get("nivel"),
            "permisos": grupo.get("permisos") or {},
            "persona": {
                "dni": persona.get("dni"),
                "nombre": persona.get("nombre"),
                "apellido": persona.get("apellido"),
                "telefono": persona.get("telefono"),
                "id_persona": persona.get("id_persona"),
                "fecha_nacimiento": persona.get("fecha_nacimiento"),
            },
            "sede": {
                "nombre": sede.get("nombre"),
                "id_sede": sede.get("id_sede"),
            },
        }

        return usuario

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Error consultando usuario GAMO: "
            f"{type(error).__name__}: {str(error)}"
        )

        raise HTTPException(
            status_code=500,
            detail="No se pudo consultar el usuario de GAMO.",
        )


# ------------------------------------------
# INICIAR SESIÓN
# ------------------------------------------

async def login(
    env,
    datos: LoginData,
    request: Request,
    response: Response,
):
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
            raise HTTPException(
                status_code=401,
                detail="Correo electrónico o contraseña incorrectos.",
            )

        sesion = await respuesta.json()

        access_token = sesion.get("access_token")
        refresh_token = sesion.get("refresh_token")
        auth_user = sesion.get("user", {})
        auth_id = auth_user.get("id")

        expires_in = int(
            sesion.get("expires_in", ACCESS_MAX_AGE)
        )

        if not access_token or not refresh_token or not auth_id:
            raise HTTPException(
                status_code=502,
                detail="Supabase no devolvió una sesión válida.",
            )

        usuario_gamo = await obtener_usuario_gamo(
            env,
            auth_id,
            access_token,
        )

        if not usuario_gamo:
            raise HTTPException(
                status_code=403,
                detail="El usuario no está registrado en GAMO.",
            )

        if usuario_gamo.get("estado") != "activo":
            raise HTTPException(
                status_code=403,
                detail="El usuario está inactivo.",
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
            "usuario": usuario_gamo,
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Error interno en login: "
            f"{type(error).__name__}: {str(error)}"
        )

        raise HTTPException(
            status_code=500,
            detail="No se pudo iniciar sesión.",
        )


# ------------------------------------------
# CONSULTAR Y RENOVAR SESIÓN
# ------------------------------------------


async def obtener_sesion(env, request: Request):
    url, key = get_supabase_config(env)

    access_token = request.cookies.get(ACCESS_COOKIE)
    refresh_token = request.cookies.get(REFRESH_COOKIE)

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión activa.",
        )

    # Comprobar si el access token sigue vigente.
    usuario_auth = await obtener_usuario_auth(
        url,
        key,
        access_token,
    )

    if usuario_auth:
        usuario_gamo = await obtener_usuario_gamo(
            env,
            usuario_auth["id"],
            access_token,
        )

        if not usuario_gamo or usuario_gamo.get("estado") != "activo":
            raise HTTPException(
                status_code=403,
                detail="El usuario no tiene acceso a GAMO.",
            )

        return {
            "autenticado": True,
            "usuario": usuario_gamo,
        }

    # El token expiró: intentar renovarlo.
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
    auth_id = sesion.get("user", {}).get("id")

    if not access_token_nuevo or not refresh_token_nuevo or not auth_id:
        raise HTTPException(
            status_code=502,
            detail="No se pudo renovar la sesión.",
        )

    usuario_gamo = await obtener_usuario_gamo(
        env,
        auth_id,
        access_token_nuevo,
    )

    if not usuario_gamo or usuario_gamo.get("estado") != "activo":
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene acceso a GAMO.",
        )

    # Crear una respuesta con la sesión y las cookies renovadas.
    response = Response(
        content=json.dumps({
            "autenticado": True,
            "usuario": usuario_gamo,
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


# ------------------------------------------
# CERRAR SESIÓN
# ------------------------------------------

async def logout(env, request: Request, response: Response):
    url, key = get_supabase_config(env)

    access_token = request.cookies.get(ACCESS_COOKIE)

    if access_token:
        resultado = await fetch(
            f"{url}/auth/v1/logout?scope=local",
            headers=headers_supabase(key, access_token),
            method="POST",
        )

        if not resultado.ok:
            print("Supabase no pudo revocar la sesión local.")

    eliminar_cookies(response)
    response.headers["Cache-Control"] = "no-store"

    return {"mensaje": "Sesión cerrada."}


# ------------------------------------------
# RUTAS FASTAPI
# ------------------------------------------
@router.post("")
async def iniciar_sesion(
    request: Request,
    datos: LoginData,
    response: Response,
):
    env = request.scope["env"]
    return await login(env, datos, request, response)


@router.get("/auth/me")
async def consultar_sesion(request: Request):
    env = request.scope["env"]
    return await obtener_sesion(env, request)


@router.post("/logout")
async def cerrar_sesion(
    request: Request,
    response: Response,
):
    env = request.scope["env"]
    return await logout(env, request, response)