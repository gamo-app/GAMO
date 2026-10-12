from fastapi import APIRouter, Request
from Base import base_persona as persona

router = APIRouter()


@router.get("")
async def get_persona(request: Request):
    return await persona.get_all_personas(request.scope["env"])

