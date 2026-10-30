from fastapi import APIRouter, Depends, Request
from Base import base_representante as representante
from auth import validar_acceso_administrativo

router = APIRouter()


@router.get("")
async def get_representantes(
    request: Request,
    access_token: str = Depends(validar_acceso_administrativo),
):
    return await representante.get_all_representantes(
        request.scope["env"],
        access_token,
    )
