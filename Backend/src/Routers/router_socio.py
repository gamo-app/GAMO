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
    #falta la auth del usuario para saber si tiene permisos 
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

#get socio por estado ya no funciona porque se saco estado de socio pero es remplazar por usuario y funcionaria
@router.get("/rol/{rol}/estado/{estado}")
async def get_socios_estado(request: Request, rol: str, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio_all_estado(request.scope["env"], rol,  estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def socio_all_estado(env, rol: str , estado: str):
    url, key = get_supabase_config(env)
    
    response = await fetch(
        f"{url}/rest/v1/socio?select=id_socio,estado,persona!inner(telefono,nombre,apellido,usuario!inner(email,grupo_usuario!inner(nombre)))&persona.usuario.grupo_usuario.nombre=eq.{rol}&estado=eq.{estado}",
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



#Cambiar el estado de un socio
@router.post("/persona/{id_persona}/estado/{estado}")
async def patch_socios_estado(request: Request, id_persona: int, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await actualizar_estado_usuario_general(request.scope["env"], id_persona,  estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
async def actualizar_estado_usuario_general(env, id_persona: int, estado: str):
    
  url, key = get_supabase_config(env)
  response = await fetch(
      f"{url}/rest/v1/rpc/actualizar_estado_usuario_general",
      method="POST",
      headers={
          "apikey": key,
          "Authorization": f"Bearer {key}",
          "Content-Type": "application/json",
      },
      body={
          "p_id_persona": id_persona,
          "p_nuevo_estado": estado,
      },
  )

  if not response.ok:
    raise HTTPException(status_code=response.status, detail=await response.text())
  resultado = await response.json()
  return {"status": "success", "message": "Estado actualizado correctamente", "data": resultado}