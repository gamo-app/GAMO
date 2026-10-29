from fastapi import Depends, HTTPException, Request
from workers import fetch
from supabase_config import get_supabase_config
from Base.base_login import obtener_datos_usuario


async def validar_sesion(request: Request) -> str:
    access_token = request.cookies.get("gamo_access")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión activa.",
        )

    request.state.usuario_auth = await validar_jwt(
        request.scope["env"],
        access_token,
    )
    return access_token


async def validar_acceso_listado_socios(
    request: Request,
    access_token: str = Depends(validar_sesion),
) -> str:
    usuario_auth = request.state.usuario_auth
    usuario = await obtener_datos_usuario(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )

    rol = (usuario or {}).get("rol") or {}
    nombre_rol = rol.get("nombre", "")
    if (
        not isinstance(nombre_rol, str)
        or not nombre_rol.strip()
        or nombre_rol.strip().casefold() == "socio"
    ):
        raise HTTPException(
            status_code=403,
            detail="No tenés permiso para consultar el listado de socios.",
        )

    return access_token


async def validar_jwt(env, access_token: str):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión activa."
        )

    url, key = get_supabase_config(env)

    response = await fetch(
        f"{url}/auth/v1/user",
        method="GET",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {access_token}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=401,
            detail="La sesión no es válida o expiró."
        )

    usuario_auth = await response.json()

    if not usuario_auth or not usuario_auth.get("id"):
        raise HTTPException(
            status_code=401,
            detail="La sesión no es válida."
        )

    return usuario_auth
