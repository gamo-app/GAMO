from fastapi import APIRouter, Request, Depends
from Base import base_persona as persona
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_persona(request: Request, access_token: str = Depends(validar_sesion),):
    return await persona.get_all_personas(request.scope["env"], access_token)
