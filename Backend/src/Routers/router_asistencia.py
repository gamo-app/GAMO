
from Base import base_asistencia as asistencia
from fastapi import APIRouter, Request
router = APIRouter()


@router.get("")
async def get_asistencia(request: Request):
    return await asistencia.get_all_asistencias(request.scope["env"])

