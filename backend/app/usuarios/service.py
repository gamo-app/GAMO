import logging
from datetime import date
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from supabase import Client

logger = logging.getLogger(__name__)

ROLES_SEDE_OBLIGATORIA = {"socio"}
ROLES_CON_DEPORTE = {"representante"}
TABLAS_ROL = ("socio", "profesor", "representante")


class UsuarioBase(BaseModel):
    """Esquema base con los atributos comunes a todos los usuarios."""
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, description="Nombre de la persona")
    apellido: str = Field(min_length=1, description="Apellido de la persona")
    dni: str = Field(min_length=1, description="Número de documento")
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = Field(
        default=None,
        description="Fecha de nacimiento en formato YYYY-MM-DD (ej: 1998-05-20)",
    )
    email: EmailStr
    password: str = Field(min_length=6, description="Contraseña de al menos 6 caracteres")
    rol: str = Field(description="Rol asignado al usuario")
    id_sede: Optional[int] = Field(
        default=None,
        description="ID de la sede (obligatorio para socio, opcional para otros)",
    )

    @field_validator("id_sede", mode="before")
    @classmethod
    def normalizar_sede(cls, v):
        if v is None or v == "" or (isinstance(v, int) and v <= 0):
            return None
        return v

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, v: EmailStr) -> str:
        return v.lower()


def _rollback(supabase: Client, user_id: Optional[str], id_persona: Optional[int]):
    """Deshace los registros creados en orden inverso si ocurre algún fallo."""
    try:
        if id_persona is not None:
            for tabla in (*TABLAS_ROL, "usuario"):
                supabase.table(tabla).delete().eq("id_persona", id_persona).execute()
            supabase.table("persona").delete().eq("id_persona", id_persona).execute()
        if user_id:
            supabase.auth.admin.delete_user(user_id)
    except Exception:
        logger.exception("Error durante rollback (id_persona=%s, user_id=%s)", id_persona, user_id)


def _existe_activo(supabase: Client, tabla: str, columna: str, valor) -> bool:
    """Verifica si un registro existe y se encuentra activo en la base de datos."""
    res = supabase.table(tabla).select(columna).eq(columna, valor).eq("activo", True).execute()
    return bool(res.data)


def crear_usuario_completo(supabase: Client, datos: UsuarioBase) -> dict:
    """Lógica unificada de negocio y persistencia en Supabase."""
    rol = datos.rol
    id_deporte = getattr(datos, "id_deporte", None) if rol in ROLES_CON_DEPORTE else None

    # 1. Validaciones de negocio específicas por rol
    if rol in ROLES_SEDE_OBLIGATORIA and datos.id_sede is None:
        raise HTTPException(
            status_code=400,
            detail="El socio debe tener una sede válida asignada (id_sede mayor a 0).",
        )
    if rol in ROLES_CON_DEPORTE and id_deporte is None:
        raise HTTPException(
            status_code=400,
            detail="El representante debe tener un deporte asignado (id_deporte mayor a 0).",
        )

    # 2. Verificar existencia del grupo en la base
    grupo = supabase.table("grupo_usuario").select("id_grupo").ilike("nombre", f"%{rol}%").execute()
    if not grupo.data:
        raise HTTPException(
            status_code=400,
            detail=f"No existe el grupo para el rol '{rol}' en la tabla grupo_usuario.",
        )
    id_grupo = grupo.data[0]["id_grupo"]

    # 3. Validar claves foráneas activas
    if id_deporte is not None and not _existe_activo(supabase, "deporte", "id_deporte", id_deporte):
        raise HTTPException(
            status_code=400,
            detail=f"El deporte con ID {id_deporte} no existe o está inactivo.",
        )
    if datos.id_sede is not None and not _existe_activo(supabase, "sede", "id_sede", datos.id_sede):
        raise HTTPException(
            status_code=400,
            detail=f"La sede con ID {datos.id_sede} no existe o está inactiva.",
        )

    # 4. Validar unicidad previa
    if supabase.table("persona").select("id_persona").eq("dni", datos.dni).execute().data:
        raise HTTPException(status_code=409, detail="Ya existe una persona registrada con ese DNI.")
    if supabase.table("usuario").select("id_usuario").eq("email", datos.email).execute().data:
        raise HTTPException(status_code=409, detail="Ya existe un usuario registrado con ese email.")

    user_id = None
    id_persona = None
    try:
        # A. Crear usuario en el servicio Auth de Supabase
        auth_response = supabase.auth.admin.create_user({
            "email": datos.email,
            "password": datos.password,
            "email_confirm": True,
        })
        user_id = auth_response.user.id

        # B. Registrar en public.persona
        persona_res = supabase.table("persona").insert({
            "nombre": datos.nombre,
            "apellido": datos.apellido,
            "dni": datos.dni,
            "telefono": datos.telefono,
            "fecha_nacimiento": datos.fecha_nacimiento.isoformat() if datos.fecha_nacimiento else None,
        }).execute()
        id_persona = persona_res.data[0]["id_persona"]

        # C. Registrar en public.usuario
        supabase.table("usuario").insert({
            "id_usuario": user_id,
            "id_persona": id_persona,
            "id_sede": datos.id_sede,
            "id_grupo": id_grupo,
            "email": datos.email,
            "nombre_usuario": f"{datos.nombre} {datos.apellido}",
        }).execute()

        # D. Registrar en la tabla correspondiente al rol
        payload = {"id_persona": id_persona}
        if rol == "socio":
            payload["id_sede"] = datos.id_sede
        elif rol == "representante":
            payload["id_deporte"] = id_deporte

        supabase.table(rol).insert(payload).execute()

        return {
            "mensaje": f"{rol.capitalize()} registrado exitosamente en el sistema.",
            "id_usuario": user_id,
            "id_persona": id_persona,
            "rol": rol,
        }

    except HTTPException:
        _rollback(supabase, user_id, id_persona)
        raise
    except Exception as e:
        _rollback(supabase, user_id, id_persona)
        logger.exception("Error al registrar el usuario")

        texto = str(e).lower()
        if "duplicate key" in texto or "23505" in texto or "already" in texto:
            raise HTTPException(status_code=409, detail="El DNI o el email ya están registrados.")

        raise HTTPException(
            status_code=500,
            detail="Error al registrar el usuario en la base de datos.",
        )