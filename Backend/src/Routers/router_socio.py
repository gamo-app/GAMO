from fastapi import APIRouter, Depends, Request

from auth import (
    validar_acceso_administrativo,
    validar_acceso_listado_socios,
    validar_sesion,
)
from Base import base_socio as socio
from model import SocioAltaCreate

router = APIRouter()


@router.post("", status_code=201)
async def crear_socio(
    datos: SocioAltaCreate,
    request: Request,
    access_token: str = Depends(validar_acceso_administrativo),
):
    return await socio.crear_usuario_socio(request.scope["env"], datos)


@router.get("/planes")
async def get_planes(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await socio.get_all_planes(request.scope["env"], access_token)


@router.get("")
async def get_socios(
    request: Request,
    access_token: str = Depends(validar_acceso_listado_socios),
):
    return await socio.get_all_socios(request.scope["env"], access_token)
