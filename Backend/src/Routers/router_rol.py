from fastapi import APIRouter, Request
from Base import base_rol as rol


router = APIRouter()


@router.get("")
async def get_grupos_roles(request: Request):
    return await rol.get_all_roles(request.scope["env"])

  