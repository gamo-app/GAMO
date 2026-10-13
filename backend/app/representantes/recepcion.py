from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, logger, status
from pydantic import BaseModel, EmailStr, Field
from supabase import Client
from app.database import get_supabase
from datetime import date  
import logging


logger = logging.getLogger(__name__)

router = APIRouter()

# Esquema de validación para los datos recibidos
class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = Field(
        default=None, 
        description="Fecha de nacimiento en formato YYYY-MM-DD (ej: 1998-05-20)"
    )
    email: EmailStr
    password: str = Field(min_length=6, description="Contraseña de al menos 6 caracteres")
    rol: Literal["socio", "profesor", "representante"]
    id_sede: Optional[int] = Field(default=None, description="ID de la sede (obligatorio para socio)")
    id_deporte: Optional[int] = Field(default=None, description="ID del deporte (obligatorio para representante)")


def _rollback(supabase: Client, user_id, id_persona):
    """Deshace lo creado en orden inverso si ocurre algún fallo."""
    try:
        if id_persona is not None:
            for tabla in ("socio", "profesor", "representante", "usuario"):
                supabase.table(tabla).delete().eq("id_persona", id_persona).execute()
            supabase.table("persona").delete().eq("id_persona", id_persona).execute()
        if user_id:
            supabase.auth.admin.delete_user(user_id)
    except Exception as rollback_err:
        logger.warning(f"Error durante rollback: {rollback_err}")


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, supabase: Client = Depends(get_supabase)):
    # 1. Normalización de valores por defecto (Swagger envía 0 para enteros)
    if datos.id_sede is not None and datos.id_sede <= 0:
        datos.id_sede = None
    if datos.id_deporte is not None and datos.id_deporte <= 0:
        datos.id_deporte = None

    # Si el rol no es representante, limpiamos id_deporte
    if datos.rol != "representante":
        datos.id_deporte = None

    # 2. Validaciones de negocio según el rol
    if datos.rol == "socio" and datos.id_sede is None:
        raise HTTPException(
            status_code=400,
            detail="El socio debe tener una sede válida asignada (ingrese un id_sede mayor a 0)."
        )

    if datos.rol == "representante" and datos.id_deporte is None:
        raise HTTPException(
            status_code=400,
            detail="El representante debe tener un deporte asignado (ingrese un id_deporte mayor a 0)."
        )

    
    grupo = supabase.table("grupo_usuario").select("id_grupo").ilike("nombre", f"%{datos.rol}%").execute()
    if not grupo.data:
        raise HTTPException(
            status_code=400,
            detail=f"No existe el grupo para el rol '{datos.rol}' en la tabla grupo_usuario."
        )
    id_grupo = grupo.data[0]["id_grupo"]

    
    if datos.id_deporte is not None:
        deporte = (
            supabase.table("deporte")
            .select("id_deporte")
            .eq("id_deporte", datos.id_deporte)
            .eq("activo", True)
            .execute()
        )
        if not deporte.data:
            raise HTTPException(
                status_code=400,
                detail=f"El deporte con ID {datos.id_deporte} no existe o está inactivo."
            )

    
    if datos.id_sede is not None:
        sede = (
            supabase.table("sede")
            .select("id_sede")
            .eq("id_sede", datos.id_sede)
            .eq("activo", True)
            .execute()
        )
        if not sede.data:
            raise HTTPException(
                status_code=400,
                detail=f"La sede con ID {datos.id_sede} no existe o está inactiva."
            )

    
    if supabase.table("persona").select("id_persona").eq("dni", datos.dni).execute().data:
        raise HTTPException(status_code=409, detail="Ya existe una persona con ese DNI.")
    if supabase.table("usuario").select("id_usuario").eq("email", datos.email).execute().data:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email.")

    
    user_id = None
    id_persona = None
    try:
        # A. Crear usuario en el servicio de Auth de Supabase
        auth_response = supabase.auth.admin.create_user({
            "email": datos.email,
            "password": datos.password,
            "email_confirm": True,
        })
        user_id = auth_response.user.id

        
        persona_payload = {
            "nombre": datos.nombre,
            "apellido": datos.apellido,
            "dni": datos.dni,
            "telefono": datos.telefono,
            "fecha_nacimiento": datos.fecha_nacimiento.isoformat() if datos.fecha_nacimiento else None,
        }
        persona_res = supabase.table("persona").insert(persona_payload).execute()
        id_persona = persona_res.data[0]["id_persona"]

        # C. Registrar la entidad 'usuario' en el sistema
        supabase.table("usuario").insert({
            "id_usuario": user_id,
            "id_persona": id_persona,
            "id_sede": datos.id_sede,
            "id_grupo": id_grupo,
            "email": datos.email,
            "nombre_usuario": f"{datos.nombre} {datos.apellido}",
        }).execute()

        
        if datos.rol == "socio":
            supabase.table("socio").insert({
                "id_persona": id_persona,
                "id_sede": datos.id_sede,
            }).execute()
        elif datos.rol == "profesor":
            supabase.table("profesor").insert({
                "id_persona": id_persona
            }).execute()
        else:  # representante
            supabase.table("representante").insert({
                "id_persona": id_persona,
                "id_deporte": datos.id_deporte,
            }).execute()

        return {
            "mensaje": "Usuario registrado exitosamente en el sistema",
            "id_usuario": user_id,
            "id_persona": id_persona,
            "rol": datos.rol,
        }

    except Exception as e:
        _rollback(supabase, user_id, id_persona)
        logger.exception("Error al registrar el usuario")

        texto = str(e).lower()
        if "duplicate key" in texto or "already" in texto or "23505" in texto:
            raise HTTPException(status_code=409, detail="El DNI o el email ya están registrados.")

        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar el usuario en la base de datos: {str(e)}",
        )