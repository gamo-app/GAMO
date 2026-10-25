from fastapi import APIRouter, Depends, Request
from Base import base_rol as rol
from auth import validar_sesion

router = APIRouter()


@router.get("")
async def get_roles(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await rol.get_all_rol(request.scope["env"], access_token)