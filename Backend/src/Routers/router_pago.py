from fastapi import APIRouter, Request
from Base import base_pago as pago


router = APIRouter()


@router.get("")
async def get_cuota(request: Request):
    return await pago.get_all_pagos(request.scope["env"])


@router.get("/test-si-ves-esto-en-main-borralo/{codigo_credencial}")
async def test(request : Request, codigo_credencial : str):
    return await pago.get_pagos_by_socio(request.scope["env"], codigo_credencial)

