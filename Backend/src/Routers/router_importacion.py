from fastapi import APIRouter, Request
from Base import base_importacion as importacion

router = APIRouter()


@router.get("")
async def get_importacion(request: Request):
    return await importacion.get_all_importaciones(request.scope["env"])
    
