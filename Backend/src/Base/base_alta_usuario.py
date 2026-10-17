import hashlib
import json
import logging
import os
import re
from datetime import date, timedelta
from typing import Literal, Optional
from urllib.parse import quote

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from supabase_config import get_supabase_config
from workers import fetch

logger = logging.getLogger(__name__)

ROLES_SEDE_OBLIGATORIA = {"socio", "profesor", "representante"}
ROLES_CON_DEPORTE = {"representante"}

PK_POR_ROL = {
    "socio": "id_socio",
    "profesor": "id_profesor",
    "representante": "id_representante",
}


def _generar_hash_y_salt(password: str) -> tuple[str, str]:
    salt_bytes = os.urandom(16)
    hash_hex = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        100_000,
    ).hex()
    salt_bytea = f"\\x{salt_bytes.hex()}"
    return hash_hex, salt_bytea


class UsuarioBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, description="Nombre de la persona")
    apellido: str = Field(min_length=1, description="Apellido de la persona")
    dni: str = Field(pattern=r"^\d{7,9}$", description="Número de documento")
    telefono: Optional[str] = Field(
        default=None,
        description="Teléfono (se formatea automáticamente a XX-XXXX-XXXX, ej: 11-5555-1000)",
    )
    fecha_nacimiento: Optional[date] = Field(
        default=None,
        description="Fecha de nacimiento en formato YYYY-MM-DD (ej: 1998-05-20)",
    )
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Email del usuario")
    password: str = Field(min_length=6, description="Contraseña de al menos 6 caracteres")
    rol: str = Field(description="Rol asignado al usuario")
    id_sede: Optional[int] = Field(
        default=None,
        description="ID de la sede",
    )
    id_plan: Optional[int] = Field(
        default=None,
        description="ID del plan de membresía (opcional para socios)",
    )

    @field_validator("telefono", mode="before")
    @classmethod
    def formatear_telefono(cls, v: Optional[str]) -> Optional[str]:
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


class UsuarioCreateRecepcion(UsuarioBase):
    rol: Literal["socio", "profesor"]
    id_sede: int = Field(
        gt=0,
        description="ID de la sede (obligatorio para cualquier alta desde Recepción)",
    )


async def _rollback(
    url: str,
    headers: dict,
    user_id: Optional[str],
    id_persona: Optional[int],
    rol: str,
    id_socio: Optional[int] = None,
):
    """Deshace los registros creados en orden inverso si ocurre algún fallo."""
    try:
        if id_socio is not None:
            await fetch(f"{url}/rest/v1/cuota?id_socio=eq.{id_socio}", method="DELETE", headers=headers)
            await fetch(f"{url}/rest/v1/membresia?id_socio=eq.{id_socio}", method="DELETE", headers=headers)
        if id_persona is not None:
            await fetch(f"{url}/rest/v1/{rol}?id_persona=eq.{id_persona}", method="DELETE", headers=headers)
            await fetch(f"{url}/rest/v1/usuario?id_persona=eq.{id_persona}", method="DELETE", headers=headers)
            await fetch(f"{url}/rest/v1/persona?id_persona=eq.{id_persona}", method="DELETE", headers=headers)
        if user_id:
            await fetch(f"{url}/auth/v1/admin/users/{user_id}", method="DELETE", headers=headers)
    except Exception:
        logger.exception("Error durante rollback (id_persona=%s, user_id=%s)", id_persona, user_id)


async def _existe_activo(url: str, headers: dict, tabla: str, columna: str, valor) -> bool:
    res = await fetch(
        f"{url}/rest/v1/{tabla}?select={columna}&{columna}=eq.{valor}&activo=eq.true",
        headers=headers,
    )
    if not res.ok:
        return False
    datos = await res.json()
    return bool(datos)


async def crear_usuario_completo(env, datos: UsuarioBase) -> dict:
    url, key = get_supabase_config(env)
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    rol = datos.rol
    id_deporte = getattr(datos, "id_deporte", None) if rol in ROLES_CON_DEPORTE else None

    if rol in ROLES_SEDE_OBLIGATORIA and datos.id_sede is None:
        raise HTTPException(
            status_code=400,
            detail=f"El {rol} debe tener una sede válida asignada (id_sede mayor a 0).",
        )
    if rol in ROLES_CON_DEPORTE and id_deporte is None:
        raise HTTPException(
            status_code=400,
            detail="El representante debe tener un deporte asignado (id_deporte mayor a 0).",
        )

    # 1. Buscar id_grupo
    grupo_res = await fetch(
        f"{url}/rest/v1/grupo_usuario?select=id_grupo&nombre=ilike.{quote(rol)}",
        headers=headers,
    )
    grupo_data = await grupo_res.json() if grupo_res.ok else []
    if not grupo_data:
        raise HTTPException(
            status_code=400,
            detail=f"No existe el grupo para el rol '{rol}' en la tabla grupo_usuario.",
        )
    id_grupo = grupo_data[0]["id_grupo"]

    # 2. Verificar deporte y sede activos
    if id_deporte is not None and not await _existe_activo(url, headers, "deporte", "id_deporte", id_deporte):
        raise HTTPException(
            status_code=400,
            detail=f"El deporte con ID {id_deporte} no existe o está inactivo.",
        )
    if datos.id_sede is not None and not await _existe_activo(url, headers, "sede", "id_sede", datos.id_sede):
        raise HTTPException(
            status_code=400,
            detail=f"La sede con ID {datos.id_sede} no existe o está inactiva.",
        )

    # 3. Verificar duplicados de DNI y Email
    dni_res = await fetch(f"{url}/rest/v1/persona?select=id_persona&dni=eq.{quote(datos.dni)}", headers=headers)
    if dni_res.ok and await dni_res.json():
        raise HTTPException(status_code=409, detail="Ya existe una persona registrada con ese DNI.")

    email_res = await fetch(f"{url}/rest/v1/usuario?select=id_usuario&email=eq.{quote(datos.email)}", headers=headers)
    if email_res.ok and await email_res.json():
        raise HTTPException(status_code=409, detail="Ya existe un usuario registrado con ese email.")

    user_id = None
    id_persona = None
    id_socio = None
    try:
        # 4. Crear en Supabase Auth
        auth_res = await fetch(
            f"{url}/auth/v1/admin/users",
            method="POST",
            headers=headers,
            body=json.dumps({
                "email": datos.email,
                "password": datos.password,
                "email_confirm": True,
            }),
        )
        if not auth_res.ok:
            raise Exception(await auth_res.text())
        auth_data = await auth_res.json()
        user_id = auth_data["id"]

        # 5. Insertar en tabla persona
        persona_res = await fetch(
            f"{url}/rest/v1/persona",
            method="POST",
            headers=headers,
            body=json.dumps({
                "nombre": datos.nombre,
                "apellido": datos.apellido,
                "dni": datos.dni,
                "telefono": datos.telefono,
                "fecha_nacimiento": datos.fecha_nacimiento.isoformat() if datos.fecha_nacimiento else None,
            }),
        )
        if not persona_res.ok:
            raise Exception(await persona_res.text())
        persona_data = await persona_res.json()
        id_persona = persona_data[0]["id_persona"]

        # 6. Insertar en tabla usuario (con estado 'activo' explícito)
        hash_hex, salt_bytea = _generar_hash_y_salt(datos.password)
        usuario_res = await fetch(
            f"{url}/rest/v1/usuario",
            method="POST",
            headers=headers,
            body=json.dumps({
                "id_usuario": user_id,
                "id_persona": id_persona,
                "id_sede": datos.id_sede,
                "id_grupo": id_grupo,
                "email": datos.email,
                "nombre_usuario": f"{datos.nombre} {datos.apellido}",
                "hash": hash_hex,
                "salt": salt_bytea,
                "estado": "activo",
            }),
        )
        if not usuario_res.ok:
            raise Exception(await usuario_res.text())

        # 7. Insertar en tabla del rol (socio / profesor / representante)
        hoy = date.today()
        payload = {"id_persona": id_persona}
        if rol == "socio":
            payload["id_sede"] = datos.id_sede
            payload["fecha_alta"] = hoy.isoformat()
        elif rol == "representante":
            payload["id_deporte"] = id_deporte

        rol_res = await fetch(
            f"{url}/rest/v1/{rol}",
            method="POST",
            headers=headers,
            body=json.dumps(payload),
        )
        if not rol_res.ok:
            raise Exception(await rol_res.text())
        rol_lista = await rol_res.json()
        datos_rol = rol_lista[0] if rol_lista else {}

        # 8. Si es socio y se indicó un plan (o existe un plan activo), crear membresía y primera cuota
        if rol == "socio":
            id_socio = datos_rol.get("id_socio")
            if datos.id_plan is not None and id_socio is not None:
                plan_res = await fetch(
                    f"{url}/rest/v1/plan_membresia?select=*&id_plan=eq.{datos.id_plan}&activo=eq.true",
                    headers=headers,
                )
                planes = await plan_res.json() if plan_res.ok else []
                if not planes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El plan con ID {datos.id_plan} no existe o está inactivo.",
                    )
                plan_info = planes[0]
                duracion = int(plan_info.get("duracion_dias") or 30)
                vencimiento = hoy + timedelta(days=duracion)
                monto = plan_info.get("precio") or plan_info.get("monto") or 0

                memb_res = await fetch(
                    f"{url}/rest/v1/membresia",
                    method="POST",
                    headers=headers,
                    body=json.dumps({
                        "id_socio": id_socio,
                        "id_plan": datos.id_plan,
                        "fecha_inicio": hoy.isoformat(),
                        "fecha_fin": vencimiento.isoformat(),
                        "estado": "activo",
                    }),
                )
                if not memb_res.ok:
                    raise Exception(await memb_res.text())
                memb_lista = await memb_res.json()
                id_membresia = memb_lista[0].get("id_membresia") if memb_lista else None

                cuota_payload = {
                    "id_socio": id_socio,
                    "periodo": hoy.replace(day=1).isoformat(),
                    "fecha_vencimiento": vencimiento.isoformat(),
                    "estado": "pendiente",
                    "monto": monto,
                }
                if id_membresia is not None:
                    cuota_payload["id_membresia"] = id_membresia

                cuota_res = await fetch(
                    f"{url}/rest/v1/cuota",
                    method="POST",
                    headers=headers,
                    body=json.dumps(cuota_payload),
                )
                if not cuota_res.ok:
                    raise Exception(await cuota_res.text())

        respuesta = {
            "mensaje": f"{rol.capitalize()} registrado exitosamente en el sistema.",
            "id_usuario": user_id,
            "id_persona": id_persona,
            "rol": rol,
            PK_POR_ROL[rol]: datos_rol.get(PK_POR_ROL[rol]),
        }

        if rol == "socio" and "codigo_credencial" in datos_rol:
            respuesta["codigo_credencial"] = datos_rol["codigo_credencial"]

        return respuesta

    except HTTPException:
        await _rollback(url, headers, user_id, id_persona, rol, id_socio)
        raise
    except Exception as e:
        await _rollback(url, headers, user_id, id_persona, rol, id_socio)
        logger.exception("Error al registrar el usuario")
        texto = str(e).lower()
        if "duplicate key" in texto or "23505" in texto or "already" in texto:
            raise HTTPException(status_code=409, detail="El DNI o el email ya están registrados.")
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar el usuario en la base de datos: {str(e)}",
        )