from typing import Literal
from fastapi import APIRouter, Depends, status
from supabase import Client
from app.database import get_supabase
from .service import UsuarioBase, crear_usuario_completo

router = APIRouter()


class UsuarioCreateRecepcion(UsuarioBase):
    rol: Literal["socio", "profesor"]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Recepción)",
    description="Permite registrar exclusivamente usuarios con rol socio o profesor.",
)
def crear_usuario(datos: UsuarioCreateRecepcion, supabase: Client = Depends(get_supabase)):
    return crear_usuario_completo(supabase, datos)