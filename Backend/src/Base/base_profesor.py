from supabase_config import get_supabase
from postgrest import APIError

async def get_all_profesores(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("profesor").select("*").execute()
    except APIError as e:
            return f'<p>Error ar cargar profesores: {e.message}</p>'

    return response.data   