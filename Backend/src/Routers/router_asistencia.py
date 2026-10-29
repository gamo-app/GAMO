from datetime import date
from Base import base_asistencia as asistencia
from Base.base_login import obtener_datos_usuario
from fastapi import APIRouter, Depends, HTTPException, Request
from auth import validar_sesion
from model import AsistenciaQrEscaneo, AsistenciaRegistro
router = APIRouter()


@router.get("")
async def get_asistencia(request: Request):
    return await asistencia.get_all_asistencias(request.scope["env"])


# @router.get("/socio/{codigo_credencial}")
# async def get_historial_asistencia_socio(
#     request: Request,
#     codigo_credencial: str,
#     desde: date | None = None,
#     hasta: date | None = None,
# ):

    
#     return await asistencia.get_historial_asistencia_socio(
#         request.scope["env"], codigo_credencial, desde=desde, hasta=hasta
#     )


@router.get("/mis-asistencias")
async def get_mis_asistencias(
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    usuario_auth = request.state.usuario_auth
    return await asistencia.get_mis_asistencias(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )


@router.post("", status_code=201)
async def post_asistencia(
    datos: AsistenciaRegistro,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    usuario_auth = request.state.usuario_auth
    usuario = await obtener_datos_usuario(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="El usuario autenticado no tiene un perfil en GAMO.",
        )

    rol = usuario.get("rol") or {}
    nombre_rol = (rol.get("nombre") or "").strip().casefold()
    if nombre_rol not in {"admin", "representante", "profesor"}:
        raise HTTPException(
            status_code=403,
            detail=(
                "Solo Admin, Representante o Profesor pueden registrar "
                "asistencias manualmente."
            ),
        )

    return await asistencia.registrar_asistencia(
        request.scope["env"],
        datos,
        usuario_auth["id"],
        rol.get("nombre"),
        access_token,
    )


@router.get("/qr/sede/{id_sede}")
async def get_qr_sede(
    id_sede: int,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    usuario_auth = request.state.usuario_auth
    usuario = await obtener_datos_usuario(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="El usuario autenticado no tiene un perfil en GAMO.",
        )

    rol = usuario.get("rol") or {}
    nombre_rol = (rol.get("nombre") or "").strip().casefold()
    if nombre_rol not in {"admin", "profesor"}:
        raise HTTPException(
            status_code=403,
            detail="Solo Admin o Profesor pueden obtener el QR de una sede.",
        )

    return await asistencia.generar_qr_sede(
        request.scope["env"],
        id_sede,
        access_token,
    )


@router.post("/qr/escaneo", status_code=201)
async def post_escanear_qr_sede(
    datos: AsistenciaQrEscaneo,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    usuario_auth = request.state.usuario_auth
    usuario = await obtener_datos_usuario(
        request.scope["env"],
        usuario_auth["id"],
        access_token,
    )
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="El usuario autenticado no tiene un perfil en GAMO.",
        )

    rol = usuario.get("rol") or {}
    nombre_rol = (rol.get("nombre") or "").strip().casefold()
    if nombre_rol != "socio":
        raise HTTPException(
            status_code=403,
            detail="Solo un socio puede registrar asistencia escaneando el QR de sede.",
        )

    return await asistencia.registrar_asistencia_qr(
        request.scope["env"],
        datos,
        usuario_auth["id"],
        access_token,
    )
