from fastapi import APIRouter, Request
from Base import base_grupos_roles as grupo


router = APIRouter()


@router.get("")
async def get_grupos_roles(request: Request):
    return await grupo.get_all_grupos_roles(request.scope["env"])

  