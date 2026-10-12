import json
from fastapi import HTTPException, Request, APIRouter
from model import SocioAltaCreate
from supabase_config import get_supabase_config
from workers import fetch

router = APIRouter()

ID_SEDE_DEFAULT = 1
ID_GRUPO_SOCIO = 1

@router.post("/socio", status_code=201)
async def post_usuario(
    datos: SocioAltaCreate,
    request: Request,
):
    return await create_user(
        request.scope["env"],
        datos,
    )
    
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



#------------------------------------------
#------------------------------------------
#------------------------------------------
#------------------------------------------
#------------------------------------------




@router.get("/me/{id_usuario}")
async def get_mi_sesion(request: Request, id_usuario: str):

    return await get_sesion(
        request.scope["env"],
        id_usuario
    )


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