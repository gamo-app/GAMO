from datetime import date
from fastapi import HTTPException
from supabase_config import get_supabase
from postgrest import APIError

from Base import base_socio as socio





async def get_all_asistencias(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("asistencia").select("*").execute()
    except APIError as e:
        return f'<p>Error ar cargar asistencias: {e.message}</p>'
    return response.data

async def get_historial_asistencia_socio(env, codigo_credencial : int, desde : date | None = None, hasta : date | None = None):

    if not await socio.socio_exists(env, codigo_credencial):
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    supabase = get_supabase(env)


    request = supabase.table("asistencia").select("*,clase(*)").eq("codigo_credencial", codigo_credencial)

    if desde:
        request.gte("fecha", desde.isoformat())
    if hasta:
        request.lte("fecha", hasta.isoformat())
    
    try:
        response = request.execute()
    except APIError as e:
        return f'<p>Error ar cargar historial de asistencias: {e.message}</p>'
    return response.data



