from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch
from model import EstadoDePagoEnum

async def get_all_cuotas(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/cuota?select=*",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
        )
    print(response)
    if not response.ok:
                raise HTTPException(
                    status_code=response.status,
                    detail=await response.text(),
                )    
    return await response.json()    


async def get_cuotas_by_socio(env, id_socio: int):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/cuota?id_socio=eq.{id_socio}",
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

async def get_cuotas_of_type_by_socio(env, id_socio: int, estado_cuota: EstadoDePagoEnum):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/cuota?select=*&estado=eq.{estado_cuota.value}&id_socio=eq.{id_socio}",
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