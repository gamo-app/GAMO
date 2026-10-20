from supabase_config import get_supabase
from postgrest import APIError


async def get_all_clases(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("clase").select("*").execute()
    except APIError as e:
          return f'<p>Error ar cargar clases: {e.message}</p>'
    
    return response.data