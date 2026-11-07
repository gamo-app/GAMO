from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from Base.base_importacion import (
    MAX_BYTES_ARCHIVO,
    generar_plantilla_csv,
    generar_plantilla_xlsx,
    importar_socios_desde_archivo,
)
from auth import validar_sesion

# router_rol.py lo publica bajo /rol/importar:
#   GET  /rol/importar/plantilla?formato=xlsx|csv
#   POST /rol/importar/socios?nombre_archivo=socios.xlsx   (el cuerpo es el archivo)
router = APIRouter()

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def _leer_archivo(request: Request) -> bytes:
    """El cuerpo del request ES el archivo (no hace falta multipart ni librerías extra)."""
    if request.headers.get("content-type", "").lower().startswith("multipart/"):
        raise HTTPException(
            status_code=415,
            detail="Enviá el archivo como cuerpo de la petición (body: archivo), no como FormData.",
        )
    demasiado_grande = HTTPException(
        status_code=413,
        detail=f"El archivo supera el máximo de {MAX_BYTES_ARCHIVO // (1024 * 1024)} MB.",
    )
    declarado = request.headers.get("content-length", "")
    if declarado.isdigit() and int(declarado) > MAX_BYTES_ARCHIVO:
        raise demasiado_grande
    contenido = await request.body()
    if len(contenido) > MAX_BYTES_ARCHIVO:
        raise demasiado_grande
    return contenido


@router.get("/plantilla", summary="Descargar la plantilla de importación de socios")
async def descargar_plantilla(
    formato: Literal["xlsx", "csv"] = Query("xlsx", description="Formato de la plantilla"),
    access_token: str = Depends(validar_sesion),
):
    if formato == "csv":
        contenido, media_type = generar_plantilla_csv(), "text/csv; charset=utf-8"
    else:
        contenido, media_type = generar_plantilla_xlsx().getvalue(), XLSX_MEDIA_TYPE
    return Response(
        content=contenido,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="plantilla_importacion_socios_gamo.{formato}"',
        },
    )


@router.post("/socios", summary="Importar socios desde un archivo .csv o .xlsx")
async def importar_socios(
    request: Request,
    nombre_archivo: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre del archivo (con su extensión .csv o .xlsx)",
    ),
    access_token: str = Depends(validar_sesion),
):
    contenido = await _leer_archivo(request)
    return await importar_socios_desde_archivo(request.scope["env"], nombre_archivo, contenido)