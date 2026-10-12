from fastapi import HTTPException, Request, APIRouter
from model import SocioAltaCreate
from model import UsuarioCreate, LoginData
from Base import base_usuario as usuario

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
async def create_usuario(usuario: UsuarioCreate, request: Request):
    try:
        usuario_dict = usuario.model_dump(mode="json")
        
        password = usuario_dict.pop("password")
        
        return await usuario.create_user_with_auth(request.scope["env"], usuario_dict, password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/login")
async def router_login(login: LoginData, request: Request):
    try:
        return await login(request.scope["env"], login.email, login.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=700, detail=str(e))





    





