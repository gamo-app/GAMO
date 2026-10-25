from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel,  Field, model_validator


# ---------------------------------------------------------------------------
# Configuración y enumeraciones
# ---------------------------------------------------------------------------




class DiaSemanaEnum(str, Enum):
    lunes = "Lunes"
    martes = "Martes"
    miercoles = "Miércoles"
    jueves = "Jueves"
    viernes = "Viernes"
    sabado = "Sábado"
    domingo = "Domingo"


# ---------------------------------------------------------------------------
# Usuario y autenticación
# public.usuario: uuid_usuario, DNI, nombre, apellido, fecha_nacimiento, id_rol
# ---------------------------------------------------------------------------

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


class LoginData(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)


class UsuarioSocioCreate(UsuarioBase):
    email: str
    password: str = Field(min_length=8, max_length=128)
    DNI: int = Field(gt=0)


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


# ---------------------------------------------------------------------------
# Rol
# public.rol: id_rol, nombre, permisos
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Profesor
# public.profesor: id_profesor, uuid_usuario
# ---------------------------------------------------------------------------

class ProfesorBase(BaseModel):
    uuid_usuario: UUID


class ProfesorCreate(ProfesorBase):
    pass


class ProfesorResponse(ProfesorBase):
    id_profesor: int


# ---------------------------------------------------------------------------
# Deporte
# public.deporte: id_deporte, nombre, descripcion, activo
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Sede
# public.sede: id_sede, nombre, direccion, correo, telefono, activa
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Representante
# public.representante: id_representante, id_profesor, id_deporte
# ---------------------------------------------------------------------------

class RepresentanteBase(BaseModel):
    id_profesor: int = Field(gt=0)
    id_deporte: int = Field(gt=0)


class RepresentanteCreate(RepresentanteBase):
    pass


class RepresentanteResponse(RepresentanteBase):
    id_representante: int


# ---------------------------------------------------------------------------
# Clase
# public.clase: uuid_clase, id_sede, id_deporte, id_profesor, dia_de_semana, 
# hora_inicio, hora_fin, cupo
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Socio
# public.socio: codigo_credencial, uuid_usuario
# ---------------------------------------------------------------------------

class SocioBase(BaseModel):
    uuid_usuario: UUID


class SocioCreate(SocioBase):
    pass


class SocioResponse(SocioBase):
    codigo_credencial: UUID


class SocioUpdate(BaseModel):
    uuid_usuario: UUID | None = None


# ---------------------------------------------------------------------------
# Asistencia
# public.asistencia: id_asistencia, uuid_clase, codigo_credencial, fecha
# ---------------------------------------------------------------------------

class AsistenciaBase(BaseModel):
    uuid_clase: UUID
    codigo_credencial: UUID
    fecha: date


class AsistenciaCreate(AsistenciaBase):
    pass


class AsistenciaResponse(AsistenciaBase):
    id_asistencia: int


# ---------------------------------------------------------------------------
# Plan
# public.plan: id_plan, nombre, precio_semanal, clases_semanales
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Membresía
# public.membresia: id_membresia, codigo_credencial, id_plan, fecha_inicio, 
# fecha_fin, porcentaje_descuento
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Pago
# public.pago: id_pago, id_membresia, monto
# ---------------------------------------------------------------------------

class PagoBase(BaseModel):
    id_membresia: int = Field(gt=0)
    monto: Decimal = Field(gt=0)


class PagoCreate(PagoBase):
    pass


class PagoResponse(PagoBase):
    id_pago: int


# ---------------------------------------------------------------------------
# Notificaciones y Canales
# ---------------------------------------------------------------------------

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
    pass