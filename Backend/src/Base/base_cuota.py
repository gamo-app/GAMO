from supabase_config import get_supabase
from postgrest import APIError
from model import EstadoDePagoEnum

async def get_all_cuotas(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("cuota").select("*").execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas: {e.message}</p>'
    
    return response.data

async def get_cuotas_by_socio(env, id_socio : int):
    supabase = get_supabase(env)
    try:
        response = supabase.table("cuota").select("*").eq("id_socio", id_socio).execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas por socio: {e.message}</p>'

    return response.data

async def get_cuotas_of_type_by_socio(env, id_socio : int, estado_cuota: EstadoDePagoEnum):
    supabase = get_supabase(env)
    try:
        response = supabase.table("cuota").select("*").eq("id_socio", id_socio).eq("estado", estado_cuota.value).execute()
    except APIError as e:
          return f'<p>Error ar cargar cuotas por socio: {e.message}</p>'

    return response.data
