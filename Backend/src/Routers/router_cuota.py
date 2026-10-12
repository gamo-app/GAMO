from fastapi import APIRouter, Request
from Base import base_cuota as cuota


router = APIRouter()


@router.get("")
async def get_cuota(request: Request):
    return await cuota.get_all_cuotas(request.scope["env"])

