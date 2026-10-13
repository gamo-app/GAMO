import json
from fastapi import HTTPException
from workers import fetch

from model import SocioCreate


def get_supabase_config(env):
    url = getattr(env, "SUPABASE_URL", None)
    key = getattr(env, "SUPABASE_KEY", None)
    if not url or not key:
        raise HTTPException(
            status_code=500,
            detail="Faltan SUPABASE_URL o SUPABASE_KEY en la configuración del Worker.",
        )

    return url.rstrip("/"), key


async def get_socios(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()


async def crear_socio(env, socio: SocioCreate):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/SOCIO",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        body=json.dumps(socio.model_dump()),
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()