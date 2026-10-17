from fastapi import APIRouter, Request, Depends
from Base import base_inscripcion as inscripcion
from auth import validar_sesion

router = APIRouter()

@router.get("")
async def get_inscripcion(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await inscripcion.get_all_inscripciones(request.scope["env"],access_token)