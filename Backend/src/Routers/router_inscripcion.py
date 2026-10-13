from fastapi import APIRouter, Request
from Base import base_inscripcion as inscripcion

router = APIRouter()


@router.get("")
async def get_inscripcion(request: Request):
    return await inscripcion.get_all_inscripciones(request.scope["env"])
    
