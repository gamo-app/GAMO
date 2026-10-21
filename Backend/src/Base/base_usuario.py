from supabase import create_async_client
from supabase_config import get_supabase_config
from fastapi import HTTPException
from model import UsuarioCreate

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
    persona_id = None

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

        # 2. Crear la persona
        persona = await (
            supabase.table("persona")
            .insert({
                "nombre": datos.nombre_usuario,
                "apellido": datos.apellido,
            })
            .execute()
        )

        persona_id = persona.data[0]["id_persona"]

        # 3. Crear el perfil de GAMO
        perfil = await (
            supabase.table("usuario")
            .insert({
                "id_usuario": auth_user.id,
                "id_persona": persona_id,
                "id_grupo": datos.id_grupo,
                "id_sede": datos.id_sede,
                "email": datos.email,
                "nombre_usuario": datos.email.split("@")[0],
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
        # Evitar dejar una identidad huérfana si falla el alta.
        # En producción, conviene registrar y gestionar también
        # posibles fallos durante la limpieza.
        if persona_id is not None:
            try:
                await (
                    supabase.table("persona")
                    .delete()
                    .eq("id_persona", persona_id)
                    .execute()
                )
            except Exception:
                pass

        if auth_user is not None:
            try:
                await supabase.auth.admin.delete_user(auth_user.id)
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail=f"Error al crear el usuario: {str(e)}",
        )
