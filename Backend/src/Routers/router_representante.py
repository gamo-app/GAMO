from fastapi import APIRouter, Request, Depends
from Base import base_representante as representante
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_representantes(request: Request, access_token: str = Depends(validar_sesion),):
    return await representante.get_all_representantes(request.scope["env"], access_token)
    
