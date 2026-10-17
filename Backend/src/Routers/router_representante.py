from fastapi import APIRouter, Request
from Base import base_representante as representante

router = APIRouter()


@router.get("")
async def get_representantes(request: Request):
    return await representante.get_all_representantes(request.scope["env"])
    

@router.get("/buscar")
async def buscar_representantes(
    request: Request,
    nombre: str | None = None,
    apellido: str | None = None,
    dni: str | None = None,
    id_persona: int | None = None,
    id_deporte: int | None = None,
    deporte: str | None = None,
    id_sede: int | None = None,
    sede: str | None = None,
):
    return await representante.buscar_representantes(
        request.scope["env"],
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        id_persona=id_persona,
        id_deporte=id_deporte,
        deporte=deporte,
        id_sede=id_sede,
        sede=sede,
    )
