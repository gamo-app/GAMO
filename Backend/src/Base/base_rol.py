from datetime import date, timedelta
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

ROLES_VALIDOS = {"socio", "profesor", "representante", "administrador"}
ESTADOS_VALIDOS = {"activo", "inactivo", "suspendido", "moroso", "al_dia", "pendiente"}

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
    "suspendido": "suspendido",
    "suspendidos": "suspendido",
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

        # Usar el token del usuario para respetar las políticas RLS
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


# ---------------------------------------------------------------------------
# Funciones auxiliares de filtrado
# ---------------------------------------------------------------------------

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

    dias_vencido = (date.today() - fecha_fin).days
    if dias_vencido <= 0:
        return "activo", EstadoDePagoSocioEnum.al_dia.value, False
    if dias_vencido > DIAS_PARA_CONSIDERAR_MOROSO:
        return "activo", EstadoDePagoSocioEnum.moroso.value, True
    return "activo", EstadoDePagoSocioEnum.pendiente.value, False


def _armar_usuario_filtrado(fila: dict[str, Any]) -> UsuarioFiltradoResponse:
    rol_data = _primero(fila.get("rol"))
    socio_data = _primero(fila.get("socio"))
    profesor_data = _primero(fila.get("profesor"))
    representante_data = _primero(profesor_data.get("representante"))
    deporte_data = _primero(representante_data.get("deporte"))

    clase_data = _primero(profesor_data.get("clase"))
    sede_data = _primero(clase_data.get("sede"))

    membresia_actual = _ultima_membresia(socio_data.get("membresia"))
    plan_data = _primero(membresia_actual.get("plan"))
    pago_actual = _ultimo_pago(membresia_actual.get("pago"))

    es_socio = bool(socio_data) or _clave_rol(rol_data.get("nombre")) == "socio"
    estado_usr, estado_cuota, es_moroso = _calcular_estado_membresia(
        membresia_actual, es_socio
    )

    monto = pago_actual.get("monto")
    if monto is None and plan_data.get("precio_semanal") is not None:
        monto = Decimal(str(plan_data["precio_semanal"]))
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
        id_deporte=deporte_data.get("id_deporte"),
        deporte=deporte_data.get("nombre"),
        id_sede=sede_data.get("id_sede"),
        sede=sede_data.get("nombre"),
    )


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

    if estado_norm == "moroso" and rol_norm in ("profesor", "representante", "administrador"):
        return ListadoUsuariosResponse(
            datos=[],
            paginacion=PaginacionUsuariosInfo(
                paginaActual=page,
                elementosPorPagina=limit,
                totalPaginas=0,
                totalRegistros=0,
            ),
        )

    j_socio = (
        "socio!inner"
        if (estado_norm in ("moroso", "activo", "al_dia", "pendiente") or id_plan)
        else "socio"
    )
    j_memb = (
        "membresia!inner"
        if (estado_norm in ("moroso", "activo", "al_dia", "pendiente") or id_plan)
        else "membresia"
    )
    j_prof = (
        "profesor!inner"
        if (id_deporte or id_sede or rol_norm == "representante")
        else "profesor"
    )
    j_rep = (
        "representante!inner"
        if (id_deporte or rol_norm == "representante")
        else "representante"
    )
    j_clase = "clase!inner" if id_sede else "clase"

    select_usuarios = (
        "uuid_usuario,DNI,nombre,apellido,fecha_nacimiento,id_rol,"
        "rol!inner(id_rol,nombre),"
        f"{j_socio}(codigo_credencial,"
        f"{j_memb}(id_membresia,id_plan,fecha_inicio,fecha_fin,porcentaje_descuento,"
        "plan(id_plan,nombre,precio_semanal,clases_semanales),"
        "pago(id_pago,monto))),"
        f"{j_prof}(id_profesor,"
        f"{j_rep}(id_representante,id_deporte,deporte(id_deporte,nombre)),"
        f"{j_clase}(id_sede,sede(id_sede,nombre)))"
    )

    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    query_parts = [
        f"select={quote(select_usuarios, safe='(),!*')}",
        "order=apellido.asc,uuid_usuario.asc",
    ]

    if rol_norm and rol_norm != "representante":
        query_parts.append(f"rol.nombre=ilike.{quote(rol_norm, safe='')}%25")

    hoy = date.today()
    fecha_limite_moroso = (hoy - timedelta(days=DIAS_PARA_CONSIDERAR_MOROSO)).isoformat()

    if estado_norm == "moroso":
        query_parts.append(f"socio.membresia.fecha_fin=lt.{fecha_limite_moroso}")
    elif estado_norm in ("activo", "al_dia") and rol_norm == "socio":
        query_parts.append(f"socio.membresia.fecha_fin=gte.{hoy.isoformat()}")
    elif estado_norm == "pendiente":
        query_parts.append(f"socio.membresia.fecha_fin=lt.{hoy.isoformat()}")
        query_parts.append(f"socio.membresia.fecha_fin=gte.{fecha_limite_moroso}")

    if id_plan:
        query_parts.append(f"socio.membresia.id_plan=eq.{id_plan}")
    if id_deporte:
        query_parts.append(f"profesor.representante.id_deporte=eq.{id_deporte}")
    if id_sede:
        query_parts.append(f"profesor.clase.id_sede=eq.{id_sede}")

    terminos = _terminos_de_busqueda(buscar)
    if len(terminos) == 1:
        or_cond = ",".join(_condiciones_para(terminos[0]))
        query_parts.append(f"or=({quote(or_cond, safe=',.*')})")
    elif len(terminos) > 1:
        grupos_or = [f"or({','.join(_condiciones_para(p))})" for p in terminos]
        and_cond = ",".join(grupos_or)
        query_parts.append(f"and=({quote(and_cond, safe=',().*')})")

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