from fastapi import HTTPException
from supabase import create_async_client

from supabase_config import get_supabase_config


async def get_all_representantes(env, access_token: str):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)
        response = await (
            supabase.table("representante")
            .select("id_representante,id_profesor,id_deporte")
            .execute()
        )
        return response.data
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error al obtener los representantes.",
        ) from error
    finally:
        await supabase.postgrest.aclose()
