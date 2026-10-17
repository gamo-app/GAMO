from supabase import create_async_client
from supabase_config import get_supabase_config


async def get_all_clases(env, access_token: str):
    url, key = get_supabase_config(env)

    supabase = await create_async_client(url, key)

    # Usar el token del usuario para respetar las políticas RLS
    supabase.postgrest.auth(access_token)

    response = (
        await supabase
        .table("clase")
        .select("*")
        .execute()
    )

    return response.data