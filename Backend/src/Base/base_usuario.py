from fastapi import HTTPException
from supabase import create_async_client
from supabase_config import get_supabase_config
from model import SocioAltaCreate, UsuarioCreate


async def get_sesion(env, uuid_usuario: str, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select(
                "uuid_usuario,DNI,nombre,apellido,fecha_nacimiento,"
                "rol:id_rol(id_rol,nombre,permisos)"
            )
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el usuario.",
            )

        usuario_data = response.data[0]
        rol = usuario_data.get("rol")
        if isinstance(rol, list):
            usuario_data["rol"] = rol[0] if rol else None

        return usuario_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener la sesión del usuario: {str(e)}",
        )


async def get_user_rol(env, uuid_usuario: str, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select("rol:id_rol(id_rol,nombre,permisos)")
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el usuario.",
            )

        rol = response.data[0].get("rol")
        if isinstance(rol, list):
            rol = rol[0] if rol else None

        if not rol:
            raise HTTPException(
                status_code=404,
                detail="El usuario no tiene un rol asignado.",
            )

        return rol["nombre"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el rol del usuario: {str(e)}",
        )


# Alias por compatibilidad con llamadas anteriores
get_user_group = get_user_rol


async def get_all_usuarios(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)

        # Usar el token del usuario para respetar las políticas RLS
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("usuario")
            .select("*, rol:id_rol(id_rol,nombre)")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los usuarios: {str(e)}",
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


async def create_socio_alta(env, datos: SocioAltaCreate):
    """Crea la identidad en Auth, el registro en usuario, socio y su primera membresía."""
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    auth_user = None
    uuid_usuario = None
    codigo_credencial = None

    try:
        # 1. Obtener id_rol correspondiente a 'socio'
        rol_res = await (
            supabase.table("rol")
            .select("id_rol")
            .ilike("nombre", "socio%")
            .limit(1)
            .execute()
        )
        if not rol_res.data:
            raise HTTPException(
                status_code=400,
                detail="No existe el rol 'socio' en la tabla rol.",
            )
        id_rol_socio = rol_res.data[0]["id_rol"]

        # 2. Crear usuario en Supabase Auth
        respuesta_auth = await supabase.auth.admin.create_user({
            "email": datos.usuario.email,
            "password": datos.usuario.password,
            "email_confirm": True,
        })
        auth_user = respuesta_auth.user
        if auth_user is None:
            raise HTTPException(
                status_code=500,
                detail="No se pudo crear la identidad del socio en Auth.",
            )
        uuid_usuario = auth_user.id

        # 3. Insertar en public.usuario
        perfil_res = await (
            supabase.table("usuario")
            .insert({
                "uuid_usuario": uuid_usuario,
                "DNI": datos.usuario.DNI,
                "nombre": datos.usuario.nombre,
                "apellido": datos.usuario.apellido,
                "fecha_nacimiento": datos.usuario.fecha_nacimiento.isoformat(),
                "id_rol": id_rol_socio,
            })
            .execute()
        )

        # 4. Insertar en public.socio
        socio_res = await (
            supabase.table("socio")
            .insert({"uuid_usuario": uuid_usuario})
            .execute()
        )
        socio_data = socio_res.data[0]
        codigo_credencial = socio_data["codigo_credencial"]

        # 5. Insertar primera membresía en public.membresia
        membresia_res = await (
            supabase.table("membresia")
            .insert({
                "codigo_credencial": codigo_credencial,
                "id_plan": datos.id_plan,
                "fecha_inicio": datos.fecha_inicio.isoformat(),
                "fecha_fin": datos.fecha_fin.isoformat(),
                "porcentaje_descuento": 0,
            })
            .execute()
        )

        return {
            "mensaje": "Socio y membresía registrados correctamente.",
            "usuario": perfil_res.data[0],
            "socio": socio_data,
            "membresia": membresia_res.data[0],
        }

    except HTTPException:
        raise
    except Exception as e:
        if codigo_credencial is not None:
            try:
                await supabase.table("membresia").delete().eq("codigo_credencial", codigo_credencial).execute()
                await supabase.table("socio").delete().eq("codigo_credencial", codigo_credencial).execute()
            except Exception:
                pass
        if uuid_usuario is not None:
            try:
                await supabase.table("usuario").delete().eq("uuid_usuario", uuid_usuario).execute()
            except Exception:
                pass
        if auth_user is not None:
            try:
                await supabase.auth.admin.delete_user(auth_user.id)
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail=f"Error al dar de alta el socio: {str(e)}",
        )