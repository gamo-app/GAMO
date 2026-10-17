import json
import logging
import math
import re
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import quote
from fastapi import HTTPException
from pydantic import BaseModel
from supabase_config import get_supabase_config
from workers import fetch

logger = logging.getLogger(__name__)

# Alineado con EstadoUsuarioEnum de model.py
EstadoUsuario = Literal["activo", "inactivo", "suspendido"]


# ==========================================
# MODELOS DE RESPUESTA (FILTRO Y PAGINACIÓN)
# ==========================================

class SocioResponse(BaseModel):
    id_socio: Optional[int] = None
    id_persona: Optional[int] = None
    id_sede: Optional[int] = None
    codigo_credencial: Optional[str] = None
    sede: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[str] = None
    plan: Optional[str] = None
    fecha_alta: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    estado_cuota: Optional[str] = "sin_cuota"
    monto_cuota: Optional[float] = None


class PaginacionInfo(BaseModel):
    paginaActual: int
    elementosPorPagina: int
    totalPaginas: int
    totalSocios: int


class ListadoSociosResponse(BaseModel):
    datos: List[SocioResponse]
    paginacion: PaginacionInfo


SELECT_SOCIOS = (
    "id_persona,nombre,apellido,dni,telefono,"
    "usuario(email,estado),"
    "socio!inner(id_socio,id_sede,fecha_alta,codigo_credencial,"
    "sede(nombre),"
    "membresia(estado,plan_membresia(nombre)),"
    "cuota(id_cuota,fecha_vencimiento,estado,monto))"
)


async def _error_upstream(response, mensaje: str) -> HTTPException:
    """Loguea el detalle real del error de Supabase y lo incluye en el 502 para depuración."""
    try:
        detalle = await response.text()
    except Exception:
        detalle = "<sin detalle>"
    logger.error("%s (status %s): %s", mensaje, response.status, detalle)
    return HTTPException(
        status_code=502,
        detail=f"{mensaje} (Supabase {response.status}): {detalle}",
    )


def _terminos_de_busqueda(buscar: Optional[str]) -> List[str]:
    if not buscar or not buscar.strip():
        return []
    limpio = re.sub(r'[,()%*_"\\]', " ", buscar.strip())
    return [t for t in limpio.split() if t][:5]


def _condiciones_para(palabra: str) -> List[str]:
    condiciones = [
        f"nombre.ilike.*{palabra}*",
        f"apellido.ilike.*{palabra}*",
    ]
    # Acepta DNI escrito con puntos (12.345.678) y permite coincidencia parcial
    solo_digitos = palabra.replace(".", "")
    if solo_digitos.isascii() and solo_digitos.isdigit() and len(solo_digitos) <= 9:
        condiciones.append(f"dni.ilike.*{solo_digitos}*")
    return condiciones


def _primero(valor: Any) -> Dict[str, Any]:
    """PostgREST devuelve una relación como objeto o como lista según la FK."""
    if isinstance(valor, list):
        return valor[0] if valor else {}
    return valor or {}


def _ultima_cuota(cuotas: Any) -> Optional[Dict[str, Any]]:
    if not cuotas:
        return None
    if isinstance(cuotas, dict):
        return cuotas
    return max(cuotas, key=lambda c: c.get("fecha_vencimiento") or "")


def _obtener_plan(membresias: Any) -> Optional[str]:
    if not membresias:
        return None
    lista = membresias if isinstance(membresias, list) else [membresias]
    # En la base de datos el enum estado_membresia utiliza 'activa'
    activa = next(
        (m for m in lista if m.get("estado") in ("activa", "activo")),
        lista[0],
    )
    plan_data = _primero(activa.get("plan_membresia"))
    return plan_data.get("nombre")


def _texto(valor: Any) -> Optional[str]:
    return None if valor is None else str(valor)


def _armar_socio(persona: Dict[str, Any]) -> Dict[str, Any]:
    socio_data = _primero(persona.get("socio"))
    usuario_data = _primero(persona.get("usuario"))
    sede_data = _primero(socio_data.get("sede"))
    cuota = _ultima_cuota(socio_data.get("cuota")) or {}

    return {
        "id_socio": socio_data.get("id_socio"),
        "id_persona": persona.get("id_persona"),
        "id_sede": socio_data.get("id_sede"),
        "codigo_credencial": socio_data.get("codigo_credencial"),
        "sede": sede_data.get("nombre"),
        "nombre": persona.get("nombre"),
        "apellido": persona.get("apellido"),
        "dni": _texto(persona.get("dni")),
        "telefono": _texto(persona.get("telefono")),
        "email": usuario_data.get("email"),
        "estado": usuario_data.get("estado"),
        "plan": _obtener_plan(socio_data.get("membresia")),
        "fecha_alta": socio_data.get("fecha_alta"),
        "fecha_vencimiento": cuota.get("fecha_vencimiento"),
        "estado_cuota": cuota.get("estado") or "sin_cuota",
        "monto_cuota": cuota.get("monto"),
    }


def _extraer_total(content_range: Optional[str]) -> int:
    if not content_range or "/" not in content_range:
        return 0
    total_str = content_range.split("/")[-1]
    return int(total_str) if total_str.isdigit() else 0


async def obtener_socios_paginados(
    env, page: int, limit: int, buscar: Optional[str] = None
) -> dict:
    url, key = get_supabase_config(env)

    if page < 1:
        raise HTTPException(status_code=400, detail="La pagina debe ser mayor o igual a 1")
    if limit < 1:
        raise HTTPException(status_code=400, detail="El limite debe ser mayor o igual a 1")

    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    query_parts = [
        f"select={quote(SELECT_SOCIOS, safe='(),!*')}",
        "order=apellido.asc,id_persona.asc",
        "socio.cuota.order=fecha_vencimiento.desc",
        "socio.cuota.limit=1",
    ]

    terminos = _terminos_de_busqueda(buscar)
    if len(terminos) == 1:
        or_cond = ",".join(_condiciones_para(terminos[0]))
        query_parts.append(f"or=({quote(or_cond, safe=',.*')})")
    elif len(terminos) > 1:
        grupos_or = [f"or({','.join(_condiciones_para(p))})" for p in terminos]
        and_cond = ",".join(grupos_or)
        query_parts.append(f"and=({quote(and_cond, safe=',().*')})")

    full_url = f"{url}/rest/v1/persona?{'&'.join(query_parts)}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Prefer": "count=exact",
        "Range-Unit": "items",
        "Range": f"{inicio}-{fin}",
    }

    response = await fetch(full_url, headers=headers)

    if response.status == 416:
        headers["Range"] = "0-0"
        response_count = await fetch(full_url, headers=headers)
        if not response_count.ok:
            raise await _error_upstream(response_count, "Error al consultar los socios")
        total_socios = _extraer_total(response_count.headers.get("content-range"))
        filas = []
    elif not response.ok:
        raise await _error_upstream(response, "Error al consultar los socios")
    else:
        filas = await response.json()
        total_socios = _extraer_total(response.headers.get("content-range"))

    datos = [_armar_socio(fila) for fila in filas]
    total_paginas = math.ceil(total_socios / limit) if total_socios else 0

    return {
        "datos": datos,
        "paginacion": {
            "paginaActual": page,
            "elementosPorPagina": limit,
            "totalPaginas": total_paginas,
            "totalSocios": total_socios,
        },
    }


async def get_all_socios(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise await _error_upstream(response, "Error al consultar los socios")

    return await response.json()


async def socio_all_estado(env, rol: str, estado: str):
    url, key = get_supabase_config(env)

    select = (
        "id_socio,persona!inner(telefono,nombre,apellido,"
        "usuario!inner(email,estado,grupo_usuario!inner(nombre)))"
    )
    full_url = (
        f"{url}/rest/v1/socio"
        f"?select={quote(select, safe='(),!')}"
        f"&persona.usuario.grupo_usuario.nombre=eq.{quote(rol, safe='')}"
        f"&persona.usuario.estado=eq.{quote(estado, safe='')}"
    )

    response = await fetch(
        full_url,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise await _error_upstream(response, "Error al consultar los socios")

    return await response.json()


async def actualizar_estado_usuario_general(env, id_persona: int, estado: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/rpc/actualizar_estado_usuario_general",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        body=json.dumps({
            "p_id_persona": id_persona,
            "p_nuevo_estado": estado,
        }),
    )

    if not response.ok:
        raise await _error_upstream(response, "Error al actualizar el estado")

    try:
        resultado = await response.json()
    except Exception:
        resultado = None

    return {
        "status": "success",
        "message": "Estado actualizado correctamente",
        "data": resultado,
    }