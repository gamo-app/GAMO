from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch

async def get_all_socios(env):
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


async def get_socio_by_name(env, nombre: str, apellido: str):
    nombre = nombre + "*"
    apellido = apellido + "*"
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/socio?select=*&persona.nombre=ilike.{nombre}&persona.apellido=ilike.{apellido}",
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
async def get_estado_pago(env, id_usuario: int):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/estado_pago?select=*&id_usuario=eq.{id_usuario}",
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

    return await response.json()'''