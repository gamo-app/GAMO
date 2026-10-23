from supabase_config import get_supabase
from postgrest import APIError
from model import EstadoDePagoEnum
from Base import base_membresia as membresia

async def get_all_pagos(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("pago").select("*").execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas: {e.message}</p>'
    
    return response.data

async def get_pagos_by_socio(env, codigo_credencial):
    supabase = get_supabase(env)
    membresias = await membresia.get_ids_membresias_by_socio(env, codigo_credencial)
    
    try:
        response = supabase.table("pago").select("*").in_("id_membresia", membresias).execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas por socio: {e.message}</p>'

    return response.data

async def get_pagos_of_type_by_socio(env, id_socio : int, estado_cuota: EstadoDePagoEnum):
    supabase = get_supabase(env)
    try:
        response = supabase.table("pago").select("*").eq("id_socio", id_socio).eq("estado", estado_cuota.value).execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas por socio: {e.message}</p>'

    return response.data
