import logging
import math
import re
import unicodedata
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from postgrest import APIError
from supabase import create_async_client

from Base import base_login
from model import (
    EstadoUsuarioEnum,
    ListadoUsuariosResponse,
    PaginacionUsuariosInfo,
    UsuarioFiltradoResponse,
)
from supabase_config import get_supabase, get_supabase_config

logger = logging.getLogger(__name__)

ROLES_VALIDOS = {"socio", "profesor", "representante", "administrador"}
ESTADOS_USUARIO = {e.value for e in EstadoUsuarioEnum}
ESTADOS_VALIDOS = ESTADOS_USUARIO | {"moroso"}
GRUPOS_CON_ACCESO = {"administrador"}
ORDEN_LISTADO = ["persona(apellido)", "id_persona"]

PATRON_LIMPIEZA = re.compile(r'[,()%*"\\]')

MAPA_ROLES = {
    "socio": "socio", "socios": "socio",
    "profesor": "profesor", "profesores": "profesor",
    "representante": "representante", "representantes": "representante",
    "administrador": "administrador", "administradores": "administrador", "admin": "administrador",
}
MAPA_ESTADOS = {
    "activo": "activo", "activos": "activo",
    "inactivo": "inactivo", "inactivos": "inactivo",
    "suspendido": "suspendido", "suspendidos": "suspendido",
    "moroso": "moroso", "morosos": "moroso",
}


def _primero(v: Any) -> Dict[str, Any]:
    return (v[0] if v else {}) if isinstance(v, list) else (v or {})


def _lista(v: Any) -> List[Dict[str, Any]]:
    return (v if isinstance(v, list) else [v]) if v else []


def _str_opt(v: Any) -> Optional[str]:
    return str(v) if v else None


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _normalizar(valor: Optional[str], mapa: Dict[str, str]) -> Optional[str]:
    limpio = _sin_acentos((valor or "").strip().lower())
    return None if limpio in ("", "todos", "todas") else mapa.get(limpio, limpio)


def _clave_grupo(nombre: Optional[str]) -> str:
    limpio = _sin_acentos((nombre or "").strip().lower())
    return MAPA_ROLES.get(limpio, limpio)


def _validar_filtros(rol: Optional[str], estado: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    rol_norm, estado_norm = _normalizar(rol, MAPA_ROLES), _normalizar(estado, MAPA_ESTADOS)
    if rol_norm is not None and rol_norm not in ROLES_VALIDOS:
        raise HTTPException(422, "Rol inválido. Valores permitidos: Todos, Socios, Profesores, Representantes, Administradores.")
    if estado_norm is not None and estado_norm not in ESTADOS_VALIDOS:
        raise HTTPException(422, "Estado inválido. Valores permitidos: Todos, Activos, Inactivos, Suspendidos, Morosos.")
    return rol_norm, estado_norm


def _armar_usuario_filtrado(fila: Dict[str, Any]) -> UsuarioFiltradoResponse:
    persona = _primero(fila.get("persona"))
    grupo = _primero(fila.get("grupo_usuario"))
    sede_usuario = _primero(fila.get("sede"))
    socio, profesor, representante = (
        _primero(persona.get("socio")),
        _primero(persona.get("profesor")),
        _primero(persona.get("representante")),
    )
    sede_rol = _primero(socio.get("sede")) or _primero(profesor.get("sede")) or _primero(representante.get("sede"))

    membresias = _lista(socio.get("membresia"))
    membresia = (
        next((m for m in membresias if m.get("estado") in ("activa", "activo")), None)
        or max(membresias, key=lambda m: m.get("id_membresia") or 0, default={})
    )
    plan = _primero(membresia.get("plan_membresia"))

    cuotas = _lista(socio.get("cuota"))
    cuota = max(cuotas, key=lambda c: c.get("fecha_vencimiento") or "", default={})
    deporte = _primero(representante.get("deporte"))

    return UsuarioFiltradoResponse(
        id_usuario=str(fila.get("id_usuario")),
        id_persona=persona.get("id_persona") or fila.get("id_persona"),
        nombre=persona.get("nombre") or "",
        apellido=persona.get("apellido") or "",
        dni=persona.get("dni"),
        telefono=persona.get("telefono"),
        fecha_nacimiento=_str_opt(persona.get("fecha_nacimiento")),
        email=fila.get("email") or "",
        nombre_usuario=fila.get("nombre_usuario"),
        rol=grupo.get("nombre") or "",
        estado=fila.get("estado") or "activo",
        id_sede=fila.get("id_sede") or sede_rol.get("id_sede"),
        sede=sede_usuario.get("nombre") or sede_rol.get("nombre"),
        id_socio=socio.get("id_socio"),
        codigo_credencial=_str_opt(socio.get("codigo_credencial")),
        fecha_alta=_str_opt(socio.get("fecha_alta")),
        id_plan=plan.get("id_plan"),
        plan=plan.get("nombre"),
        estado_membresia=membresia.get("estado"),
        fecha_vencimiento_cuota=_str_opt(cuota.get("fecha_vencimiento")),
        estado_cuota=cuota.get("estado") or ("sin_cuota" if socio else None),
        monto_cuota=float(cuota["monto"]) if cuota.get("monto") is not None else None,
        es_moroso=any(c.get("estado") == "vencida" for c in cuotas),
        id_profesor=profesor.get("id_profesor"),
        id_representante=representante.get("id_representante"),
        id_deporte=deporte.get("id_deporte"),
        deporte=deporte.get("nombre"),
    )


def _construir_query(
    supabase,
    rol_norm: Optional[str],
    estado_norm: Optional[str],
    id_sede: Optional[int],
    id_plan: Optional[int],
    id_deporte: Optional[int],
    buscar: Optional[str],
):
    j_socio = "socio!inner" if (estado_norm == "moroso" or id_plan) else "socio"
    j_memb = "membresia!inner" if id_plan else "membresia"
    j_cuota = "cuota!inner" if estado_norm == "moroso" else "cuota"
    j_rep = "representante!inner" if id_deporte else "representante"

    select_query = (
        "id_usuario,id_persona,id_sede,id_grupo,email,estado,nombre_usuario,"
        "grupo_usuario!inner(id_grupo,nombre),sede(id_sede,nombre),"
        "persona!inner(id_persona,nombre,apellido,dni,telefono,fecha_nacimiento,"
        f"{j_socio}(id_socio,fecha_alta,codigo_credencial,sede(id_sede,nombre),"
        f"{j_memb}(id_membresia,estado,id_plan,plan_membresia(id_plan,nombre)),"
        f"{j_cuota}(id_cuota,fecha_vencimiento,estado,monto)),"
        "profesor(id_profesor,sede(id_sede,nombre)),"
        f"{j_rep}(id_representante,id_deporte,deporte(id_deporte,nombre),sede(id_sede,nombre)))"
    )

    query = supabase.table("usuario").select(select_query, count="exact")

    if rol_norm:
        query = query.ilike("grupo_usuario.nombre", f"{rol_norm}%")
    if estado_norm in ESTADOS_USUARIO:
        query = query.eq("estado", estado_norm)
    elif estado_norm == "moroso":
        if rol_norm != "socio":
            query = query.ilike("grupo_usuario.nombre", "socio%")
        query = query.eq("persona.socio.cuota.estado", "vencida")

    if id_sede:
        query = query.eq("id_sede", id_sede)
    if id_plan:
        query = query.eq("persona.socio.membresia.id_plan", id_plan).eq("persona.socio.membresia.estado", "activa")
    if id_deporte:
        query = query.eq("persona.representante.id_deporte", id_deporte)

    terminos = [t for t in PATRON_LIMPIEZA.sub(" ", (buscar or "").strip()).split() if t][:5]
    for termino in terminos:
        if "@" in termino:
            query = query.ilike("email", f"%{termino}%")
        else:
            conds = [f"{col}.ilike.%{termino}%" for col in ("nombre", "apellido", "telefono")]
            digitos = termino.replace(".", "").replace("-", "")
            if digitos.isascii() and digitos.isdigit():
                conds.append(f"dni.ilike.%{digitos}%")
            try:
                query = query.or_(",".join(conds), reference_table="persona")
            except TypeError:
                query = query.or_(",".join(conds), foreign_table="persona")

    for col in ORDEN_LISTADO:
        query = query.order(col)
    return query


async def _ejecutar_pagina(armar_query, inicio: int, fin: int) -> Tuple[List[Dict[str, Any]], int]:
    try:
        res = await armar_query().range(inicio, fin).execute()
        return res.data or [], res.count or 0
    except APIError as e:
        if getattr(e, "code", None) != "PGRST103":
            raise
        conteo = await armar_query().range(0, 0).execute()
        return [], conteo.count or 0


async def filtrar_usuarios_por_rol(
    env,
    access_token: str,
    page: int = 1,
    limit: int = 10,
    rol: Optional[str] = None,
    estado: Optional[str] = None,
    id_sede: Optional[int] = None,
    buscar: Optional[str] = None,
    id_plan: Optional[int] = None,
    id_deporte: Optional[int] = None,
) -> ListadoUsuariosResponse:
    url, key = get_supabase_config(env)
    rol_norm, estado_norm = _validar_filtros(rol, estado)

    id_sede = id_sede if id_sede and id_sede > 0 else None
    id_plan = id_plan if id_plan and id_plan > 0 else None
    id_deporte = id_deporte if id_deporte and id_deporte > 0 else None

    if estado_norm == "moroso" and rol_norm in ("profesor", "representante", "administrador"):
        return ListadoUsuariosResponse(
            datos=[],
            paginacion=PaginacionUsuariosInfo(
                paginaActual=page, elementosPorPagina=limit, totalPaginas=0, totalRegistros=0
            ),
        )

    inicio = (page - 1) * limit
    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)
        armar_query = partial(_construir_query, supabase, rol_norm, estado_norm, id_sede, id_plan, id_deporte, buscar)
        filas, total = await _ejecutar_pagina(armar_query, inicio, inicio + limit - 1)
    except HTTPException:
        raise
    except APIError as e:
        codigo = getattr(e, "code", None)
        logger.error("Error de PostgREST al filtrar usuarios (code=%s): %s", codigo, e)
        if codigo in ("PGRST301", "PGRST303"):
            raise HTTPException(401, "La sesión expiró. Iniciá sesión nuevamente.")
        if codigo == "42501":
            raise HTTPException(403, "No tenés permisos para ver este listado.")
        raise HTTPException(502, "Error al consultar los usuarios.")
    except Exception:
        logger.exception("Error inesperado al filtrar usuarios por rol")
        raise HTTPException(500, "Error interno al filtrar los usuarios.")

    return ListadoUsuariosResponse(
        datos=[_armar_usuario_filtrado(f) for f in filas],
        paginacion=PaginacionUsuariosInfo(
            paginaActual=page,
            elementosPorPagina=limit,
            totalPaginas=math.ceil(total / limit) if total else 0,
            totalRegistros=total,
        ),
    )


async def validar_acceso_listado(env, access_token: str) -> None:
    url, key = get_supabase_config(env)
    usuario_auth = await base_login.obtener_usuario_auth(url, key, access_token)
    if not usuario_auth or not usuario_auth.get("id"):
        raise HTTPException(401, "La sesión expiró. Iniciá sesión nuevamente.")

    try:
        res = get_supabase(env).table("usuario").select("grupo_usuario(nombre)").eq("id_usuario", usuario_auth["id"]).limit(1).execute()
        grupo = _primero(_primero(res.data).get("grupo_usuario")).get("nombre")
    except Exception:
        logger.exception("No se pudo verificar el grupo del usuario %s", usuario_auth.get("id"))
        raise HTTPException(502, "No se pudo verificar los permisos del usuario.")

    if _clave_grupo(grupo) not in GRUPOS_CON_ACCESO:
        raise HTTPException(403, "No tenés permisos para ver el listado de usuarios.")