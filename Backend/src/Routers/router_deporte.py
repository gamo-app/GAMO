from fastapi import APIRouter, Request
from Base import base_deporte as deporte

router = APIRouter()


@router.get("")
async def get_deporte(request: Request):
    return await deporte.get_all_deportes(request.scope["env"])

