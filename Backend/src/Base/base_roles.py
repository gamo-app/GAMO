import math
import re
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from supabase import create_async_client
from supabase_config import get_supabase_config


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


def _terminos_de_busqueda(buscar: Optional[str]) -> List[str]:
    if not buscar or not buscar.strip():
        return []
    limpio = re.sub(r'[,()%*_"\\]', " ", buscar.strip())
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
    return next((m for m in lista if m.get("estado") == "activa"), lista[0])


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


# =========================================================
# FUNCIÓN PRINCIPAL DE BÚSQUEDA Y FILTRADO POR ROLES
# =========================================================

async def filtrar_usuarios_por_rol(
    env,
    access_token: Optional[str],
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

    rol_norm = _normalizar_rol(rol)
    estado_norm = _normalizar_estado(estado)

    # Si piden "Morosos" para un rol distinto de socio, devolver lista vacía
    if estado_norm == "moroso" and rol_norm in ("profesor", "representante", "administrador"):
        return {
            "datos": [],
            "paginacion": {
                "paginaActual": page,
                "elementosPorPagina": limit,
                "totalPaginas": 0,
                "totalRegistros": 0,
            },
        }

    # Activar !inner dinámicamente cuando se filtra por tablas anidadas
    join_socio = "socio!inner" if (estado_norm == "moroso" or id_plan) else "socio"
    join_membresia = "membresia!inner" if id_plan else "membresia"
    join_cuota = "cuota!inner" if estado_norm == "moroso" else "cuota"
    join_representante = "representante!inner" if id_deporte else "representante"

    select_query = (
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

    inicio = (page - 1) * limit
    fin = inicio + limit - 1

    try:
        supabase = await create_async_client(url, key)
        #supabase.postgrest.auth(access_token)

        query = supabase.table("usuario").select(select_query, count="exact")

        
        if rol_norm:
            query = query.ilike("grupo_usuario.nombre", f"{rol_norm}%")

        # 2. Filtro por Estado (activo, inactivo o moroso)
        if estado_norm in ("activo", "inactivo"):
            query = query.eq("estado", estado_norm)
        elif estado_norm == "moroso":
            query = query.ilike("grupo_usuario.nombre", "socio%")
            query = query.eq("persona.socio.cuota.estado", "vencida")

        
        if id_sede is not None and id_sede > 0:
            query = query.eq("id_sede", id_sede)

       
        if id_plan is not None and id_plan > 0:
            query = query.eq("persona.socio.membresia.id_plan", id_plan)
            query = query.eq("persona.socio.membresia.estado", "activa")
        
        if id_deporte is not None and id_deporte > 0:
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
                if solo_digitos.isdigit():
                    condiciones.append(f"dni.ilike.%{solo_digitos}%")

                query = _aplicar_or_tabla(query, ",".join(condiciones), "persona")

        # 6. Ordenamiento y Paginación
        response = (
            await query
            .order("id_persona", desc=False)
            .range(inicio, fin)
            .execute()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al filtrar los usuarios por rol: {str(e)}",
        )

    filas = response.data or []
    total_registros = response.count or 0
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