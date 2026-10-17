from fastapi import APIRouter, Request, Depends
from Base import base_importacion as importacion
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_importacion(request: Request, access_token: str = Depends(validar_sesion),):
    return await importacion.get_all_importaciones(request.scope["env"],access_token)
    
