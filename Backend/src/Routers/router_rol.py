from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from Base import base_rol as rol
from Routers import router_exportacion
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
    uuid_clase: UUID | None = Query(
        None,
        description="Opcional: filtrar socios por UUID de clase",
    ),
    id_clase: UUID | None = Query(
        None,
        include_in_schema=False,
    ),
    access_token: str = Depends(validar_sesion),
):
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
        uuid_clase=uuid_clase or id_clase,
    )


# La exportación a XLSX/PDF está en router_exportacion.py. Se publica acá para que las URLs
# sigan siendo /rol/exportar/xlsx y /rol/exportar/pdf (con la sesión que ya exige /rol).
router.include_router(router_exportacion.router, prefix="/exportar")