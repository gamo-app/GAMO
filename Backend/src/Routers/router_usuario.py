from fastapi import Depends, HTTPException, Request, APIRouter
from model import UsuarioCreate
from Base import base_usuario as usuario
from auth import validar_sesion

router = APIRouter()



# @router.post("/socio", status_code=201)
# async def post_usuario(datos: SocioAltaCreate, request: Request, access_token: str = Depends(validar_sesion),
#     return await usuario.create_user(request.scope["env"],datos,)
    

@router.get("/me/{id_usuario}")
async def get_mi_sesion(request: Request, id_usuario: str, access_token: str = Depends(validar_sesion),):
    return await usuario.get_sesion(
        request.scope["env"],
        id_usuario,
        access_token
    )

#get all usuarios
@router.get("")
async def get_usuarios(request: Request, access_token: str = Depends(validar_sesion),):
    try:
        return await usuario.get_all_usuarios(request.scope["env"], access_token)
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
# @router.post("/")
# async def create_usuario(usuario: UsuarioCreate,request: Request,access_token: str = Depends(validar_sesion),):
#     return await usuario.create_user(request.scope["env"],usuario,)


@router.post("/ConValidacion", status_code=201)
async def create_usuario(
    datos: UsuarioCreate,
    request: Request,
    access_token: str = Depends(validar_sesion),
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )



@router.post("/SinValidacion", status_code=201)
async def create_usuario(
    datos: UsuarioCreate,
    request: Request,
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )




    



