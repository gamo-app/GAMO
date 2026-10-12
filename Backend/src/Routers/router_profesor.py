from fastapi import APIRouter, Request
from Base import base_profesor as profesor

router = APIRouter()


@router.get("")
async def get_profesores(request: Request):
    return await profesor.get_all_profesores(request.scope["env"])

