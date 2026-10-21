from supabase_config import get_supabase
from postgrest import APIError
async def get_all_sedes(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("sede").select("*").execute()
    except APIError as e:
        return f"Error al cargar sedes: {e.message}"

    return response