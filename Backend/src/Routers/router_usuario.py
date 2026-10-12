from fastapi import Request, APIRouter
from model import SocioAltaCreate


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


