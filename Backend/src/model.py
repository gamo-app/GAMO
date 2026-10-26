from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
import re
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ===========================================================================
# 1. CONFIGURACIÓN Y ENUMERACIONES
# ===========================================================================

class DiaSemanaEnum(str, Enum):
    lunes = "Lunes"
    martes = "Martes"
    miercoles = "Miércoles"
    jueves = "Jueves"
    viernes = "Viernes"
    sabado = "Sábado"
    domingo = "Domingo"


class EstadoDePagoSocioEnum(str, Enum):
    al_dia = "al dia"
    pendiente = "pendiente"
    moroso = "moroso"


# ===========================================================================
# 2. ROL Y AUTENTICACIÓN
# public.rol: id_rol, nombre, permisos
# ===========================================================================

class RolBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    permisos: dict[str, Any] = Field(default_factory=dict)


class RolCreate(RolBase):
    pass


class RolResponse(RolBase):
    id_rol: int


class RolUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    permisos: dict[str, Any] | None = None


class LoginData(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)


# ===========================================================================
# 3. USUARIO: CRUD BÁSICO
# public.usuario: uuid_usuario, DNI, nombre, apellido, fecha_nacimiento, id_rol
# ===========================================================================

class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    fecha_nacimiento: date


class UsuarioCreate(UsuarioBase):
    email: str
    password: str = Field(min_length=8, max_length=128)
    DNI: int = Field(gt=0)
    id_rol: int = Field(gt=0)


class UsuarioResponse(UsuarioBase):
    uuid_usuario: UUID
    DNI: int
    id_rol: int


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    fecha_nacimiento: date | None = None
    DNI: int | None = Field(default=None, gt=0)
    id_rol: int | None = Field(default=None, gt=0)


class UsuarioSocioCreate(UsuarioBase):
    email: str
    password: str = Field(min_length=8, max_length=128)
    DNI: int = Field(gt=0)


# ===========================================================================
# 4. USUARIO: ALTA POR ROL (ADMINISTRACIÓN Y RECEPCIÓN)
# ===========================================================================

class UsuarioAltaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    nombre: str = Field(min_length=1, max_length=100, description="Nombre de la persona")
    apellido: str = Field(min_length=1, max_length=100, description="Apellido de la persona")
    dni: int = Field(alias="DNI", gt=0, description="Número de documento")
    telefono: str | None = Field(
        default=None,
        description="Teléfono (se formatea automáticamente a XX-XXXX-XXXX, ej: 11-5555-1000)",
    )
    fecha_nacimiento: date = Field(
        default_factory=date.today,
        description="Fecha de nacimiento en formato YYYY-MM-DD (ej: 1998-05-20)",
    )
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Email del usuario")
    password: str = Field(min_length=6, max_length=128, description="Contraseña de al menos 6 caracteres")
    rol: str = Field(description="Rol asignado al usuario")
    id_sede: int | None = Field(
        default=None,
        description="ID de la sede",
    )
    id_plan: int | None = Field(
        default=None,
        description="ID del plan de membresía (opcional para socios)",
    )

    @model_validator(mode="before")
    @classmethod
    def unificar_dni(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "DNI" not in data and "dni" in data:
                data["DNI"] = data["dni"]
            if "DNI" in data and isinstance(data["DNI"], str):
                limpio = re.sub(r"\D", "", data["DNI"])
                if limpio:
                    data["DNI"] = int(limpio)
        return data

    @field_validator("telefono", mode="before")
    @classmethod
    def formatear_telefono(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_str = str(v).strip()
        if not v_str:
            return None

        digitos = re.sub(r"\D", "", v_str)

        if digitos.startswith("549") and len(digitos) == 13:
            digitos = digitos[3:]
        elif digitos.startswith("54") and len(digitos) == 12:
            digitos = digitos[2:]
        elif digitos.startswith("0") and len(digitos) == 11:
            digitos = digitos[1:]

        if len(digitos) == 8:
            digitos = f"11{digitos}"

        if len(digitos) != 10:
            raise ValueError(
                "El teléfono debe contener 10 dígitos (ej: 1155551000 o 11-5555-1000)."
            )

        return f"{digitos[:2]}-{digitos[2:6]}-{digitos[6:]}"

    @field_validator("id_sede", "id_plan", mode="before")
    @classmethod
    def normalizar_ids_opcionales(cls, v):
        if v is None or v == "" or (isinstance(v, int) and v <= 0):
            return None
        return v

    @field_validator("email")
    @classmethod
    def email_minusculas(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioCreateAdmin(UsuarioAltaBase):
    rol: Literal["socio", "profesor", "representante"]
    id_sede: int | None = Field(
        default=None,
        description="ID de la sede",
    )
    id_deporte: int | None = Field(
        default=None,
        description="ID del deporte (obligatorio para representante)",
    )

    @field_validator("id_deporte", mode="before")
    @classmethod
    def normalizar_deporte(cls, v):
        if v is None or v == "" or (isinstance(v, int) and v <= 0):
            return None
        return v


class UsuarioCreateRecepcion(UsuarioAltaBase):
    rol: Literal["socio", "profesor"]
    id_sede: int | None = Field(
        default=None,
        description="ID de la sede",
    )

    telefono: str | None = Field(
        default=None,
        description="Teléfono (se formatea automáticamente a XX XXXX-XXXX, ej: 11 4960-9553)",
    )

    @field_validator("telefono", mode="before")
    @classmethod
    def formatear_telefono(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_str = str(v).strip()
        if not v_str:
            return None

        digitos = re.sub(r"\D", "", v_str)

        if digitos.startswith("549") and len(digitos) == 13:
            digitos = digitos[3:]
        elif digitos.startswith("54") and len(digitos) == 12:
            digitos = digitos[2:]
        elif digitos.startswith("0") and len(digitos) == 11:
            digitos = digitos[1:]

        if len(digitos) == 8:
            digitos = f"11{digitos}"

        if len(digitos) != 10:
            raise ValueError(
                "El teléfono debe contener 10 dígitos (ej: 11 4960-9553)."
            )

        return f"{digitos[:2]} {digitos[2:6]}-{digitos[6:]}"


# ===========================================================================
# 5. USUARIO: FILTRO Y PAGINACIÓN POR ROL
# ===========================================================================

class UsuarioFiltradoResponse(BaseModel):
    uuid_usuario: UUID
    id_usuario: str | None = None
    DNI: int
    dni: str | None = None
    nombre: str
    apellido: str
    fecha_nacimiento: date | None = None
    id_rol: int | None = None
    rol: str
    estado: str = "activo"

    # Datos de Socio y Membresía
    codigo_credencial: UUID | None = None
    id_plan: int | None = None
    plan: str | None = None
    fecha_inicio_membresia: date | None = None
    fecha_vencimiento_cuota: date | None = None
    porcentaje_descuento: int | None = None
    estado_cuota: str | None = None
    monto_cuota: Decimal | None = None
    es_moroso: bool = False

    # Datos de Profesor, Representante y Sede
    id_profesor: int | None = None
    id_representante: int | None = None
    id_deporte: int | None = None
    deporte: str | None = None
    id_sede: int | None = None
    sede: str | None = None


class PaginacionUsuariosInfo(BaseModel):
    paginaActual: int
    elementosPorPagina: int
    totalPaginas: int
    totalRegistros: int


class ListadoUsuariosResponse(BaseModel):
    datos: list[UsuarioFiltradoResponse]
    paginacion: PaginacionUsuariosInfo


# ===========================================================================
# 6. SEDE
# public.sede: id_sede, nombre, direccion, correo, telefono, activa
# ===========================================================================

class SedeBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    direccion: str = Field(min_length=1, max_length=250)
    correo: str | None = None
    telefono: str | None = None
    activa: bool = True


class SedeCreate(SedeBase):
    pass


class SedeResponse(SedeBase):
    id_sede: int


class SedeUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    direccion: str | None = Field(default=None, min_length=1, max_length=250)
    correo: str | None = None
    telefono: str | None = None
    activa: bool | None = None


# ===========================================================================
# 7. DEPORTE
# public.deporte: id_deporte, nombre, descripcion, activo
# ===========================================================================

class DeporteBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None
    activo: bool = True


class DeporteCreate(DeporteBase):
    pass


class DeporteResponse(DeporteBase):
    id_deporte: int


class DeporteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = None
    activo: bool | None = None


# ===========================================================================
# 8. PROFESOR Y REPRESENTANTE
# public.profesor: id_profesor, uuid_usuario
# public.representante: id_representante, id_profesor, id_deporte
# ===========================================================================

class ProfesorBase(BaseModel):
    uuid_usuario: UUID


class ProfesorCreate(ProfesorBase):
    pass


class ProfesorResponse(ProfesorBase):
    id_profesor: int


class RepresentanteBase(BaseModel):
    id_profesor: int = Field(gt=0)
    id_deporte: int = Field(gt=0)


class RepresentanteCreate(RepresentanteBase):
    pass


class RepresentanteResponse(RepresentanteBase):
    id_representante: int


# ===========================================================================
# 9. CLASE
# public.clase: uuid_clase, id_sede, id_deporte, id_profesor, dia_de_semana,
# hora_inicio, hora_fin, cupo
# ===========================================================================

class ClaseBase(BaseModel):
    id_sede: int = Field(gt=0)
    id_deporte: int = Field(gt=0)
    id_profesor: int = Field(gt=0)
    dia_de_semana: DiaSemanaEnum
    hora_inicio: time
    hora_fin: time
    cupo: int = Field(gt=0)

    @model_validator(mode="after")
    def validar_horario(self):
        if self.hora_inicio >= self.hora_fin:
            raise ValueError(
                "hora_inicio debe ser anterior a hora_fin. "
                "Para clases que cruzan medianoche, adaptar esta validación."
            )
        return self


class ClaseCreate(ClaseBase):
    pass


class ClaseResponse(ClaseBase):
    uuid_clase: UUID


class ClaseUpdate(BaseModel):
    id_sede: int | None = Field(default=None, gt=0)
    id_deporte: int | None = Field(default=None, gt=0)
    id_profesor: int | None = Field(default=None, gt=0)
    dia_de_semana: DiaSemanaEnum | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    cupo: int | None = Field(default=None, gt=0)


# ===========================================================================
# 10. SOCIO Y ASISTENCIA
# public.socio: codigo_credencial, uuid_usuario
# public.asistencia: id_asistencia, uuid_clase, codigo_credencial, fecha
# ===========================================================================

class SocioBase(BaseModel):
    uuid_usuario: UUID


class SocioCreate(SocioBase):
    pass


class SocioResponse(SocioBase):
    codigo_credencial: UUID


class SocioUpdate(BaseModel):
    uuid_usuario: UUID | None = None


class SocioAltaCreate(BaseModel):
    """Datos para crear una cuenta, un socio y su primera membresía."""
    usuario: UsuarioSocioCreate
    id_plan: int = Field(gt=0)
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def validar_fechas_membresia(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")
        return self


class AsistenciaBase(BaseModel):
    uuid_clase: UUID
    codigo_credencial: UUID
    fecha: date


class AsistenciaCreate(AsistenciaBase):
    pass


class AsistenciaResponse(AsistenciaBase):
    id_asistencia: int


# ===========================================================================
# 11. PLAN, MEMBRESÍA Y PAGO
# public.plan: id_plan, nombre, precio_semanal, clases_semanales
# public.membresia: id_membresia, codigo_credencial, id_plan, fecha_inicio,
#                   fecha_fin, porcentaje_descuento
# public.pago: id_pago, id_membresia, monto
# ===========================================================================

class PlanBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    precio_semanal: Decimal = Field(ge=0)
    clases_semanales: int = Field(gt=0)


class PlanCreate(PlanBase):
    pass


class PlanResponse(PlanBase):
    id_plan: int


class PlanUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    precio_semanal: Decimal | None = Field(default=None, ge=0)
    clases_semanales: int | None = Field(default=None, gt=0)


class MembresiaBase(BaseModel):
    codigo_credencial: UUID
    id_plan: int = Field(gt=0)
    fecha_inicio: date
    fecha_fin: date
    porcentaje_descuento: int = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")
        return self


class MembresiaCreate(MembresiaBase):
    pass


class MembresiaResponse(MembresiaBase):
    id_membresia: int


class MembresiaUpdate(BaseModel):
    id_plan: int | None = Field(default=None, gt=0)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    porcentaje_descuento: int | None = Field(default=None, ge=0, le=100)


class PagoBase(BaseModel):
    id_membresia: int = Field(gt=0)
    monto: Decimal = Field(gt=0)


class PagoCreate(PagoBase):
    pass


class PagoResponse(PagoBase):
    id_pago: int


# ===========================================================================
# 12. NOTIFICACIONES Y CANALES
# ===========================================================================

class CanalNotificacionBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class CanalNotificacionCreate(CanalNotificacionBase):
    pass


class CanalNotificacionResponse(CanalNotificacionBase):
    id_canal_notificacion: int


class NotificacionBase(BaseModel):
    codigo_credencial: UUID
    mensaje: str = Field(min_length=1)
    timestampt_envio: datetime
    id_canal_notificacion: int = Field(gt=0)


class NotificacionCreate(BaseModel):
    codigo_credencial: UUID
    mensaje: str = Field(min_length=1)
    id_canal_notificacion: int = Field(gt=0)
    timestampt_envio: datetime | None = None


class NotificacionResponse(NotificacionBase):
    id_notificacion: int


class CanalesSocioBase(BaseModel):
    codigo_credencial: UUID
    id_canal_notificacion: int = Field(gt=0)


class CanalesSocioCreate(CanalesSocioBase):
    pass


class CanalesSocioResponse(CanalesSocioBase):
    id_canal_socio: int