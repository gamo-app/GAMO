from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch

async def get_all_cuotas(env, access_token:str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/cuota?select=*",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {access_token}",
            },
        )

    if not response.ok:
                raise HTTPException(
                    status_code=response.status,
                    detail=await response.text(),
                )    
    return await response.json()    