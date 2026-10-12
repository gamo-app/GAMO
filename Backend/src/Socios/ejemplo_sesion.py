from fastapi import APIRouter, Request, HTTPException
from supabase_config import get_supabase_config
from workers import fetch


router = APIRouter()


@router.get("/me/{id_usuario}")
async def get_mi_sesion(request: Request, id_usuario: str):

    return await get_sesion(
        request.scope["env"],
        id_usuario
    )


async def get_sesion(env, id_usuario: str):

    url, key = get_supabase_config(env)

    # ========================================================
    # 1. Obtener usuario
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/usuario"
        f"?id_usuario=eq.{id_usuario}"
        "&select=*",
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

    usuarios = await response.json()

    if not usuarios:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    usuario = usuarios[0]

    id_persona = usuario["id_persona"]
    id_grupo = usuario["id_grupo"]


    # ========================================================
    # 2. Obtener persona
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/persona"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
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

    personas = await response.json()

    if not personas:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    persona = personas[0]


    # ========================================================
    # 3. Obtener grupo / rol
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/grupo_usuario"
        f"?id_grupo=eq.{id_grupo}"
        "&select=*",
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

    grupos = await response.json()

    if not grupos:
        raise HTTPException(
            status_code=404,
            detail="Grupo de usuario no encontrado"
        )

    grupo = grupos[0]


    # ========================================================
    # 4. Buscar si es socio
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/socio"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
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

    socios = await response.json()


    # ========================================================
    # 5. Buscar si es profesor
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/profesor"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
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

    profesores = await response.json()


    # ========================================================
    # 6. Buscar si es representante
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/representante"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
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

    representantes = await response.json()


    # ========================================================
    # 7. Construir respuesta
    # ========================================================

    return {
        "usuario": usuario,
        "persona": persona,
        "rol": grupo,
        "socio": socios[0] if socios else None,
        "profesor": profesores[0] if profesores else None,
        "representante": representantes[0] if representantes else None
    }