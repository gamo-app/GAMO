from fastapi import APIRouter, Request
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from supabase_config import get_supabase_config
from workers import fetch
import json
# Los datos ingresados en el formulario son enviados correctamente al backend y el sistema registra
# al nuevo socio en la base de datos.


router = APIRouter()

#get all socios 
@router.get("")
async def get_all_socios(request: Request):
    try:
        return await get_socios(request.scope["env"])
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def get_socios(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?select=*",
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

#get socio por estado
@router.get("/estado/{estado}")
async def get_socios_nombre(request: Request, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio_nombre(request.scope["env"], estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def socio_nombre(env, estado: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?estado=eq.{estado.strip()}&select=*",
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

async def get_socio_by_id(env, id_socio: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?id_socio=eq.{id_socio}&select=*",
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



