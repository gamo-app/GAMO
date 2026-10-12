from fastapi import HTTPException, APIRouter, Request
from supabase_config import get_supabase_config
from workers import fetch

router = APIRouter()


@router.get("")
async def get_grupos_roles(request: Request):
    return await get_all_grupos_roles(request.scope["env"])

async def get_all_grupos_roles(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/grupo_usuario?select=*",
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
    return await response.json()    