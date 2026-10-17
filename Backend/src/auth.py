from fastapi import HTTPException, Request
from workers import fetch
from supabase_config import get_supabase_config


async def validar_sesion(request: Request) -> str:
    access_token = request.cookies.get("gamo_access")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión activa.",
        )

    await validar_jwt(request.scope["env"], access_token)
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
