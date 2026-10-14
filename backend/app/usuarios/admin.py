from typing import Literal, Optional
from fastapi import APIRouter, Depends, status
from pydantic import Field, field_validator
from supabase import Client
from app.database import get_supabase
from .service import UsuarioBase, crear_usuario_completo

router = APIRouter()

class UsuarioCreateAdmin(UsuarioBase):
    rol: Literal["socio", "profesor", "representante"]
    id_sede: int = Field(
        gt=0,
        description="ID de la sede (obligatorio para cualquier alta desde Administración)",
    )
    id_deporte: Optional[int] = Field(
        default=None,
        description="ID del deporte (obligatorio para representante)",
    )

    @field_validator("id_deporte", mode="before")
    @classmethod
    def normalizar_deporte(cls, v):
        if v is None or v == "" or (isinstance(v, int) and v <= 0):
            return None
        return v


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (Administrador)",
    description="Permite registrar usuarios con rol socio, profesor o representante asignando obligatoriamente una sede.",
)
def crear_usuario(datos: UsuarioCreateAdmin, supabase: Client = Depends(get_supabase)):
    return crear_usuario_completo(supabase, datos)