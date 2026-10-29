import logging

from supabase import PostgrestAPIError, create_async_client
from supabase_config import get_supabase_config
from fastapi import HTTPException
from model import SocioAltaCreate

logger = logging.getLogger(__name__)


async def get_all_planes(env, access_token: str):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)
        resultado = await (
            supabase.table("plan")
            .select("id_plan,nombre,precio_semanal,clases_semanales")
            .order("nombre")
            .execute()
        )
        return resultado.data
    finally:
        await supabase.postgrest.aclose()

#limpiar esta gilada porque no sirve 
async def crear_usuario_socio(env, datos: SocioAltaCreate):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)
    auth_user = None
    codigo_credencial = None

    try:
        rol_resultado = await (
            supabase.table("rol")
            .select("id_rol,nombre")
            .execute()
        )
        roles_socio = [
            rol
            for rol in rol_resultado.data
            if rol["nombre"].strip().casefold() == "socio"
        ]
        if not roles_socio:
            raise HTTPException(
                status_code=404,
                detail="No se puede crear el socio: no existe un rol llamado 'Socio'.",
            )
        if len(roles_socio) > 1:
            raise HTTPException(
                status_code=409,
                detail="No se puede crear el socio: hay más de un rol llamado 'Socio'.",
            )

        id_rol_socio = roles_socio[0]["id_rol"]

        plan_resultado = await (
            supabase.table("plan")
            .select("id_plan")
            .eq("id_plan", datos.id_plan)
            .limit(1)
            .execute()
        )
        if not plan_resultado.data:
            raise HTTPException(
                status_code=404,
                detail="No existe el plan seleccionado.",
            )

        respuesta_auth = await supabase.auth.admin.create_user({
            "email": datos.usuario.email,
            "password": datos.usuario.password,
            "email_confirm": True,
        })
        auth_user = respuesta_auth.user
        if auth_user is None:
            raise HTTPException(
                status_code=502,
                detail="Supabase no devolvió el usuario creado.",
            )

        perfil_resultado = await (
            supabase.table("usuario")
            .insert({
                "uuid_usuario": auth_user.id,
                "DNI": datos.usuario.DNI,
                "nombre": datos.usuario.nombre,
                "apellido": datos.usuario.apellido,
                "fecha_nacimiento": datos.usuario.fecha_nacimiento.isoformat(),
                "id_rol": id_rol_socio,
            })
            .select("uuid_usuario,DNI,nombre,apellido,fecha_nacimiento,id_rol")
            .execute()
        )
        if not perfil_resultado.data:
            raise RuntimeError("La inserción del perfil no devolvió datos.")

        socio_resultado = await (
            supabase.table("socio")
            .insert({"uuid_usuario": auth_user.id})
            .select("codigo_credencial,uuid_usuario")
            .execute()
        )
        if not socio_resultado.data:
            raise RuntimeError("La inserción del socio no devolvió datos.")
        codigo_credencial = socio_resultado.data[0]["codigo_credencial"]

        membresia_resultado = await (
            supabase.table("membresia")
            .insert({
                "codigo_credencial": codigo_credencial,
                "id_plan": datos.id_plan,
                "fecha_inicio": datos.fecha_inicio.isoformat(),
                "fecha_fin": datos.fecha_fin.isoformat(),
            })
            .select(
                "id_membresia,codigo_credencial,id_plan,fecha_inicio,fecha_fin"
            )
            .execute()
        )
        if not membresia_resultado.data:
            raise RuntimeError("La inserción de la membresía no devolvió datos.")

        return {
            "mensaje": "Socio creado correctamente.",
            "usuario": {
                **perfil_resultado.data[0],
                "email": datos.usuario.email,
            },
            "socio": socio_resultado.data[0],
            "membresia": membresia_resultado.data[0],
        }
    except HTTPException:
        raise
    except Exception as error:
        errores_limpieza = []
        if auth_user is not None:
            acciones_limpieza = []
            if codigo_credencial is not None:
                acciones_limpieza.append(
                    lambda: (
                        supabase.table("membresia")
                        .delete()
                        .eq("codigo_credencial", codigo_credencial)
                        .execute()
                    )
                )
            acciones_limpieza.extend((
                lambda: (
                    supabase.table("socio")
                    .delete()
                    .eq("uuid_usuario", auth_user.id)
                    .execute()
                ),
                lambda: (
                    supabase.table("usuario")
                    .delete()
                    .eq("uuid_usuario", auth_user.id)
                    .execute()
                ),
                lambda: supabase.auth.admin.delete_user(auth_user.id),
            ))
            for limpiar in acciones_limpieza:
                try:
                    await limpiar()
                except Exception as error_limpieza:
                    errores_limpieza.append(type(error_limpieza).__name__)

        if errores_limpieza:
            logger.error(
                "Falló la limpieza al crear usuario/socio: "
                + ", ".join(errores_limpieza)
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    "Falló la creación y no se pudo completar la limpieza. "
                    "Revisá los logs del backend."
                ),
            ) from error

        if (
            isinstance(error, PostgrestAPIError)
            and error.code == "23505"
            and "id_membresia" in (error.details or "")
        ):
            logger.exception("La secuencia de id_membresia está desincronizada")
            raise HTTPException(
                status_code=500,
                detail=(
                    "No se pudo crear la membresía porque la secuencia de "
                    "id_membresia está desincronizada. Sincronizala en Supabase "
                    "y volvé a intentar."
                ),
            ) from error

        logger.exception("Error al crear usuario/socio")
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el usuario y su registro de socio.",
        ) from error
    finally:
        try:
            await supabase.postgrest.aclose()
        finally:
            try:
                await supabase.auth.close()
            finally:
                await supabase.realtime.close()

async def get_all_socios(env, access_token: str):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)
        response = await (
            supabase
            .table("socio")
            .select(
                "codigo_credencial,uuid_usuario,"
                "usuario("
                    "uuid_usuario,DNI,nombre,apellido,fecha_nacimiento"
                "),"
                "membresias:membresia("
                    "id_membresia,id_plan,fecha_inicio,fecha_fin,"
                    "porcentaje_descuento,"
                    "plan("
                        "id_plan,nombre,precio_semanal,clases_semanales"
                    ")"
                ")"
            )
            .execute()
        )

        socios = []
        for socio in response.data:
            usuario = socio.get("usuario")
            if isinstance(usuario, list):
                usuario = usuario[0] if usuario else None

            membresias = socio.get("membresias") or []
            if isinstance(membresias, dict):
                membresias = [membresias]

            for membresia in membresias:
                plan = membresia.get("plan")
                if isinstance(plan, list):
                    membresia["plan"] = plan[0] if plan else None

            socios.append({
                "codigo_credencial": socio["codigo_credencial"],
                "uuid_usuario": socio["uuid_usuario"],
                "usuario": usuario,
                "membresias": membresias,
            })

        return socios
    finally:
        await supabase.postgrest.aclose()


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