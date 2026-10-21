from fastapi import HTTPException, Request, APIRouter, status, Query
from model import SocioAltaCreate, UsuarioCreate, LoginData
from Base import base_usuario as usuario
from Base.base_alta_usuario import (
    UsuarioCreateAdmin,
    UsuarioCreateRecepcion,
    crear_usuario_completo,
)

router = APIRouter()



@router.post("/socio", status_code=201)
async def post_usuario(
    datos: SocioAltaCreate,
    request: Request,
):
    return await usuario.create_user(
        request.scope["env"],
        datos,
    )
    

@router.get("/me/{id_usuario}")
async def get_mi_sesion(request: Request, id_usuario: str):
    return await usuario.get_sesion(
        request.scope["env"],
        id_usuario
    )



#get all usuarios
@router.get("")
async def get_usuarios(request: Request):
    try:
        return await usuario.get_all_usuarios(request.scope["env"])
    except  HTTPException as e:
        raise HTTPException(400, detail=e.args) 
    
    
@router.post("")
async def create_usuario(datos: UsuarioCreate, request: Request):
    try:
        usuario_dict = datos.model_dump(mode="json")
        
        password = usuario_dict.pop("password")
        
        return await usuario.create_user_with_auth(request.scope["env"], usuario_dict, password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/login")
async def router_login(login: LoginData, request: Request):
    try:
        return await usuario.login(request.scope["env"], login.email, login.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/admin",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Administrador)",
    description="Permite registrar usuarios con rol socio, profesor o representante asignando obligatoriamente una sede.",
)
async def crear_usuario_admin(datos: UsuarioCreateAdmin, request: Request):
    return await crear_usuario_completo(request.scope["env"], datos)

@router.post(
    "/recepcion",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Recepción)",
    description="Permite registrar exclusivamente usuarios con rol socio o profesor.",
)
async def crear_usuario_recepcion(datos: UsuarioCreateRecepcion, request: Request):
    return await crear_usuario_completo(request.scope["env"], datos)







    





