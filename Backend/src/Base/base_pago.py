from supabase import create_async_client
from supabase_config import get_supabase_config
from fastapi import HTTPException


async def get_all_pago(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)

        # Usar el token del usuario para respetar las políticas RLS
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("pago")
            .select("*")
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data