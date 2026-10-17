from supabase import create_async_client
from supabase_config import get_supabase_config
from fastapi import HTTPException

async def get_all_socios(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("socio")
            .select("*")
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data


async def socio_all_estado(env, rol: str, estado: str, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("socio")
            .select(
                "id_socio,estado,"
                "persona!inner("
                    "telefono,nombre,apellido,"
                    "usuario!inner("
                        "email,"
                        "grupo_usuario!inner(nombre)"
                    ")"
                ")"
            )
            .eq("persona.usuario.grupo_usuario.nombre", rol)
            .eq("estado", estado)
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data


async def actualizar_estado_usuario_general(
    env,
    id_persona: int,
    estado: str,
    access_token: str,
):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        resultado = await supabase.rpc(
            "actualizar_estado_usuario_general",
            {
                "p_id_persona": id_persona,
                "p_nuevo_estado": estado,
            },
        ).execute()
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return {
        "status": "success",
        "message": "Estado actualizado correctamente",
        "data": resultado.data,
    }