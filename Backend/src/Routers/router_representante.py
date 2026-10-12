from fastapi import APIRouter, Request
from Base import base_representante as representante

router = APIRouter()


@router.get("")
async def get_representantes(request: Request):
    return await representante.get_all_representantes(request.scope["env"])
    
