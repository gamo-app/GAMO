

from fastapi import APIRouter, Request, Response, HTTPException
from model import LoginData
from Base import base_login as login
from supabase_config import get_supabase_config
from workers import fetch


router = APIRouter()

@router.post("/login")
async def login_endpoint(datos: LoginData, request: Request, response: Response, ):
    return await login.login(request.scope["env"], datos, request, response)
    
    

@router.get("/me")
async def get_obtener_sesion(request: Request):
    return await login.obtener_sesion(request.scope["env"], request)

@router.post("/logout")
async def logout_endpoint(request: Request, response: Response):
    return await login.logout(request.scope["env"], request, response)