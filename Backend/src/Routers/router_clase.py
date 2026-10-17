from fastapi import APIRouter, Depends, Request
from Base import base_clase as clase
from auth import validar_sesion

router = APIRouter()


@router.get("")
async def get_clase(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await clase.get_all_clases(request.scope["env"], access_token)
