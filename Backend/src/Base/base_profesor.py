from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch

async def get_all_profesores(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/profesor?select=*",
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
    return  await response.json()    