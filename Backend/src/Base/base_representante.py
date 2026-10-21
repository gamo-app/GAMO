from urllib.parse import quote
from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch
from supabase_config import get_supabase
from postgrest import APIError

async def get_all_representantes(env):
    supabase = get_supabase(env)
    try:
        response = supabase.table("representante").select("*").execute()
    except APIError as e:
            return f'<p>Error ar cargar representantes: {e.message}</p>'

    return response.data   


async def buscar_representantes(
    env,
    nombre: str | None = None,
    apellido: str | None = None,
    dni: str | None = None,
    id_persona: int | None = None,
    id_deporte: int | None = None,
    deporte: str | None = None,
    id_sede: int | None = None,
    sede: str | None = None,
):
    url, key = get_supabase_config(env)

    filtros = [
        "select=id_representante,id_persona,id_deporte,id_sede,"
        "persona!inner(nombre,apellido,dni,telefono,fecha_nacimiento),"
        "deporte!inner(nombre),"
        "sede!inner(nombre)"
    ]

    # Busqueda  sin distinguir mayusculas
    if nombre:
        filtros.append(f"persona.nombre=ilike.*{quote(nombre)}*")
    if apellido:
        filtros.append(f"persona.apellido=ilike.*{quote(apellido)}*")
    if deporte:
        filtros.append(f"deporte.nombre=ilike.*{quote(deporte)}*")
    if sede:
        filtros.append(f"sede.nombre=ilike.*{quote(sede)}*")

    # Busqueda exacta
    if dni:
        filtros.append(f"persona.dni=eq.{quote(dni)}")
    if id_persona is not None:
        filtros.append(f"id_persona=eq.{id_persona}")
    if id_deporte is not None:
        filtros.append(f"id_deporte=eq.{id_deporte}")
    if id_sede is not None:
        filtros.append(f"id_sede=eq.{id_sede}")

    response = await fetch(
        f"{url}/rest/v1/representante?{'&'.join(filtros)}",
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
