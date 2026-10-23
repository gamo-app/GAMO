from supabase_config import get_supabase
from postgrest import APIError
import datetime

async def get_all_membresias(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("membresia").select("*").execute()
    except APIError as e:
        return f"Error al cargar membresias: {e.message}"
    
    return response.data

async def get_ids_membresias_by_socio(env, codigo_credencial : str):
    supabase = get_supabase(env)
    try:
        response = supabase.table("membresia").select("id_membresia").eq("codigo_credencial", codigo_credencial).execute()
    except APIError as e:
        return f"Error al cargar membresias de socio {codigo_credencial}: {e.message}"

    result = []

    for id in response.data:
        result.append(id["id_membresia"])
    
    return result

async def get_most_recent_membresia_by_socio(env, codigo_credencial : str):
    supabase = get_supabase(env)
    try:
        response = supabase.table("membresia").select("*").eq("codigo_credencial", codigo_credencial).order("fecha_fin", desc=True).limit(1).execute()
    except APIError as e:
        return f"Error al cargar membresias de socio {codigo_credencial}: {e.message}"

    if response.data:
        return response.data[0]

    return []

async def is_membresia_active(membresia):
    if not membresia:
        return False

    fecha_inicio = datetime.date.strptime(membresia["fecha_inicio"], "%Y-%m-%d")

    fecha_fin = datetime.date.strptime(membresia["fecha_fin"], "%Y-%m-%d")


    
    today = datetime.date.today()
    #today = datetime.date.strptime("2027-01-01", "%Y-%m-%d")

    return today >= fecha_inicio and today <= fecha_fin
        



