from supabase_config import get_supabase
from supabase_config import get_supabase
from postgrest import APIError

async def get_all_deportes(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("deportes").select("*").execute()
    except APIError as e:
            return f'<p>Error ar cargar deportes: {e.message}</p>'

    return response.data  