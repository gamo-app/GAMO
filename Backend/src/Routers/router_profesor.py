from fastapi import APIRouter, Request, Depends
from Base import base_profesor as profesor
from auth import validar_sesion
router = APIRouter()


@router.get("")
async def get_profesores(request: Request, access_token: str = Depends(validar_sesion),):
    return await profesor.get_all_profesores(request.scope["env"], access_token)
