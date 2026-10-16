from fastapi import HTTPException
from model import EstadoDePagoEnum
from supabase_config import get_supabase_config
from workers import fetch
from Base import base_cuota as cuota
from model import EstadoDePagoEnum

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




async def get_estado_pago_socio(env, id_socio):
    print("medie")
    #vencidas = await cuota.get_cuotas_of_type_by_socio(env, id_socio, EstadoDePagoEnum.pagada)
    #print(vencidas)
    #pendientes = await cuota.get_cuotas_of_type_by_socio(env, id_socio, EstadoDePagoEnum.pendiente)
    #return vencidas
    return await cuota.get_cuotas_by_socio(env, id_socio)




'''
async def get_cuotas_sin_pagar(env, id_socio: int):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/cuota?id_socio=eq.{id_socio}&estado=neq.{EstadoDePagoEnum.PAGADO}",
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