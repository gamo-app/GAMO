# model.py
from datetime import date
from enum import Enum
from typing import List, Optional
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

class EstadoDePagoSocioEnum(str, Enum):
    al_dia = "al dia"
    pendiente = "pendiente"
    moroso = "moroso"

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


class UsuarioFiltradoResponse(BaseModel):
    id_usuario: str
    id_persona: int
    nombre: str
    apellido: str
    dni: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    email: str
    nombre_usuario: Optional[str] = None
    rol: str
    estado: str
    id_sede: Optional[int] = None
    sede: Optional[str] = None
    id_socio: Optional[int] = None
    codigo_credencial: Optional[str] = None
    fecha_alta: Optional[str] = None
    id_plan: Optional[int] = None
    plan: Optional[str] = None
    estado_membresia: Optional[str] = None
    fecha_vencimiento_cuota: Optional[str] = None
    estado_cuota: Optional[str] = None
    monto_cuota: Optional[float] = None
    es_moroso: bool = False
    id_profesor: Optional[int] = None
    id_representante: Optional[int] = None
    id_deporte: Optional[int] = None
    deporte: Optional[str] = None


class PaginacionUsuariosInfo(BaseModel):
    paginaActual: int
    elementosPorPagina: int
    totalPaginas: int
    totalRegistros: int


class ListadoUsuariosResponse(BaseModel):
    datos: List[UsuarioFiltradoResponse]
    paginacion: PaginacionUsuariosInfo