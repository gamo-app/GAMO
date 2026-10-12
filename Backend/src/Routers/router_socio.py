from fastapi import APIRouter, Request
from fastapi import HTTPException


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



#Cambiar el estado de un socio
@router.post("/persona/{id_persona}/estado/{estado}")
async def patch_socios_estado(request: Request, id_persona: int, estado: str):
    #falta la auth del usuario para saber si tiene permisos 
    try:
        return await socio.actualizar_estado_usuario_general(request.scope["env"], id_persona,  estado)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
