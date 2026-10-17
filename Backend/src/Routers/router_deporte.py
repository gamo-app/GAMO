from fastapi import APIRouter, Request, Depends
from Base import base_deporte as deporte
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_deporte(request: Request, access_token: str = Depends(validar_sesion),):
    return await deporte.get_all_deportes(request.scope["env"],access_token)
