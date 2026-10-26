from fastapi import APIRouter, Depends, HTTPException, Request, status
from model import (
    SocioAltaCreate,
    UsuarioCreate,
    UsuarioCreateAdmin,
    UsuarioCreateRecepcion,
)
from Base import base_usuario as usuario
from Base.base_alta_usuario import crear_usuario_completo
from auth import validar_sesion

router = APIRouter()


@router.post("/socio", status_code=status.HTTP_201_CREATED)
async def post_usuario_socio(
    datos: SocioAltaCreate,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await usuario.create_socio_alta(
        request.scope["env"],
        datos,
    )


@router.get("/me/{id_usuario}")
async def get_mi_sesion(
    request: Request,
    id_usuario: str,
    access_token: str = Depends(validar_sesion),
):
    return await usuario.get_sesion(
        request.scope["env"],
        id_usuario,
        access_token,
    )


@router.get("")
async def get_usuarios(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    try:
        return await usuario.get_all_usuarios(request.scope["env"], access_token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/ConValidacion", status_code=status.HTTP_201_CREATED)
async def create_usuario_con_validacion(
    datos: UsuarioCreate,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )


@router.post("/SinValidacion", status_code=status.HTTP_201_CREATED)
async def create_usuario_sin_validacion(
    datos: UsuarioCreate,
    request: Request,
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )


@router.post(
    "/admin",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Administrador)",
)
async def crear_usuario_admin(
    datos: UsuarioCreateAdmin,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await crear_usuario_completo(request.scope["env"], datos)


@router.post(
    "/recepcion",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Recepción)",
)
async def crear_usuario_recepcion(
    datos: UsuarioCreateRecepcion,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await crear_usuario_completo(request.scope["env"], datos)