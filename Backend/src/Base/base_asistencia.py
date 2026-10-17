from datetime import date
from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch


async def _get_json(env, path: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/{path}",
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


async def get_all_asistencias(env):
    return await _get_json(env, "asistencia?select=*")


async def get_historial_asistencia_socio(
    env,
    id_socio: int,
    desde: date | None = None,
    hasta: date | None = None,
):
    socios = await _get_json(env, f"socio?id_socio=eq.{id_socio}&select=id_socio")
    if not socios:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    filtros = f"id_socio=eq.{id_socio}"
    if desde:
        filtros += f"&fecha=gte.{desde.isoformat()}"
    if hasta:
        filtros += f"&fecha=lte.{hasta.isoformat()}"

    return await _get_json(
        env,
        f"asistencia?{filtros}"
        "&select=id_asistencia,id_horario,fecha,fecha_hora,"
        "clase_horario(dia_semana,hora_inicio,hora_fin,clase(id_clase,nombre,deporte(nombre)))"
        "&order=fecha_hora.desc",
    )
