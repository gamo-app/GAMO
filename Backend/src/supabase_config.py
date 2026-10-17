import os 
from fastapi import HTTPException


def get_supabase_config(env):
    url = getattr(env, "SUPABASE_URL", None)
    key = getattr(env, "SUPABASE_KEY", None)
    if not url or not key:
        raise HTTPException(
            status_code=500,
            detail="Faltan SUPABASE_URL o SUPABASE_KEY en la configuración del Worker.",
        )

    url = url.strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]

    return url, key.strip()