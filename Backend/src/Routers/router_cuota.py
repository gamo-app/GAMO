from fastapi import APIRouter, Request, Depends
from Base import base_cuota as cuota
from auth import validar_sesion

router = APIRouter()


@router.get("")
async def get_cuota(request: Request, access_token: str = Depends(validar_sesion),):
    return await cuota.get_all_cuotas(request.scope["env"],access_token)
