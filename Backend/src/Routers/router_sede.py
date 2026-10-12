from fastapi import APIRouter, Request
from Base import base_sede as sede
router = APIRouter()


@router.get("")
async def get_sedes(request: Request):
    return await sede.get_all_sedes(request.scope["env"])
    
