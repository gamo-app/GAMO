from fastapi import APIRouter, Depends, HTTPException, Query, Request
from Base import base_rol as rol
from auth import validar_sesion
from model import ListadoUsuariosResponse

router = APIRouter()


@router.get("")
async def get_roles(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await rol.get_all_rol(request.scope["env"], access_token)


@router.get("/filtro", response_model=ListadoUsuariosResponse)
async def get_usuarios_filtrados_por_rol(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Cantidad de registros por página"),
    rol_filtro: str | None = Query(
        None,
        alias="rol",
        description="Rol: Socios, Profesores, Representantes, Administradores (o Todos)",
    ),
    estado: str | None = Query(
        None,
        description="Estado: Todos, Activos, Inactivos, Morosos, Pendientes, Al dia",
    ),
    id_sede: int | None = Query(
        None,
        description="ID de la sede (omitir o 0 para Todas las sedes)",
    ),
    buscar: str | None = Query(
        None,
        max_length=100,
        description="Buscar por nombre, apellido o DNI",
    ),
    id_plan: int | None = Query(
        None,
        description="Opcional: filtrar socios por ID de plan de membresía",
    ),
    id_deporte: int | None = Query(
        None,
        description="Opcional: filtrar representantes por ID de deporte",
    ),
    access_token: str = Depends(validar_sesion),
):
    try:
        return await rol.filtrar_usuarios_por_rol(
            env=request.scope["env"],
            access_token=access_token,
            page=page,
            limit=limit,
            rol=rol_filtro,
            estado=estado,
            id_sede=id_sede,
            buscar=buscar,
            id_plan=id_plan,
            id_deporte=id_deporte,
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)