from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from Base import base_socio as socio

# Los datos ingresados en el formulario son enviados correctamente al backend y el sistema registra
# al nuevo socio en la base de datos.


router = APIRouter()

#get all socios 
@router.get("")
async def get_socios(request: Request):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.get_all_socios(request.scope["env"])
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
@router.get("/estado-pago/{id_ususario}")
async def get_estado_pago(request: Request, id_ususario: int):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.get_estado_pago(request.scope["env"], id_ususario)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args)

#@router.patch("/estado-pago/{id_ususario}/{estado}")

#----------------------------------------#

#get socio por estado ya no funciona porque se saco estado de socio pero es remplazar por usuario y funcionaria
@router.get("/rol/{rol}/estado/{estado}")
async def get_socios_estado(request: Request, rol: str, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.socio_all_estado(request.scope["env"], rol,  estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    

#----------------------------------------#
@router.get("/nombre-y-apellido/{nombre}/{apellido}")
async def get_socio_by_name(request: Request, nombre: str, apellido: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.get_socio_by_name(request.scope["env"], nombre, apellido)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 


#Cambiar el estado de un socio
@router.patch("/persona/{id_persona}/estado/{estado}")
async def patch_socios_estado(request: Request, id_persona: int, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.actualizar_estado_usuario_general(request.scope["env"], id_persona,  estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 


@router.get("/filtro", response_model=socio.ListadoSociosResponse)
async def get_socios_filtrados(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Cantidad de socios por página"),
    buscar: Optional[str] = Query(None, max_length=100, description="Buscar por nombre, apellido o DNI"),
):
    # TODO: falta la auth del usuario (devuelve DNI y teléfono de los socios)
    return await socio.obtener_socios_paginados(
        request.scope["env"],
        page=page,
        limit=limit,
        buscar=buscar,
    )


# Cambiar el estado de un socio (acepta PATCH y POST para compatibilidad con el front)
@router.patch("/persona/{id_persona}/estado/{estado}")
@router.post("/persona/{id_persona}/estado/{estado}")
async def patch_socios_estado(
    request: Request, id_persona: int, estado: socio.EstadoUsuario
):
    # TODO: falta la auth del usuario para saber si tiene permisos
    return await socio.actualizar_estado_usuario_general(
        request.scope["env"], id_persona, estado
    )



'''
    
@router.get("/test/{id_socio}")
async def test(request : Request, id_socio):
    try:
        id = int(id_socio)
        return await socio.get_estado_pago_socio(request.scope["env"], id_socio)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) '''