from fastapi import Depends, HTTPException, Request, APIRouter
from model import UsuarioCreate
from Base import base_usuario as usuario
from Base.base_login import obtener_datos_usuario
from auth import validar_acceso_administrativo, validar_sesion

router = APIRouter()

@router.get("/me/{id_usuario}")
async def get_mi_sesion(
    request: Request,
    id_usuario: str,
    access_token: str = Depends(validar_sesion),
):
    usuario_auth = request.state.usuario_auth
    if id_usuario != usuario_auth["id"]:
        raise HTTPException(
            status_code=403,
            detail="No tenés permiso para consultar el perfil de otro usuario.",
        )

    perfil = await obtener_datos_usuario(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )
    if not perfil:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el perfil del usuario autenticado.",
        )
    return perfil


@router.get("")
async def get_usuarios(
    request: Request,
    access_token: str = Depends(validar_acceso_administrativo),
):
    return await usuario.get_all_usuarios(request.scope["env"], access_token)

@router.post("/ConValidacion", status_code=201)
@router.post("/SinValidacion", status_code=201)
async def crear_usuario(
    datos: UsuarioCreate,
    request: Request,
    access_token: str = Depends(validar_acceso_administrativo),
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )

