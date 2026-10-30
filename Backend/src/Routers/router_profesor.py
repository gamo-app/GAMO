from fastapi import APIRouter, Request, Depends
from Base import base_profesor as profesor
from auth import validar_acceso_administrativo
router = APIRouter()


@router.get("")
async def get_profesores(
    request: Request,
    access_token: str = Depends(validar_acceso_administrativo),
):
    return await profesor.get_all_profesores(request.scope["env"], access_token)
