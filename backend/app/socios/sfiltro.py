import logging
import math
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from postgrest.exceptions import APIError
from pydantic import BaseModel
from supabase import Client

from app.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()



class SocioResponse(BaseModel):
    id_socio: Optional[int] = None
    codigo_credencial: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
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





CAMPOS_TEXTO: Dict[str, str] = {
    "nombre": "nombre",
    "apellido": "apellido",
}


CAMPOS_NUMERICOS: Dict[str, str] = {
    "dni": "dni",
}


SELECT_SOCIOS = (
    "id_persona, nombre, apellido, dni, telefono, "
    "socio!inner("
    "id_socio, codigo_credencial, fecha_alta, "
    "cuota(id_cuota, fecha_vencimiento, estado, monto)"
    ")"
)



def _terminos_de_busqueda(buscar: Optional[str]) -> List[str]:
    """Limpia caracteres especiales y devuelve hasta 5 palabras."""
    if not buscar or not buscar.strip():
        return []
    limpio = re.sub(r'[,()%*_"\\]', " ", buscar.strip())
    return limpio.split()[:5]

def _condiciones_para(palabra: str) -> List[str]:
    condiciones = [f"{col}.ilike.%{palabra}%" for col in CAMPOS_TEXTO.values()]
    if palabra.isascii() and palabra.isdigit() and len(palabra) <= 9:
        condiciones += [f"{col}.eq.{palabra}" for col in CAMPOS_NUMERICOS.values()]
    return condiciones

def _ultima_cuota(cuotas: Any) -> Optional[Dict[str, Any]]:
    if not cuotas:
        return None
    if isinstance(cuotas, dict):
        return cuotas
    return max(cuotas, key=lambda c: c.get("fecha_vencimiento") or "")

def _texto(valor: Any) -> Optional[str]:
    """Convierte a str (o None) para que Pydantic no rechace números."""
    return None if valor is None else str(valor)

def _armar_socio(persona: Dict[str, Any]) -> Dict[str, Any]:
    """Aplana persona + socio + última cuota en un solo diccionario."""
    socio = persona.get("socio") or {}
    if isinstance(socio, list):
        socio = socio[0] if socio else {}

    cuota = _ultima_cuota(socio.get("cuota")) or {}

    return {
        "id_socio": socio.get("id_socio"),
        "codigo_credencial": _texto(socio.get("codigo_credencial")),
        "nombre": persona.get("nombre"),
        "apellido": persona.get("apellido"),
        "dni": _texto(persona.get("dni")),
        "telefono": _texto(persona.get("telefono")),
        "fecha_alta": socio.get("fecha_alta"),
        "fecha_vencimiento": cuota.get("fecha_vencimiento"),
        "estado_cuota": cuota.get("estado") or "sin_cuota",
        "monto_cuota": cuota.get("monto"),
    }


def _error_bd(e: APIError) -> HTTPException:
    """Loguea el detalle real y devuelve un error genérico al cliente."""
    logger.error("Supabase APIError | code=%s | message=%s | details=%s",
                 e.code, e.message, e.details)
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Error al consultar los socios",
    )




@router.get("", response_model=ListadoSociosResponse)
def obtener_socios_paginados(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Cantidad de socios por página"),
    buscar: Optional[str] = Query(
        None, max_length=50, description="Texto a buscar en nombre, apellido o DNI"
    ),
    supabase: Client = Depends(get_supabase),
):
    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    consulta = supabase.table("persona").select(SELECT_SOCIOS, count="exact")

    
    for palabra in _terminos_de_busqueda(buscar):
        consulta = consulta.or_(",".join(_condiciones_para(palabra)))

    try:
        respuesta = (
            consulta
            .order("apellido", desc=False)
            .order("id_persona", desc=False)
            .range(inicio, fin)
            .execute()
        )
        filas = respuesta.data or []
        total_socios = respuesta.count or 0

    except APIError as e:
        if e.code != "PGRST103":
            raise _error_bd(e)
        
        try:
            respuesta = consulta.range(0, 0).execute()
        except APIError as e2:
            raise _error_bd(e2)
        filas = []
        total_socios = respuesta.count or 0

    except Exception:
        logger.exception("Error no controlado al obtener los socios")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los socios",
        )

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