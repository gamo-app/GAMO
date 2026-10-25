from supabase import create_async_client
from supabase_config import get_supabase_config
from fastapi import HTTPException
from model import UsuarioCreate

#ya no exciste mail dentro de la tabla usuario normal  
async def get_user_from_email(env, email: str, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select("*")
            .eq("email", email.strip())
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data

#cambiar por rol
async def get_user_group(env, user_id: str, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select("grupo_usuario(nombre)")
            .eq("id_usuario", user_id)
            .execute()
        )

        data = response.data

        if not data:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el usuario.",
            )

        grupo = data[0].get("grupo_usuario")

        if not grupo:
            raise HTTPException(
                status_code=404,
                detail="El usuario no tiene un grupo asignado.",
            )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return grupo["nombre"]

async def get_all_usuarios(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)

        # Usar el token del usuario para respetar las políticas RLS
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select("*")
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data



async def create_user(env, datos: UsuarioCreate):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    auth_user = None

    try:
        # 1. Crear la identidad en Supabase Auth
        respuesta = await supabase.auth.admin.create_user({
            "email": datos.email,
            "password": datos.password,
            "email_confirm": True,
        })

        auth_user = respuesta.user

        if auth_user is None:
            raise HTTPException(
                status_code=500,
                detail="No se pudo crear la identidad del usuario.",
            )

        # 2. Crear el registro en public.usuario (vinculado con el UUID de Auth)
        perfil = await (
            supabase.table("usuario")
            .insert({
                "uuid_usuario": auth_user.id,
                "DNI": datos.DNI,
                "nombre": datos.nombre,
                "apellido": datos.apellido,
                "fecha_nacimiento": datos.fecha_nacimiento.isoformat(),
                "id_rol": datos.id_rol,
            })
            .execute()
        )

        return {
            "mensaje": "Usuario creado correctamente.",
            "usuario": perfil.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        # Evitar dejar una identidad huérfana en Auth si falla la inserción en la base de datos.
        if auth_user is not None:
            try:
                await supabase.auth.admin.delete_user(auth_user.id)
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail=f"Error al crear el usuario: {str(e)}",
        )