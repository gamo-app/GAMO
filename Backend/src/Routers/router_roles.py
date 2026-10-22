from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from auth import validar_sesion
from Base import base_roles as roles
from model import ListadoUsuariosResponse

router = APIRouter()

RESPUESTAS = {
    401: {"description": "Sesión inválida o vencida"},
    403: {"description": "El usuario no tiene permisos para ver este listado"},
    422: {"description": "Parámetros de filtrado inválidos"},
}


async def solo_staff(request: Request, access_token: str = Depends(validar_sesion)) -> str:
    await roles.validar_acceso_listado(request.scope.get("env"), access_token)
    return access_token


@router.get("", response_model=ListadoUsuariosResponse, responses=RESPUESTAS, summary="Listar y filtrar usuarios por rol")
@router.get("/filtro", response_model=ListadoUsuariosResponse, responses=RESPUESTAS, summary="Filtrar usuarios multirrol")
async def get_usuarios_filtrados_por_rol(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Cantidad de registros por página"),
    rol: Optional[str] = Query(None, description="Rol: Socios, Profesores, Representantes, Administradores (o Todos)"),
    estado: Optional[str] = Query(None, description="Estado: Todos, Activos, Inactivos, Suspendidos, Morosos"),
    id_sede: Optional[int] = Query(None, description="ID de la sede (omitir, o 0, para Todas las sedes)"),
    buscar: Optional[str] = Query(None, max_length=100, description="Buscar por nombre, apellido, DNI, teléfono o email"),
    id_plan: Optional[int] = Query(None, description="Opcional: filtrar socios por ID de plan de membresía (0 = sin filtro)"),
    id_deporte: Optional[int] = Query(None, description="Opcional: filtrar representantes por ID de deporte (0 = sin filtro)"),
    access_token: str = Depends(solo_staff),
):
    return await roles.filtrar_usuarios_por_rol(
        env=request.scope.get("env"),
        access_token=access_token,
        page=page,
        limit=limit,
        rol=rol,
        estado=estado,
        id_sede=id_sede,
        buscar=buscar,
        id_plan=id_plan,
        id_deporte=id_deporte,
    )