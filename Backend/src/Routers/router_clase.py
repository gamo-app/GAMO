from fastapi import APIRouter, Request
from Base import base_clase as clase

router = APIRouter()


@router.get("")
async def get_clase(request: Request):
    return await clase.get_all_clases(request.scope["env"])

