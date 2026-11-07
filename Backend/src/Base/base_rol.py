from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
import math
import re
import unicodedata
from typing import Any
from urllib.parse import quote

from fastapi import HTTPException
from supabase import create_async_client
from supabase_config import get_supabase_config
from workers import fetch

from model import (
    EstadoDePagoSocioEnum,
    ListadoUsuariosResponse,
    PaginacionUsuariosInfo,
    UsuarioFiltradoResponse,
)

logger = logging.getLogger(__name__)

DIAS_PARA_CONSIDERAR_MOROSO = 7
LOTE_EXPORTACION = 1000
MAX_FILAS_EXPORTACION = 20000  # tope de seguridad del bucle de lotes de la exportación

# El servidor corre en UTC; Argentina no tiene horario de verano (UTC-3 fijo).
ZONA_AR = timezone(timedelta(hours=-3))

ROLES_VALIDOS = {"socio", "profesor", "representante", "administrador"}
ESTADOS_VALIDOS = {"activo", "inactivo", "moroso", "al_dia", "pendiente"}

MAPA_ROLES = {
    "socio": "socio",
    "socios": "socio",
    "profesor": "profesor",
    "profesores": "profesor",
    "representante": "representante",
    "representantes": "representante",
    "administrador": "administrador",
    "administradores": "administrador",
    "admin": "administrador",
}

MAPA_ESTADOS = {
    "activo": "activo",
    "activos": "activo",
    "inactivo": "inactivo",
    "inactivos": "inactivo",
    "moroso": "moroso",
    "morosos": "moroso",
    "al dia": "al_dia",
    "al_dia": "al_dia",
    "pendiente": "pendiente",
    "pendientes": "pendiente",
}


async def get_all_rol(env, access_token: str):
    url, key = get_supabase_config(env)
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        response = (
            await supabase
            .table("rol")
            .select("*")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los roles: {str(e)}"
        )
    return response.data


async def _error_upstream(response, mensaje: str) -> HTTPException:
    try:
        detalle = await response.text()
    except Exception:
        detalle = "<sin detalle>"
    logger.error("%s (status %s): %s", mensaje, response.status, detalle)
    return HTTPException(
        status_code=502,
        detail=f"{mensaje} (Supabase {response.status}): {detalle}",
    )


def _primero(valor: Any) -> dict[str, Any]:
    if isinstance(valor, list):
        return valor[0] if valor else {}
    return valor or {}


def _lista(valor: Any) -> list[dict[str, Any]]:
    if not valor:
        return []
    return valor if isinstance(valor, list) else [valor]


def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _normalizar(valor: str | None, mapa: dict[str, str]) -> str | None:
    limpio = _sin_acentos((valor or "").strip().lower())
    return None if limpio in ("", "todos", "todas") else mapa.get(limpio, limpio)


def _clave_rol(nombre: str | None) -> str:
    limpio = _sin_acentos((nombre or "").strip().lower())
    return MAPA_ROLES.get(limpio, limpio)


def _validar_filtros(
    rol: str | None, estado: str | None
) -> tuple[str | None, str | None]:
    rol_norm = _normalizar(rol, MAPA_ROLES)
    estado_norm = _normalizar(estado, MAPA_ESTADOS)
    if rol_norm is not None and rol_norm not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail="Rol inválido. Valores permitidos: Todos, Socios, Profesores, Representantes, Administradores.",
        )
    if estado_norm is not None and estado_norm not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail="Estado inválido. Valores permitidos: Todos, Activos, Inactivos, Morosos, Pendientes, Al dia.",
        )
    return rol_norm, estado_norm


def _terminos_de_busqueda(buscar: str | None) -> list[str]:
    if not buscar or not buscar.strip():
        return []
    limpio = re.sub(r'[,()%*_"\\]', " ", buscar.strip())
    return [t for t in limpio.split() if t][:5]


def _condiciones_para(palabra: str) -> list[str]:
    condiciones = [
        f"nombre.ilike.*{palabra}*",
        f"apellido.ilike.*{palabra}*",
    ]
    solo_digitos = palabra.replace(".", "").replace("-", "")
    if solo_digitos.isascii() and solo_digitos.isdigit() and len(solo_digitos) <= 12:
        condiciones.append(f"DNI.eq.{solo_digitos}")
    return condiciones


def _extraer_total(content_range: str | None) -> int:
    if not content_range or "/" not in content_range:
        return 0
    total_str = content_range.split("/")[-1]
    return int(total_str) if total_str.isdigit() else 0


def _ultima_membresia(membresias: Any) -> dict[str, Any]:
    lista = _lista(membresias)
    if not lista:
        return {}
    return max(lista, key=lambda m: m.get("fecha_fin") or "")


def _ultimo_pago(pagos: Any) -> dict[str, Any]:
    lista = _lista(pagos)
    if not lista:
        return {}
    return max(lista, key=lambda p: p.get("id_pago") or 0)


def _ultima_asistencia(asistencias: Any) -> dict[str, Any]:
    lista = _lista(asistencias)
    if not lista:
        return {}
    return max(lista, key=lambda a: a.get("fecha") or "")


def _formatear_horario_clase(clase_data: dict[str, Any]) -> str | None:
    if not clase_data:
        return None
    dia = clase_data.get("dia_de_semana")
    h_ini = str(clase_data.get("hora_inicio") or "")[:5]
    h_fin = str(clase_data.get("hora_fin") or "")[:5]
    deporte_cls = _primero(clase_data.get("deporte")).get("nombre")

    horario = f"{dia} {h_ini} a {h_fin}".strip() if dia else None
    if deporte_cls and horario:
        return f"{deporte_cls} - {horario}"
    return horario or deporte_cls


def _hoy_ar() -> date:
    return datetime.now(ZONA_AR).date()


def _calcular_estado_membresia(
    membresia_data: dict[str, Any], es_socio: bool
) -> tuple[str, str | None, bool]:
    if not es_socio:
        return "activo", None, False

    fecha_fin_str = membresia_data.get("fecha_fin")
    if not fecha_fin_str:
        return "inactivo", None, False

    try:
        fecha_fin = date.fromisoformat(str(fecha_fin_str))
    except ValueError:
        return "activo", None, False

    dias_vencido = (_hoy_ar() - fecha_fin).days
    if dias_vencido <= 0:
        return "activo", EstadoDePagoSocioEnum.al_dia.value, False
    if dias_vencido > DIAS_PARA_CONSIDERAR_MOROSO:
        return "activo", EstadoDePagoSocioEnum.moroso.value, True
    return "activo", EstadoDePagoSocioEnum.pendiente.value, False


def _cumple_filtro_estado(
    usuario: UsuarioFiltradoResponse, estado_norm: str | None
) -> bool:
    if not estado_norm:
        return True
    if estado_norm in ("activo", "inactivo"):
        return usuario.estado == estado_norm
    if estado_norm == "al_dia":
        return usuario.estado_cuota == EstadoDePagoSocioEnum.al_dia.value
    if estado_norm == "moroso":
        return usuario.estado_cuota == EstadoDePagoSocioEnum.moroso.value
    if estado_norm == "pendiente":
        return usuario.estado_cuota == EstadoDePagoSocioEnum.pendiente.value
    return True


def _armar_usuario_filtrado(fila: dict[str, Any]) -> UsuarioFiltradoResponse:
    rol_data = _primero(fila.get("rol"))
    socio_data = _primero(fila.get("socio"))
    profesor_data = _primero(fila.get("profesor"))
    representante_data = _primero(profesor_data.get("representante"))
    deporte_rep = _primero(representante_data.get("deporte"))

    clase_prof = _primero(profesor_data.get("clase"))
    asistencia_actual = _ultima_asistencia(socio_data.get("asistencia"))
    clase_socio = _primero(asistencia_actual.get("clase"))
    clase_activa = clase_socio or clase_prof

    sede_data = _primero(clase_activa.get("sede")) or _primero(clase_prof.get("sede"))
    deporte_clase = _primero(clase_activa.get("deporte"))

    membresia_actual = _ultima_membresia(socio_data.get("membresia"))
    plan_data = _primero(membresia_actual.get("plan"))
    pago_actual = _ultimo_pago(membresia_actual.get("pago"))

    es_socio = bool(socio_data) or _clave_rol(rol_data.get("nombre")) == "socio"
    estado_usr, estado_cuota, es_moroso = _calcular_estado_membresia(
        membresia_actual, es_socio
    )

    descuento = Decimal(str(membresia_actual.get("porcentaje_descuento") or 0))
    monto = pago_actual.get("monto")
    if monto is None and plan_data.get("precio_semanal") is not None:
        precio_base = Decimal(str(plan_data["precio_semanal"]))
        factor = (Decimal("100") - descuento) / Decimal("100")
        monto = (precio_base * factor).quantize(Decimal("0.01"))
    elif monto is not None:
        monto = Decimal(str(monto))

    uuid_val = fila.get("uuid_usuario")
    dni_val = int(fila.get("DNI") or 0)

    return UsuarioFiltradoResponse(
        uuid_usuario=uuid_val,
        id_usuario=str(uuid_val) if uuid_val else None,
        DNI=dni_val,
        dni=str(dni_val) if dni_val else None,
        nombre=fila.get("nombre") or "",
        apellido=fila.get("apellido") or "",
        fecha_nacimiento=fila.get("fecha_nacimiento"),
        id_rol=fila.get("id_rol"),
        rol=rol_data.get("nombre") or "",
        estado=estado_usr,
        codigo_credencial=socio_data.get("codigo_credencial"),
        id_plan=plan_data.get("id_plan"),
        plan=plan_data.get("nombre"),
        fecha_inicio_membresia=membresia_actual.get("fecha_inicio"),
        fecha_vencimiento_cuota=membresia_actual.get("fecha_fin"),
        porcentaje_descuento=membresia_actual.get("porcentaje_descuento"),
        estado_cuota=estado_cuota,
        monto_cuota=monto,
        es_moroso=es_moroso,
        id_profesor=profesor_data.get("id_profesor"),
        id_representante=representante_data.get("id_representante"),
        id_deporte=deporte_rep.get("id_deporte") or deporte_clase.get("id_deporte"),
        deporte=deporte_rep.get("nombre") or deporte_clase.get("nombre"),
        id_sede=sede_data.get("id_sede"),
        sede=sede_data.get("nombre"),
        uuid_clase=clase_activa.get("uuid_clase"),
        clase=_formatear_horario_clase(clase_activa),
    )


def _construir_query_usuarios(
    rol_norm: str | None,
    estado_norm: str | None,
    id_sede: int | None,
    buscar: str | None,
    id_plan: int | None,
    id_deporte: int | None,
    uuid_clase: Any = None,
) -> list[str]:
    """Construye los parámetros PostgREST sin recortar el historial de membresías."""
    es_sede_socio = bool(id_sede and rol_norm == "socio")
    es_sede_prof = bool(id_sede and rol_norm in ("profesor", "representante"))

    exige_membresia = bool(
        (estado_norm in ("moroso", "al_dia", "pendiente"))
        or (estado_norm == "activo" and rol_norm == "socio")
        or id_plan
    )
    tiene_filtro_socio = bool(
        exige_membresia
        or estado_norm == "inactivo"
        or uuid_clase
        or es_sede_socio
    )
    j_socio = "socio!inner" if tiene_filtro_socio else "socio"
    j_memb = "membresia!inner" if exige_membresia else "membresia"
    j_asist = "asistencia!inner" if (uuid_clase or es_sede_socio) else "asistencia"
    j_clase_socio = "clase!inner" if es_sede_socio else "clase"

    j_prof = (
        "profesor!inner"
        if (id_deporte or es_sede_prof or rol_norm == "representante")
        else "profesor"
    )
    j_rep = (
        "representante!inner"
        if (id_deporte or rol_norm == "representante")
        else "representante"
    )
    j_clase_prof = "clase!inner" if es_sede_prof else "clase"

    select_usuarios = (
        "uuid_usuario,DNI,nombre,apellido,fecha_nacimiento,id_rol,"
        "rol!inner(id_rol,nombre),"
        f"{j_socio}(codigo_credencial,"
        f"{j_memb}(id_membresia,id_plan,fecha_inicio,fecha_fin,porcentaje_descuento,"
        "plan(id_plan,nombre,precio_semanal,clases_semanales),"
        "pago(id_pago,monto)),"
        f"{j_asist}(id_asistencia,uuid_clase,fecha,"
        f"{j_clase_socio}(uuid_clase,dia_de_semana,hora_inicio,hora_fin,id_sede,id_deporte,"
        "deporte(id_deporte,nombre),sede(id_sede,nombre)))),"
        f"{j_prof}(id_profesor,"
        f"{j_rep}(id_representante,id_deporte,deporte(id_deporte,nombre)),"
        f"{j_clase_prof}(uuid_clase,dia_de_semana,hora_inicio,hora_fin,id_sede,sede(id_sede,nombre)))"
    )

    query_parts = [
        f"select={quote(select_usuarios, safe='(),!*')}",
        "order=apellido.asc,uuid_usuario.asc",
    ]

    if rol_norm and rol_norm != "representante":
        query_parts.append(f"rol.nombre=ilike.{quote(rol_norm, safe='')}%25")
    elif estado_norm in ("moroso", "pendiente", "al_dia", "inactivo") and not rol_norm:
        query_parts.append("rol.nombre=ilike.socio%25")

    if id_plan:
        query_parts.append(f"socio.membresia.id_plan=eq.{id_plan}")
    if uuid_clase:
        query_parts.append(f"socio.asistencia.uuid_clase=eq.{quote(str(uuid_clase), safe='')}")
    if id_deporte:
        query_parts.append(f"profesor.representante.id_deporte=eq.{id_deporte}")
    if es_sede_socio:
        query_parts.append(f"socio.asistencia.clase.id_sede=eq.{id_sede}")
    elif es_sede_prof:
        query_parts.append(f"profesor.clase.id_sede=eq.{id_sede}")

    terminos = _terminos_de_busqueda(buscar)
    if len(terminos) == 1:
        or_cond = ",".join(_condiciones_para(terminos[0]))
        query_parts.append(f"or=({quote(or_cond, safe=',.*')})")
    elif len(terminos) > 1:
        grupos_or = [f"or({','.join(_condiciones_para(p))})" for p in terminos]
        and_cond = ",".join(grupos_or)
        query_parts.append(f"and=({quote(and_cond, safe=',().*')})")

    return query_parts


async def filtrar_usuarios_por_rol(
    env,
    access_token: str | None = None,
    page: int = 1,
    limit: int = 10,
    rol: str | None = None,
    estado: str | None = None,
    id_sede: int | None = None,
    buscar: str | None = None,
    id_plan: int | None = None,
    id_deporte: int | None = None,
    uuid_clase: Any = None,
) -> ListadoUsuariosResponse:
    url, key = get_supabase_config(env)

    if page < 1:
        raise HTTPException(status_code=400, detail="La página debe ser mayor o igual a 1")
    if limit < 1:
        raise HTTPException(status_code=400, detail="El límite debe ser mayor o igual a 1")

    rol_norm, estado_norm = _validar_filtros(rol, estado)

    id_sede = id_sede if id_sede and id_sede > 0 else None
    id_plan = id_plan if id_plan and id_plan > 0 else None
    id_deporte = id_deporte if id_deporte and id_deporte > 0 else None

    if estado_norm in ("moroso", "pendiente", "al_dia", "inactivo") and rol_norm in (
        "profesor",
        "representante",
        "administrador",
    ):
        return ListadoUsuariosResponse(
            datos=[],
            paginacion=PaginacionUsuariosInfo(
                paginaActual=page,
                elementosPorPagina=limit,
                totalPaginas=0,
                totalRegistros=0,
            ),
        )

    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    # Si hay filtro de estado calculado o filtro de sede sin rol fijo,
    # paginamos sobre el conjunto filtrado para que el total coincida 100% con la exportación.
    if estado_norm is not None or (id_sede and not rol_norm):
        usuarios_filtrados = await obtener_usuarios_para_exportar(
            env=env,
            access_token=access_token,
            rol=rol_norm,
            estado=estado_norm,
            id_sede=id_sede,
            buscar=buscar,
            id_plan=id_plan,
            id_deporte=id_deporte,
            uuid_clase=uuid_clase,
        )
        total_registros = len(usuarios_filtrados)
        datos = usuarios_filtrados[inicio : inicio + limit]
        total_paginas = math.ceil(total_registros / limit) if total_registros else 0
        return ListadoUsuariosResponse(
            datos=datos,
            paginacion=PaginacionUsuariosInfo(
                paginaActual=page,
                elementosPorPagina=limit,
                totalPaginas=total_paginas,
                totalRegistros=total_registros,
            ),
        )

    query_parts = _construir_query_usuarios(
        rol_norm=rol_norm,
        estado_norm=estado_norm,
        id_sede=id_sede,
        buscar=buscar,
        id_plan=id_plan,
        id_deporte=id_deporte,
        uuid_clase=uuid_clase,
    )

    full_url = f"{url}/rest/v1/usuario?{'&'.join(query_parts)}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {access_token or key}",
        "Prefer": "count=exact",
        "Range-Unit": "items",
        "Range": f"{inicio}-{fin}",
    }

    response = await fetch(full_url, headers=headers)

    if response.status == 416:
        headers["Range"] = "0-0"
        response_count = await fetch(full_url, headers=headers)
        if not response_count.ok:
            raise await _error_upstream(response_count, "Error al consultar los usuarios")
        total_registros = _extraer_total(response_count.headers.get("content-range"))
        filas = []
    elif response.status in (401, 403):
        raise HTTPException(
            status_code=response.status,
            detail="No tenés permisos o tu sesión expiró.",
        )
    elif not response.ok:
        raise await _error_upstream(response, "Error al consultar los usuarios")
    else:
        filas = await response.json()
        total_registros = _extraer_total(response.headers.get("content-range"))

    datos = [_armar_usuario_filtrado(f) for f in filas]
    total_paginas = math.ceil(total_registros / limit) if total_registros else 0

    return ListadoUsuariosResponse(
        datos=datos,
        paginacion=PaginacionUsuariosInfo(
            paginaActual=page,
            elementosPorPagina=limit,
            totalPaginas=total_paginas,
            totalRegistros=total_registros,
        ),
    )


async def obtener_usuarios_para_exportar(
    env,
    access_token: str | None = None,
    rol: str | None = "socio",
    estado: str | None = None,
    id_sede: int | None = None,
    buscar: str | None = None,
    id_plan: int | None = None,
    id_deporte: int | None = None,
    uuid_clase: Any = None,
) -> list[UsuarioFiltradoResponse]:
    """Obtiene todos los socios/usuarios filtrados por lotes para exportar a XLSX o PDF."""
    url, key = get_supabase_config(env)

    rol_norm, estado_norm = _validar_filtros(rol, estado)

    id_sede = id_sede if id_sede and id_sede > 0 else None
    id_plan = id_plan if id_plan and id_plan > 0 else None
    id_deporte = id_deporte if id_deporte and id_deporte > 0 else None

    if estado_norm in ("moroso", "pendiente", "al_dia", "inactivo") and rol_norm in (
        "profesor",
        "representante",
        "administrador",
    ):
        return []

    query_parts = _construir_query_usuarios(
        rol_norm=rol_norm,
        estado_norm=estado_norm,
        id_sede=id_sede,
        buscar=buscar,
        id_plan=id_plan,
        id_deporte=id_deporte,
        uuid_clase=uuid_clase,
    )

    full_url = f"{url}/rest/v1/usuario?{'&'.join(query_parts)}"
    filas_totales: list[dict[str, Any]] = []
    offset = 0

    while True:
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {access_token or key}",
            "Range-Unit": "items",
            "Range": f"{offset}-{offset + LOTE_EXPORTACION - 1}",
        }
        response = await fetch(full_url, headers=headers)

        if response.status == 416:
            break
        if response.status in (401, 403):
            raise HTTPException(
                status_code=response.status,
                detail="No tenés permisos o tu sesión expiró.",
            )
        if not response.ok:
            raise await _error_upstream(response, "Error al consultar los usuarios para exportar")

        lote = await response.json()
        if not lote:
            break

        filas_totales.extend(lote)
        if len(filas_totales) > MAX_FILAS_EXPORTACION:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"La exportación supera las {MAX_FILAS_EXPORTACION} filas. "
                    "Aplicá más filtros (por ejemplo, por clase o sede)."
                ),
            )
        # Se avanza por lo que realmente llegó: si Supabase limita las filas por respuesta
        # (max_rows) a menos que LOTE_EXPORTACION, cortar con "len(lote) < LOTE_EXPORTACION"
        # dejaba la exportación incompleta sin avisar.
        offset += len(lote)

    usuarios = [
        u for f in filas_totales
        if _cumple_filtro_estado(u := _armar_usuario_filtrado(f), estado_norm)
    ]

    if id_sede and not rol_norm:
        usuarios = [u for u in usuarios if u.id_sede == id_sede]

    if id_plan:
        usuarios = [u for u in usuarios if u.id_plan == id_plan]

    return usuarios