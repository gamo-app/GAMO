import os

from fastapi import APIRouter, Request
from fastapi import APIRouter, Depends, HTTPException
from supabase_config import get_supabase_config
from model import UsuarioCreate, LoginCreate
from profesores import get_trainer_by_id
from workers import fetch
import uuid
import json
import hashlib
import jwt

router = APIRouter()

#get all usuarios
@router.get("")
async def get_all_usuarios(request: Request):
    try:
        return await get_usuario(request.scope["env"])
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def get_usuario(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()    
#----------------------------------------#

@router.post("")
async def create_usuario(usuario: UsuarioCreate, request: Request):
    try:
        usuario_dict = usuario.model_dump(mode="json")
        
        password = usuario_dict.pop("password")
        
        return await create_user_with_auth(request.scope["env"], usuario_dict, password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def create_user_with_auth(env, datos_usuario: dict, password: str):
    url, key = get_supabase_config(env)

    # 1. Crear usuario en Supabase Auth
    auth_resp = await fetch(
        f"{url}/auth/v1/signup",
        method="POST",
        headers={
            "apikey": key,
            "Content-Type": "application/json",
        },
        body=json.dumps({
            "email": datos_usuario["email"],
            "password": password,
        }),
    )

    if not auth_resp.ok:
        raise HTTPException(
            status_code=auth_resp.status,
            detail=f"Error en Auth: {await auth_resp.text()}",
        )

    auth_data = await auth_resp.json()
    user_info = auth_data.get("user") or auth_data
    auth_uuid = user_info["id"]  # Este UUID generado por Auth se usará como FK

    # 2. Insertar en public.usuario usando ese UUID válido
    datos_usuario["id_usuario"] = auth_uuid

    db_resp = await fetch(
        f"{url}/rest/v1/usuario",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        body=json.dumps(datos_usuario),
    )

    if not db_resp.ok:
        raise HTTPException(
            status_code=db_resp.status,
            detail=await db_resp.text(),
        )

    return await db_resp.json()




def hash(password : str, salt : bytes) -> str:
    return hashlib.sha256(salt + password.encode()).hexdigest()

def get_random_salt() -> bytes:
    return os.urandom(16)


@router.post("/login")
async def router_login(login: LoginCreate, request: Request):
    try:
        return await login(request.scope["env"], login.email, login.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=700, detail=str(e))


async def login(env, email : str, password : str):

    user = await get_user_from_email(env, email)
    salt : bytes = user.get("salt", None)

    hashed_object : str = hash(password, salt)
    if hashed_object == user.get("hash", None):
        return {"jwt": await generate_jwt(env, user.get("id_usuario"))}
    else:
        return {"jwt_falso": jwt.encode({"user_id": "68b79ba5-e7b6-4e2c-a9d2-38d46b1772c4", "group" : "Socio"}, JWT_SECRET, algorithm="HS256")}
 
JWT_SECRET = "your_secret_key"  # Cambia esto
async def generate_jwt(env, user_id: str):
    payload = {
        "user_id": user_id,
        "group": await get_user_group(env, user_id),
        #"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expira en 1 hora
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token



async def get_user_group(env, user_id: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?id_usuario=eq.{user_id}&select=grupo_usuario(nombre)",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    data = await response.json()
    return data[0]["grupo"]["nombre"]
    

#----------------------------------------#

async def get_user_from_email(env, email : str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?email=eq.{email.strip()}&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()


'''
trigger de sql (puede que esté algo mal)

CREATE TRIGGER set_payment_status
AFTER UPDATE ON deudas_pagos
FOR EACH ROW
BEGIN
    IF NEW.fecha_pago is not NULL and NEW.fecha_pago != "" THEN
        UPDATE socio SET estado_pago = "Al día"
END
'''




