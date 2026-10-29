from datetime import date, datetime, time, timedelta, timezone
from fastapi import HTTPException
from supabase import PostgrestAPIError, create_async_client
from supabase_config import get_supabase_config
from model import AsistenciaQrEscaneo, AsistenciaRegistro

# Buenos Aires currently uses UTC-03:00 year-round; this avoids runtime tzdata.
ZONA_HORARIA_ARGENTINA = timezone(
    timedelta(hours=-3),
    name="America/Argentina/Buenos_Aires",
)

DIAS_SEMANA = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


async def get_all_asistencias(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)

        # Usar el token del usuario para respetar las políticas RLS
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("asistencia")
            .select("*")
            .execute()
        )
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener las clases: {str(e)}"
            )
    return response.data


async def get_mis_asistencias(
    env,
    uuid_usuario: str,
    access_token: str,
):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)

        socio_resultado = await (
            supabase.table("socio")
            .select("codigo_credencial")
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )

        if not socio_resultado.data:
            return []

        codigo_credencial = socio_resultado.data[0]["codigo_credencial"]
        resultado = await (
            supabase.table("asistencia")
            .select("*")
            .eq("codigo_credencial", codigo_credencial)
            .order("fecha", desc=True)
            .execute()
        )
        return resultado.data
    finally:
        await supabase.postgrest.aclose()


async def registrar_asistencia(
    env,
    datos: AsistenciaRegistro,
    uuid_usuario: str,
    nombre_rol: str | None,
    access_token: str,
):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)

        socio_resultado = await (
            supabase.table("socio")
            .select("codigo_credencial")
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )
        codigo_propio = (
            socio_resultado.data[0]["codigo_credencial"]
            if socio_resultado.data
            else None
        )

        codigo_solicitado = datos.codigo_credencial
        registrar_para_otro = (
            codigo_solicitado is not None
            and str(codigo_solicitado) != str(codigo_propio)
        )

        if registrar_para_otro and (
            nombre_rol is None
            or nombre_rol.strip().casefold()
            not in {"admin", "representante", "profesor"}
        ):
            raise HTTPException(
                status_code=403,
                detail="No tenés permiso para registrar la asistencia de otra persona.",
            )

        codigo_credencial = codigo_solicitado or codigo_propio
        if codigo_credencial is None:
            raise HTTPException(
                status_code=404,
                detail="La cuenta autenticada no tiene un socio asociado.",
            )

        socio_destino = await (
            supabase.table("socio")
            .select("codigo_credencial")
            .eq("codigo_credencial", str(codigo_credencial))
            .limit(1)
            .execute()
        )
        if not socio_destino.data:
            raise HTTPException(
                status_code=404,
                detail="No existe un socio con esa credencial.",
            )

        clase_resultado = await (
            supabase.table("clase")
            .select("uuid_clase")
            .eq("uuid_clase", str(datos.uuid_clase))
            .limit(1)
            .execute()
        )
        if not clase_resultado.data:
            raise HTTPException(
                status_code=404,
                detail="No existe la clase indicada.",
            )

        try:
            resultado = await (
                supabase.table("asistencia")
                .insert({
                    "uuid_clase": str(datos.uuid_clase),
                    "codigo_credencial": str(codigo_credencial),
                    "fecha": datos.fecha.isoformat(),
                })
                .select("*")
                .execute()
            )
        except PostgrestAPIError as error:
            if error.code == "42501":
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "La política RLS de Supabase no permite registrar "
                        "esta asistencia."
                    ),
                ) from error
            raise

        if not resultado.data:
            raise HTTPException(
                status_code=500,
                detail="No se pudo registrar la asistencia.",
            )

        return resultado.data[0]
    finally:
        await supabase.postgrest.aclose()


async def generar_qr_sede(
    env,
    id_sede: int,
    access_token: str,
):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)
        resultado = await (
            supabase.table("sede")
            .select("id_sede")
            .eq("id_sede", id_sede)
            .limit(1)
            .execute()
        )
        if not resultado.data:
            raise HTTPException(
                status_code=404,
                detail="No existe la sede indicada.",
            )

        return {
            "tipo": "asistencia_sede",
            "id_sede": id_sede,
            "qr_payload": f"GAMO:ASISTENCIA:SEDE:{id_sede}",
        }
    finally:
        await supabase.postgrest.aclose()


def _hora_local(valor: str | time) -> time:
    try:
        hora = valor if isinstance(valor, time) else time.fromisoformat(valor)
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="La sede tiene un horario de clase inválido.",
        ) from error

    return hora.replace(tzinfo=None)


def _id_sede_desde_qr(datos: AsistenciaQrEscaneo) -> int:
    partes = datos.qr_payload.split(":")
    if len(partes) != 4 or partes[:3] != ["GAMO", "ASISTENCIA", "SEDE"]:
        raise HTTPException(
            status_code=400,
            detail="El QR no corresponde a una sede de asistencia de GAMO.",
        )

    try:
        id_sede = int(partes[3])
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="El QR contiene un identificador de sede inválido.",
        ) from error

    if id_sede <= 0:
        raise HTTPException(
            status_code=400,
            detail="El QR contiene un identificador de sede inválido.",
        )

    return id_sede


async def registrar_asistencia_qr(
    env,
    datos: AsistenciaQrEscaneo,
    uuid_usuario: str,
    access_token: str,
):
    id_sede = _id_sede_desde_qr(datos)
    ahora = datetime.now(ZONA_HORARIA_ARGENTINA)
    dia_actual = DIAS_SEMANA[ahora.weekday()]
    hora_actual = ahora.time().replace(tzinfo=None)
    fecha_actual = ahora.date()

    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        supabase.postgrest.auth(access_token)

        sede_resultado = await (
            supabase.table("sede")
            .select("id_sede")
            .eq("id_sede", id_sede)
            .limit(1)
            .execute()
        )
        if not sede_resultado.data:
            raise HTTPException(
                status_code=404,
                detail="No existe la sede indicada en el QR.",
            )

        socio_resultado = await (
            supabase.table("socio")
            .select("codigo_credencial")
            .eq("uuid_usuario", uuid_usuario)
            .limit(1)
            .execute()
        )
        if not socio_resultado.data:
            raise HTTPException(
                status_code=403,
                detail="La cuenta autenticada no está asociada a un socio.",
            )
        codigo_credencial = socio_resultado.data[0]["codigo_credencial"]

        clases = await (
            supabase.table("clase")
            .select("uuid_clase,dia_de_semana,hora_inicio,hora_fin")
            .eq("id_sede", id_sede)
            .eq("dia_de_semana", dia_actual)
            .execute()
        )

        clases_activas = [
            clase
            for clase in clases.data
            if _hora_local(clase["hora_inicio"])
            <= hora_actual
            < _hora_local(clase["hora_fin"])
        ]

        if not clases_activas:
            raise HTTPException(
                status_code=404,
                detail="No hay una clase activa en esta sede en este momento.",
            )
        if len(clases_activas) > 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Hay más de una clase activa en esta sede. "
                    "Revisá los horarios configurados."
                ),
            )

        uuid_clase = clases_activas[0]["uuid_clase"]
        asistencia_existente = await (
            supabase.table("asistencia")
            .select("id_asistencia")
            .eq("uuid_clase", uuid_clase)
            .eq("codigo_credencial", codigo_credencial)
            .eq("fecha", fecha_actual.isoformat())
            .limit(1)
            .execute()
        )
        if asistencia_existente.data:
            raise HTTPException(
                status_code=409,
                detail="La asistencia a esta clase ya fue registrada hoy.",
            )

        try:
            resultado = await (
                supabase.table("asistencia")
                .insert({
                    "uuid_clase": uuid_clase,
                    "codigo_credencial": codigo_credencial,
                    "fecha": fecha_actual.isoformat(),
                })
                .select("*")
                .execute()
            )
        except PostgrestAPIError as error:
            if error.code == "42501":
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "La política RLS de Supabase no permite registrar "
                        "esta asistencia."
                    ),
                ) from error
            if error.code == "23505":
                raise HTTPException(
                    status_code=409,
                    detail="La asistencia a esta clase ya fue registrada hoy.",
                ) from error
            raise

        if not resultado.data:
            raise HTTPException(
                status_code=500,
                detail="No se pudo registrar la asistencia.",
            )

        return {
            "mensaje": "Asistencia registrada correctamente.",
            "asistencia": resultado.data[0],
            "zona_horaria": "America/Argentina/Buenos_Aires",
        }
    finally:
        await supabase.postgrest.aclose()
