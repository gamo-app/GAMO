from fastapi import APIRouter, Request
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from supabase_config import get_supabase_config
from workers import fetch
import json
# Los datos ingresados en el formulario son enviados correctamente al backend y el sistema registra
# al nuevo socio en la base de datos.


router = APIRouter()

#get all representantes 
@router.get("")
async def get_all_representantes(request: Request):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await get_representantes(request.scope["env"])
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def get_representantes(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/representante?select=*",
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


    
    
async def get_representante_by_id(env, id_representante: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/representante?id_representante=eq.{id_representante}&select=*",
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



