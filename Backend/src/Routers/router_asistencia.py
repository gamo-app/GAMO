from datetime import date
from Base import base_asistencia as asistencia
from fastapi import APIRouter, Request
router = APIRouter()


@router.get("")
async def get_asistencia(request: Request):
    return await asistencia.get_all_asistencias(request.scope["env"])


@router.get("/socio/{id_socio}")
async def get_historial_asistencia_socio(
    request: Request,
    id_socio: int,
    desde: date | None = None,
    hasta: date | None = None,
):

    
    return await asistencia.get_historial_asistencia_socio(
        request.scope["env"], id_socio, desde=desde, hasta=hasta
    )
