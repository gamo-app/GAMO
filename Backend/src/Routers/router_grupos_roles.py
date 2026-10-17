from fastapi import APIRouter, Request, Depends
from Base import base_grupos_roles as grupo
from auth import validar_sesion

router = APIRouter()


@router.get("")
async def get_grupos_roles(request: Request, access_token: str = Depends(validar_sesion),):
    return await grupo.get_all_grupos_roles(request.scope["env"], access_token)

  