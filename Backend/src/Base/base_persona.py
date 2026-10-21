from supabase_config import get_supabase
from postgrest import APIError

async def get_all_personas(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("persona").select("*").execute()
    except APIError as e:
            return f'<p>Error ar cargar personas: {e.message}</p>'

    return response.data  