
from fastapi import APIRouter, Request, Response
from model import LoginData
from supabase_config import get_supabase_config
from workers import fetch
from supabase import create_async_client
from Base import base_login
router = APIRouter()


@router.post("")
async def iniciar_sesion(request: Request,datos: LoginData, response: Response,):
    return await base_login.login(request.scope["env"], datos,  response)


@router.get("/auth/me")
async def consultar_sesion(request: Request):
    return await base_login.obtener_sesion(request.scope["env"], request)


@router.post("/logout")
async def cerrar_sesion(request: Request,response: Response,):
    env = request.scope["env"]
    return await base_login.logout(env, request, response)