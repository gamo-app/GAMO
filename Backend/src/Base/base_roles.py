import logging
import math
import re
import unicodedata
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from postgrest import APIError
from pydantic import BaseModel
from supabase import create_async_client

from Base import base_login
from supabase_config import get_supabase, get_supabase_config

logger = logging.getLogger(__name__)


# =========================================================
# MODELOS DE RESPUESTA PARA EL FILTRO MULTIRROL
# =========================================================

class UsuarioFiltradoResponse(BaseModel):
    # Datos generales (usuario + persona + grupo_usuario + sede)
    id_usuario: str
    id_persona: int
    nombre: str
    apellido: str
    dni: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    email: str
    nombre_usuario: Optional[str] = None
    rol: str
    estado: str
    id_sede: Optional[int] = None
    sede: Optional[str] = None

    # Datos específicos de Socio
    id_socio: Optional[int] = None
    codigo_credencial: Optional[str] = None
    fecha_alta: Optional[str] = None
    id_plan: Optional[int] = None
    plan: Optional[str] = None
    estado_membresia: Optional[str] = None
    fecha_vencimiento_cuota: Optional[str] = None
    estado_cuota: Optional[str] = None
    monto_cuota: Optional[float] = None
    es_moroso: bool = False

    # Datos específicos de Profesor
    id_profesor: Optional[int] = None

    # Datos específicos de Representante
    id_representante: Optional[int] = None
    id_deporte: Optional[int] = None
    deporte: Optional[str] = None


class PaginacionUsuariosInfo(BaseModel):
    paginaActual: int
    elementosPorPagina: int
    totalPaginas: int
    totalRegistros: int


class ListadoUsuariosResponse(BaseModel):
    datos: List[UsuarioFiltradoResponse]
    paginacion: PaginacionUsuariosInfo


# =========================================================
# CONSTANTES
# =========================================================

# Valores que acepta el filtro. Cualquier otro se rechaza con 422
# (antes un estado desconocido se ignoraba en silencio y devolvía todos los usuarios).
ROLES_VALIDOS = {"socio", "profesor", "representante", "administrador"}
ESTADOS_USUARIO = {"activo", "inactivo"}  # valores de usuario.estado; si el enum de la base crece, sumarlos acá
ESTADOS_VALIDOS = ESTADOS_USUARIO | {"moroso"}

# Grupos que pueden ver este listado (expone DNI, teléfono, email y cuotas de todos los usuarios).
# Se comparan sin mayúsculas ni acentos. Si recepción también lo necesita: {"administrador", "recepcion"}
GRUPOS_CON_ACCESO = {"administrador"}

# Orden del listado: por apellido (igual que /socio) y desempate por id_persona.
# Ordenar por una columna de persona requiere PostgREST >= 11 (Supabase lo trae).
# Si tu versión es anterior, dejá solo ["id_persona"].
ORDEN_LISTADO = ["persona(apellido)", "id_persona"]


# =========================================================
# NORMALIZADORES Y AUXILIARES
# =========================================================

MAPA_ROLES = {
    "socio": "socio",
    "socios": "socio",
    "profesor": "profesor",
    "profesores": "profesor",
    "representante": "representante",
    "representantes": "representante",
    "administrador": "administrador",
    "administradores": "administrador",
    "admin": "administrador",
}

MAPA_ESTADOS = {
    "activo": "activo",
    "activos": "activo",
    "inactivo": "inactivo",
    "inactivos": "inactivo",
    "moroso": "moroso",
    "morosos": "moroso",
}


def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _normalizar_rol(rol: Optional[str]) -> Optional[str]:
    if not rol or rol.strip().lower() in ("todos", "todas", ""):
        return None
    limpio = rol.strip().lower()
    return MAPA_ROLES.get(limpio, limpio)


def _normalizar_estado(estado: Optional[str]) -> Optional[str]:
    if not estado or estado.strip().lower() in ("todos", "todas", ""):
        return None
    limpio = estado.strip().lower()
    return MAPA_ESTADOS.get(limpio, limpio)


def _clave_grupo(nombre: Optional[str]) -> str:
    """Nombre de grupo en minúsculas, sin acentos y con plurales/alias unificados ('Administradores' -> 'administrador')."""
    limpio = _sin_acentos((nombre or "").strip().lower())
    return MAPA_ROLES.get(limpio, limpio)


def _validar_filtros(rol: Optional[str], estado: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Normaliza rol y estado y rechaza (422) los valores que no existen."""
    rol_norm = _normalizar_rol(rol)
    estado_norm = _normalizar_estado(estado)

    if rol_norm is not None and rol_norm not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail="Rol inválido. Valores permitidos: Todos, Socios, Profesores, Representantes, Administradores.",
        )
    if estado_norm is not None and estado_norm not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail="Estado inválido. Valores permitidos: Todos, Activos, Inactivos, Morosos.",
        )
    return rol_norm, estado_norm


def _terminos_de_busqueda(buscar: Optional[str]) -> List[str]:
    if not buscar or not buscar.strip():
        return []
    # Solo se sacan los caracteres que rompen la sintaxis de PostgREST.
    # El "_" se deja: es común en emails (en ilike solo es un comodín de un carácter, no es un riesgo).
    limpio = re.sub(r'[,()%*"\\]', " ", buscar.strip())
    return [t for t in limpio.split() if t][:5]


def _aplicar_or_tabla(query, condiciones: str, tabla: str):
    """Aplica .or_() sobre una tabla relacionada soportando cualquier versión de postgrest-py."""
    try:
        return query.or_(condiciones, reference_table=tabla)
    except TypeError:
        return query.or_(condiciones, foreign_table=tabla)


def _primero(valor: Any) -> Dict[str, Any]:
    if isinstance(valor, list):
        return valor[0] if valor else {}
    return valor or {}


def _lista(valor: Any) -> List[Dict[str, Any]]:
    if not valor:
        return []
    return valor if isinstance(valor, list) else [valor]


def _ultima_cuota(cuotas: Any) -> Dict[str, Any]:
    lista = _lista(cuotas)
    if not lista:
        return {}
    return max(lista, key=lambda c: c.get("fecha_vencimiento") or "")


def _membresia_principal(membresias: Any) -> Dict[str, Any]:
    lista = _lista(membresias)
    if not lista:
        return {}
    activa = next((m for m in lista if m.get("estado") == "activa"), None)
    # Sin membresía activa: la más reciente (mayor id), no una cualquiera
    return activa or max(lista, key=lambda m: m.get("id_membresia") or 0)


def _armar_usuario_filtrado(fila: Dict[str, Any]) -> Dict[str, Any]:
    persona = _primero(fila.get("persona"))
    grupo = _primero(fila.get("grupo_usuario"))
    sede_usuario = _primero(fila.get("sede"))

    socio = _primero(persona.get("socio"))
    profesor = _primero(persona.get("profesor"))
    representante = _primero(persona.get("representante"))

    # Resolver sede priorizando usuario.sede y usando la sede del rol como respaldo
    sede_rol = (
        _primero(socio.get("sede"))
        or _primero(profesor.get("sede"))
        or _primero(representante.get("sede"))
    )
    id_sede_final = fila.get("id_sede") or sede_rol.get("id_sede")
    nombre_sede_final = sede_usuario.get("nombre") or sede_rol.get("nombre")

    # Datos de socio (membresía y cuota)
    membresia = _membresia_principal(socio.get("membresia"))
    plan = _primero(membresia.get("plan_membresia"))

    cuotas_socio = _lista(socio.get("cuota"))
    cuota = _ultima_cuota(cuotas_socio)
    estado_cuota = cuota.get("estado") or ("sin_cuota" if socio else None)
    tiene_cuota_vencida = any(c.get("estado") == "vencida" for c in cuotas_socio)

    # Datos de representante (deporte)
    deporte = _primero(representante.get("deporte"))

    return {
        "id_usuario": str(fila.get("id_usuario")),
        "id_persona": persona.get("id_persona") or fila.get("id_persona"),
        "nombre": persona.get("nombre") or "",
        "apellido": persona.get("apellido") or "",
        "dni": persona.get("dni"),
        "telefono": persona.get("telefono"),
        "fecha_nacimiento": str(persona["fecha_nacimiento"]) if persona.get("fecha_nacimiento") else None,
        "email": fila.get("email") or "",
        "nombre_usuario": fila.get("nombre_usuario"),
        "rol": grupo.get("nombre") or "",
        "estado": fila.get("estado") or "activo",
        "id_sede": id_sede_final,
        "sede": nombre_sede_final,
        # Socio
        "id_socio": socio.get("id_socio"),
        "codigo_credencial": str(socio["codigo_credencial"]) if socio.get("codigo_credencial") else None,
        "fecha_alta": str(socio["fecha_alta"]) if socio.get("fecha_alta") else None,
        "id_plan": plan.get("id_plan"),
        "plan": plan.get("nombre"),
        "estado_membresia": membresia.get("estado"),
        "fecha_vencimiento_cuota": str(cuota["fecha_vencimiento"]) if cuota.get("fecha_vencimiento") else None,
        "estado_cuota": estado_cuota,
        "monto_cuota": float(cuota["monto"]) if cuota.get("monto") is not None else None,
        "es_moroso": tiene_cuota_vencida,
        # Profesor
        "id_profesor": profesor.get("id_profesor"),
        # Representante
        "id_representante": representante.get("id_representante"),
        "id_deporte": deporte.get("id_deporte"),
        "deporte": deporte.get("nombre"),
    }


def _respuesta_vacia(page: int, limit: int) -> dict:
    return {
        "datos": [],
        "paginacion": {
            "paginaActual": page,
            "elementosPorPagina": limit,
            "totalPaginas": 0,
            "totalRegistros": 0,
        },
    }


def _error_http(e: APIError) -> HTTPException:
    """Convierte un error de PostgREST en una respuesta HTTP sin exponer el detalle interno al cliente."""
    codigo = getattr(e, "code", None)
    logger.error("Error de PostgREST al filtrar usuarios (code=%s): %s", codigo, e)

    if codigo in ("PGRST301", "PGRST303"):  # JWT inválido o vencido
        return HTTPException(status_code=401, detail="La sesión expiró. Iniciá sesión nuevamente.")
    if codigo == "42501":  # permiso denegado en la base
        return HTTPException(status_code=403, detail="No tenés permisos para ver este listado.")
    return HTTPException(status_code=502, detail="Error al consultar los usuarios.")


# =========================================================
# CONSTRUCCIÓN DE LA CONSULTA
# =========================================================

def _construir_select(
    estado_norm: Optional[str],
    id_plan: Optional[int],
    id_deporte: Optional[int],
) -> str:
    # Activar !inner dinámicamente cuando se filtra por tablas anidadas
    join_socio = "socio!inner" if (estado_norm == "moroso" or id_plan) else "socio"
    join_membresia = "membresia!inner" if id_plan else "membresia"
    join_cuota = "cuota!inner" if estado_norm == "moroso" else "cuota"
    join_representante = "representante!inner" if id_deporte else "representante"

    return (
        "id_usuario,id_persona,id_sede,id_grupo,email,estado,nombre_usuario,"
        "grupo_usuario!inner(id_grupo,nombre),"
        "sede(id_sede,nombre),"
        "persona!inner("
            "id_persona,nombre,apellido,dni,telefono,fecha_nacimiento,"
            f"{join_socio}("
                "id_socio,fecha_alta,codigo_credencial,"
                "sede(id_sede,nombre),"
                f"{join_membresia}(id_membresia,estado,id_plan,plan_membresia(id_plan,nombre)),"
                f"{join_cuota}(id_cuota,fecha_vencimiento,estado,monto)"
            "),"
            "profesor(id_profesor,sede(id_sede,nombre)),"
            f"{join_representante}(id_representante,id_deporte,deporte(id_deporte,nombre),sede(id_sede,nombre))"
        ")"
    )


def _aplicar_filtros(
    query,
    rol_norm: Optional[str],
    estado_norm: Optional[str],
    id_sede: Optional[int],
    id_plan: Optional[int],
    id_deporte: Optional[int],
    buscar: Optional[str],
):
    #  Filtro por Rol
    if rol_norm:
        query = query.ilike("grupo_usuario.nombre", f"{rol_norm}%")

    #  Filtro por Estado (activo, inactivo o moroso)
    if estado_norm in ESTADOS_USUARIO:
        query = query.eq("estado", estado_norm)
    elif estado_norm == "moroso":
        if rol_norm != "socio":
            query = query.ilike("grupo_usuario.nombre", "socio%")
        query = query.eq("persona.socio.cuota.estado", "vencida")

    #  Filtro por Sede
    # OJO: filtra por usuario.id_sede. El listado muestra la sede del rol como respaldo cuando
    # usuario.id_sede es null, pero PostgREST no permite ese OR entre tablas: asegurate de que
    # usuario.id_sede esté siempre cargada (o resolvelo en SQL).
    if id_sede:
        query = query.eq("id_sede", id_sede)

    # Filtro por Plan (solo socios con membresía activa en ese plan) y por Deporte (representantes)
    if id_plan:
        query = query.eq("persona.socio.membresia.id_plan", id_plan)
        query = query.eq("persona.socio.membresia.estado", "activa")

    if id_deporte:
        query = query.eq("persona.representante.id_deporte", id_deporte)

    # 5. Buscador por nombre, apellido, DNI, teléfono o email
    for termino in _terminos_de_busqueda(buscar):
        if "@" in termino:
            query = query.ilike("email", f"%{termino}%")
        else:
            condiciones = [
                f"nombre.ilike.%{termino}%",
                f"apellido.ilike.%{termino}%",
                f"telefono.ilike.%{termino}%",
            ]
            solo_digitos = termino.replace(".", "").replace("-", "")
            if solo_digitos.isascii() and solo_digitos.isdigit():
                condiciones.append(f"dni.ilike.%{solo_digitos}%")

            query = _aplicar_or_tabla(query, ",".join(condiciones), "persona")

    return query


def _construir_query(
    supabase,
    select_query: str,
    rol_norm: Optional[str],
    estado_norm: Optional[str],
    id_sede: Optional[int],
    id_plan: Optional[int],
    id_deporte: Optional[int],
    buscar: Optional[str],
):
    query = supabase.table("usuario").select(select_query, count="exact")
    query = _aplicar_filtros(query, rol_norm, estado_norm, id_sede, id_plan, id_deporte, buscar)

    # 6. Ordenamiento
    for columna in ORDEN_LISTADO:
        query = query.order(columna)
    return query


async def _ejecutar_pagina(armar_query, inicio: int, fin: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Ejecuta la consulta paginada. Si la página pedida no existe (por ejemplo, el front cambió un
    filtro estando en la página 3) devuelve [] con el total real en vez de un error.
    """
    try:
        response = await armar_query().range(inicio, fin).execute()
        return response.data or [], response.count or 0
    except APIError as e:
        # PGRST103 = rango fuera de límites (HTTP 416). Misma idea que el 416 de base_socio.
        if getattr(e, "code", None) != "PGRST103":
            raise
        # Query nueva: reutilizar la anterior podría duplicar los parámetros offset/limit.
        conteo = await armar_query().range(0, 0).execute()
        return [], conteo.count or 0


# =========================================================
# FUNCIÓN PRINCIPAL DE BÚSQUEDA Y FILTRADO POR ROLES
# =========================================================

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
) -> dict:
    url, key = get_supabase_config(env)

    rol_norm, estado_norm = _validar_filtros(rol, estado)

    # Un id <= 0 significa "sin filtro" (el front puede mandar 0 para "Todas")
    id_sede = id_sede if id_sede and id_sede > 0 else None
    id_plan = id_plan if id_plan and id_plan > 0 else None
    id_deporte = id_deporte if id_deporte and id_deporte > 0 else None

    # Si piden "Morosos" para un rol distinto de socio, devolver lista vacía
    if estado_norm == "moroso" and rol_norm in ("profesor", "representante", "administrador"):
        return _respuesta_vacia(page, limit)

    select_query = _construir_select(estado_norm, id_plan, id_deporte)

    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    try:
        supabase = await create_async_client(url, key)
        supabase.postgrest.auth(access_token)

        armar_query = partial(
            _construir_query,
            supabase, select_query, rol_norm, estado_norm, id_sede, id_plan, id_deporte, buscar,
        )
        filas, total_registros = await _ejecutar_pagina(armar_query, inicio, fin)

    except HTTPException:
        raise
    except APIError as e:
        raise _error_http(e)
    except Exception:
        # El detalle va al log, no al cliente (antes se devolvía str(e) con nombres de tablas y columnas)
        logger.exception("Error inesperado al filtrar usuarios por rol")
        raise HTTPException(status_code=500, detail="Error interno al filtrar los usuarios.")

    total_paginas = math.ceil(total_registros / limit) if total_registros else 0

    return {
        "datos": [_armar_usuario_filtrado(fila) for fila in filas],
        "paginacion": {
            "paginaActual": page,
            "elementosPorPagina": limit,
            "totalPaginas": total_paginas,
            "totalRegistros": total_registros,
        },
    }


# =========================================================
# CONTROL DE ACCESO AL LISTADO
# =========================================================

async def validar_acceso_listado(env, access_token: str) -> None:
    """
    Verifica que quien consulta pertenezca a un grupo de GRUPOS_CON_ACCESO.
    Se suma a RLS: el backend no debería depender solo de las policies para proteger datos personales.
    """
    url, key = get_supabase_config(env)

    usuario_auth = await base_login.obtener_usuario_auth(url, key, access_token)
    if not usuario_auth or not usuario_auth.get("id"):
        raise HTTPException(status_code=401, detail="La sesión expiró. Iniciá sesión nuevamente.")

    try:
        respuesta = (
            get_supabase(env)
            .table("usuario")
            .select("grupo_usuario(nombre)")
            .eq("id_usuario", usuario_auth["id"])
            .limit(1)
            .execute()
        )
        grupo = _primero(_primero(respuesta.data).get("grupo_usuario")).get("nombre")
    except Exception:
        logger.exception("No se pudo verificar el grupo del usuario %s", usuario_auth.get("id"))
        raise HTTPException(status_code=502, detail="No se pudo verificar los permisos del usuario.")

    if _clave_grupo(grupo) not in GRUPOS_CON_ACCESO:
        raise HTTPException(
            status_code=403,
            detail="No tenés permisos para ver el listado de usuarios.",
        )