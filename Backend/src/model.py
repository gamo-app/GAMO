# model.py
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from enum import Enum

class EstadoUsuarioEnum(str, Enum):
    activo = "activo"
    inactivo = "inactivo"
    suspendido = "suspendido"


class EstadoSocioEnum(str, Enum):
    activo = "activo"
    inactivo = "inactivo"
    suspendido = "suspendido"


class EstadoMembresiaEnum(str, Enum):
    activo = "activo"
    vencida = "vencida"
    cancelada = "cancelada"


class EstadoDePagoEnum(str, Enum):
    pagada = "pagada"
    pendiente = "pendiente"
    vencida = "vencida"


# Datos personales
class PersonaCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str
    telefono: str
    fecha_nacimiento: date


# Datos de acceso
class UsuarioCreate(BaseModel):
    email: str
    nombre_usuario: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


# Datos propios del socio
class SocioCreate(BaseModel):
    id_persona: int
    id_sede: int
    fecha_alta: date = Field(default_factory=date.today)
    estado: EstadoSocioEnum = EstadoSocioEnum.activo
    codigo_credencial: Optional[str] = None


# Datos para registrar persona y usuario juntos
class SocioAltaCreate(BaseModel):
    persona: PersonaCreate
    usuario: UsuarioCreate
    id_plan: int = Field(gt=0)

# Modelo para representar un socio en una respuesta
class Socio(BaseModel):
    id_socio: int
    id_persona: int
    id_sede: int
    fecha_alta: date
    estado: EstadoSocioEnum
    codigo_credencial: Optional[str] = None


class MembresiaCreate(BaseModel):
    id_socio: int
    id_plan: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoMembresiaEnum = EstadoMembresiaEnum.activo


class CuotaCreate(BaseModel):
    id_socio: int
    id_membresia: int
    periodo: date
    fecha_vencimiento: date
    fecha_pago: Optional[date] = None
    estado: EstadoDePagoEnum = EstadoDePagoEnum.pendiente
    observaciones: Optional[str] = None


class PlanMembresia(BaseModel):
    id_plan: int
    nombre: str
    duracion_dias: int
    activo: bool


class PlanMembresiaPrecio(PlanMembresia):
    precio: int
    clases_semana: int
    
    
class SocioAltaCreate(BaseModel):
    persona: PersonaCreate
    usuario: UsuarioCreate
    id_plan: int = Field(gt=0)    

class LoginData(BaseModel):
    email: str
    password: str

class LoginCreate(BaseModel):
    username: str  # o email
    password: str