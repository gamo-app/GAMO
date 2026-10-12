import hashlib
import os
from fastapi import HTTPException
from supabase_config import get_supabase_config
from workers import fetch
from model import SocioAltaCreate
import json
import jwt

JWT_SECRET = "rot8jwyocrmwefDXFGVERVDSFCGWERCGWerwok9r9834752345%&/"  # espamié el teclado, no se si es seguro
ID_SEDE_DEFAULT = 1
ID_GRUPO_SOCIO = 1

def hash(password : str, salt : bytes) -> str:
    return hashlib.sha256(salt + password.encode()).hexdigest()

def get_random_salt() -> bytes:
    return os.urandom(16)

async def login(env, email : str, password : str):

    user = await get_user_from_email(env, email)
    salt : bytes = user.get("salt", None)

    hashed_object : str = hash(password, salt)
    if hashed_object == user.get("hash", None):
        return {"jwt": await generate_jwt(env, user.get("id_usuario"))}
    else:
        return {"jwt_falso": jwt.encode({"user_id": "68b79ba5-e7b6-4e2c-a9d2-38d46b1772c4", "group" : "Socio"}, JWT_SECRET, algorithm="HS256")}
 
async def generate_jwt(env, user_id: str):
    payload = {
        "user_id": user_id,
        "group": await get_user_group(env, user_id),
        #"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expira en 1 hora
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

async def get_user_from_email(env, email : str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?email=eq.{email.strip()}&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()

async def get_user_group(env, user_id: str):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?id_usuario=eq.{user_id}&select=grupo_usuario(nombre)",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    data = await response.json()
    return data[0]["grupo_usuario"]["nombre"]

async def create_user(env, datos: SocioAltaCreate) -> dict:
    url, key = get_supabase_config(env)

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    # 1. Crear la identidad en Supabase Auth
    auth_response = await fetch(
        f"{url}/auth/v1/admin/users",
        method="POST",
        headers=headers,
        body=json.dumps({
            "email": str(datos.usuario.email),
            "password": datos.usuario.password,
            "email_confirm": False,
        }),
    )

    if not auth_response.ok:
        detalle = await auth_response.text()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo crear el usuario en Auth: {detalle}",
        )

    auth_user = await auth_response.json()
    id_usuario = auth_user["id"]

    # 2. Crear persona, usuario y socio mediante la función SQL
    payload = {
        "p_id_usuario": id_usuario,
        "p_persona": datos.persona.model_dump(mode="json"),
        "p_usuario": {
            "email": str(datos.usuario.email),
            "nombre_usuario": datos.usuario.nombre_usuario,
        },
        "p_id_sede": ID_SEDE_DEFAULT,
        "p_id_grupo": ID_GRUPO_SOCIO,
    }

    response = await fetch(
        f"{url}/rest/v1/rpc/crear_socio",
        method="POST",
        headers=headers,
        body=json.dumps(payload),
    )

    if not response.ok:
        detalle = await response.text()

        # 3. Intentar limpiar la identidad si falló el registro en GAMO
        await fetch(
            f"{url}/auth/v1/admin/users/{id_usuario}",
            method="DELETE",
            headers=headers,
        )

        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el socio: {detalle}",
        )

    resultado = await response.json()

    return {
        "mensaje": "Socio registrado correctamente",
        **resultado,
    }

async def create_user_with_auth(env, datos_usuario: dict, password: str):
    url, key = get_supabase_config(env)

    # 1. Crear usuario en Supabase Auth
    auth_resp = await fetch(
        f"{url}/auth/v1/signup",
        method="POST",
        headers={
            "apikey": key,
            "Content-Type": "application/json",
        },
        body=json.dumps({
            "email": datos_usuario["email"],
            "password": password,
        }),
    )

    if not auth_resp.ok:
        raise HTTPException(
            status_code=auth_resp.status,
            detail=f"Error en Auth: {await auth_resp.text()}",
        )

    auth_data = await auth_resp.json()
    user_info = auth_data.get("user") or auth_data
    auth_uuid = user_info["id"]  # Este UUID generado por Auth se usará como FK

    # 2. Insertar en public.usuario usando ese UUID válido
    datos_usuario["id_usuario"] = auth_uuid

    db_resp = await fetch(
        f"{url}/rest/v1/usuario",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        body=json.dumps(datos_usuario),
    )

    if not db_resp.ok:
        raise HTTPException(
            status_code=db_resp.status,
            detail=await db_resp.text(),
        )

    return await db_resp.json()

async def get_sesion(env, id_usuario: str):
    url, key = get_supabase_config(env)

    # ========================================================
    # 1. Obtener usuario
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/usuario"
        f"?id_usuario=eq.{id_usuario}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    usuarios = await response.json()

    if not usuarios:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    usuario = usuarios[0]

    id_persona = usuario["id_persona"]
    id_grupo = usuario["id_grupo"]


    # ========================================================
    # 2. Obtener persona
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/persona"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    personas = await response.json()

    if not personas:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    persona = personas[0]


    # ========================================================
    # 3. Obtener grupo / rol
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/grupo_usuario"
        f"?id_grupo=eq.{id_grupo}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    grupos = await response.json()

    if not grupos:
        raise HTTPException(
            status_code=404,
            detail="Grupo de usuario no encontrado"
        )

    grupo = grupos[0]


    # ========================================================
    # 4. Buscar si es socio
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/socio"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    socios = await response.json()


    # ========================================================
    # 5. Buscar si es profesor
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/profesor"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    profesores = await response.json()


    # ========================================================
    # 6. Buscar si es representante
    # ========================================================

    response = await fetch(
        f"{url}/rest/v1/representante"
        f"?id_persona=eq.{id_persona}"
        "&select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    representantes = await response.json()


    # ========================================================
    # 7. Construir respuesta
    # ========================================================

    return {
        "usuario": usuario,
        "persona": persona,
        "rol": grupo,
        "socio": socios[0] if socios else None,
        "profesor": profesores[0] if profesores else None,
        "representante": representantes[0] if representantes else None
    }



async def get_all_usuarios(env):
    url, key = get_supabase_config(env)
    response = await fetch(
        f"{url}/rest/v1/usuario?select=*",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status,
            detail=await response.text(),
        )

    return await response.json()   