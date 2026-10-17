from fastapi import APIRouter, Request, Depends
from Base import base_sede as sede
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_sedes(request: Request, access_token: str = Depends(validar_sesion),):
    return await sede.get_all_sedes(request.scope["env"], access_token)
    
