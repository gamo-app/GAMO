from datetime import date, timedelta
import logging
import re

from fastapi import HTTPException
from supabase import create_async_client
from supabase_config import get_supabase_config
from model import (
    UsuarioAltaBase as UsuarioBase,
    UsuarioCreateAdmin,
    UsuarioCreateRecepcion,
)

logger = logging.getLogger(__name__)

ROLES_CON_DEPORTE = {"representante"}

PK_POR_ROL = {
    "socio": "codigo_credencial",
    "profesor": "id_profesor",
    "representante": "id_representante",
}


def formatear_telefono(v: str | None) -> str | None:
    """
    Normaliza el número de celular al formato 'XX XXXX-XXXX' (ej: '11 4960-9553').
    """
    if v is None:
        return None
    v_str = str(v).strip()
    if not v_str:
        return None

    digitos = re.sub(r"\D", "", v_str)

    if digitos.startswith("549") and len(digitos) == 13:
        digitos = digitos[3:]
    elif digitos.startswith("54") and len(digitos) == 12:
        digitos = digitos[2:]
    elif digitos.startswith("0") and len(digitos) == 11:
        digitos = digitos[1:]

    if len(digitos) == 8:
        digitos = f"11{digitos}"

    if len(digitos) != 10:
        raise HTTPException(
            status_code=400,
            detail="El teléfono debe contener 10 dígitos (ej: 11 4960-9553).",
        )

    return f"{digitos[:2]} {digitos[2:6]}-{digitos[6:]}"


async def _rollback(
    supabase,
    uuid_usuario: str | None = None,
    codigo_credencial: str | None = None,
    id_membresia: int | None = None,
    id_profesor: int | None = None,
    id_representante: int | None = None,
):
    """Deshace los registros creados en orden inverso si ocurre algún fallo."""
    try:
        if id_membresia is not None:
            await supabase.table("pago").delete().eq("id_membresia", id_membresia).execute()
            await supabase.table("membresia").delete().eq("id_membresia", id_membresia).execute()
        if codigo_credencial is not None:
            await supabase.table("socio").delete().eq("codigo_credencial", codigo_credencial).execute()
        if id_representante is not None:
            await supabase.table("representante").delete().eq("id_representante", id_representante).execute()
        if id_profesor is not None:
            await supabase.table("profesor").delete().eq("id_profesor", id_profesor).execute()
        if uuid_usuario is not None:
            await supabase.table("usuario").delete().eq("uuid_usuario", uuid_usuario).execute()
            await supabase.auth.admin.delete_user(uuid_usuario)
    except Exception:
        logger.exception("Error durante rollback (uuid_usuario=%s)", uuid_usuario)


async def crear_usuario_completo(env, datos: UsuarioBase) -> dict:
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    uuid_usuario = None
    codigo_credencial = None
    id_membresia = None
    id_profesor = None
    id_representante = None

    try:
        rol = datos.rol.strip().lower()
        telefono_formateado = formatear_telefono(datos.telefono)
        id_deporte = getattr(datos, "id_deporte", None) if rol in ROLES_CON_DEPORTE else None

        if rol in ROLES_CON_DEPORTE and id_deporte is None:
            raise HTTPException(
                status_code=400,
                detail="El representante debe tener un deporte asignado (id_deporte mayor a 0).",
            )

        # 1. Buscar id_rol en la tabla rol (con respaldo a 'profesor' si es representante)
        rol_res = await (
            supabase.table("rol")
            .select("id_rol,nombre")
            .ilike("nombre", f"{rol}%")
            .limit(1)
            .execute()
        )
        if not rol_res.data and rol == "representante":
            rol_res = await (
                supabase.table("rol")
                .select("id_rol,nombre")
                .ilike("nombre", "profesor%")
                .limit(1)
                .execute()
            )
        if not rol_res.data:
            raise HTTPException(
                status_code=400,
                detail=f"No existe el rol '{rol}' en la tabla rol.",
            )
        id_rol = rol_res.data[0]["id_rol"]

        # 2. Validar claves foráneas antes de insertar en Auth o en usuario
        if id_deporte is not None:
            dep_res = await (
                supabase.table("deporte")
                .select("id_deporte")
                .eq("id_deporte", id_deporte)
                .eq("activo", True)
                .limit(1)
                .execute()
            )
            if not dep_res.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"El deporte con ID {id_deporte} no existe o está inactivo.",
                )

        if datos.id_sede is not None:
            sede_res = await (
                supabase.table("sede")
                .select("id_sede")
                .eq("id_sede", datos.id_sede)
                .eq("activa", True)
                .limit(1)
                .execute()
            )
            if not sede_res.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"La sede con ID {datos.id_sede} no existe o está inactiva.",
                )

        plan_info = None
        if rol == "socio" and datos.id_plan is not None:
            plan_res = await (
                supabase.table("plan")
                .select("*")
                .eq("id_plan", datos.id_plan)
                .limit(1)
                .execute()
            )
            if not plan_res.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"El plan con ID {datos.id_plan} no existe.",
                )
            plan_info = plan_res.data[0]

        # 3. Verificar duplicado de DNI en public.usuario
        dni_res = await (
            supabase.table("usuario")
            .select("uuid_usuario")
            .eq("DNI", datos.dni)
            .limit(1)
            .execute()
        )
        if dni_res.data:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario registrado con ese DNI.",
            )

        # 4. Crear identidad en Supabase Auth
        auth_res = await supabase.auth.admin.create_user({
            "email": datos.email,
            "password": datos.password,
            "email_confirm": True,
            "user_metadata": {
                "nombre": datos.nombre,
                "apellido": datos.apellido,
                "dni": datos.dni,
                "telefono": telefono_formateado,
                "rol": rol,
            },
        })
        if auth_res.user is None:
            raise HTTPException(
                status_code=500,
                detail="No se pudo crear la identidad del usuario en Supabase Auth.",
            )
        uuid_usuario = auth_res.user.id

        # 5. Insertar en public.usuario
        await (
            supabase.table("usuario")
            .insert({
                "uuid_usuario": uuid_usuario,
                "DNI": datos.dni,
                "nombre": datos.nombre,
                "apellido": datos.apellido,
                "fecha_nacimiento": datos.fecha_nacimiento.isoformat(),
                "id_rol": id_rol,
            })
            .execute()
        )

        # 6. Insertar en la tabla específica del rol
        hoy = date.today()
        datos_rol = {}

        if rol == "socio":
            socio_res = await (
                supabase.table("socio")
                .insert({"uuid_usuario": uuid_usuario})
                .execute()
            )
            datos_rol = socio_res.data[0] if socio_res.data else {}
            codigo_credencial = datos_rol.get("codigo_credencial")

            # 7. Si se indicó un plan válido, crear membresía y pago inicial
            if plan_info is not None and codigo_credencial is not None:
                vencimiento = hoy + timedelta(days=30)

                memb_res = await (
                    supabase.table("membresia")
                    .insert({
                        "codigo_credencial": codigo_credencial,
                        "id_plan": datos.id_plan,
                        "fecha_inicio": hoy.isoformat(),
                        "fecha_fin": vencimiento.isoformat(),
                        "porcentaje_descuento": 0,
                    })
                    .execute()
                )
                if memb_res.data:
                    id_membresia = memb_res.data[0].get("id_membresia")
                    monto = float(plan_info.get("precio_semanal") or 0)
                    if id_membresia is not None and monto > 0:
                        await (
                            supabase.table("pago")
                            .insert({
                                "id_membresia": id_membresia,
                                "monto": monto,
                            })
                            .execute()
                        )

        elif rol == "profesor":
            prof_res = await (
                supabase.table("profesor")
                .insert({"uuid_usuario": uuid_usuario})
                .execute()
            )
            datos_rol = prof_res.data[0] if prof_res.data else {}
            id_profesor = datos_rol.get("id_profesor")

        elif rol == "representante":
            prof_res = await (
                supabase.table("profesor")
                .insert({"uuid_usuario": uuid_usuario})
                .execute()
            )
            prof_data = prof_res.data[0] if prof_res.data else {}
            id_profesor = prof_data.get("id_profesor")

            if id_profesor is None:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo generar el perfil de profesor para el representante.",
                )

            rep_res = await (
                supabase.table("representante")
                .insert({
                    "id_profesor": id_profesor,
                    "id_deporte": id_deporte,
                })
                .execute()
            )
            datos_rol = rep_res.data[0] if rep_res.data else {}
            id_representante = datos_rol.get("id_representante")

        respuesta = {
            "mensaje": f"{rol.capitalize()} registrado exitosamente en el sistema.",
            "uuid_usuario": uuid_usuario,
            "id_usuario": uuid_usuario,
            "telefono": telefono_formateado,
            "rol": rol,
            PK_POR_ROL[rol]: datos_rol.get(PK_POR_ROL[rol]),
        }

        if rol == "representante" and id_profesor is not None:
            respuesta["id_profesor"] = id_profesor

        return respuesta

    except HTTPException:
        await _rollback(
            supabase,
            uuid_usuario,
            codigo_credencial,
            id_membresia,
            id_profesor,
            id_representante,
        )
        raise
    except Exception as e:
        await _rollback(
            supabase,
            uuid_usuario,
            codigo_credencial,
            id_membresia,
            id_profesor,
            id_representante,
        )
        logger.exception("Error al registrar el usuario")
        texto = str(e).lower()
        if "duplicate key" in texto or "23505" in texto or "already" in texto:
            raise HTTPException(
                status_code=409,
                detail="El DNI o el email ya están registrados.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar el usuario en la base de datos: {str(e)}",
        )
    finally:
        await supabase.postgrest.aclose()