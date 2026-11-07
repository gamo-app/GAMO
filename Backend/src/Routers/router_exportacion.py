import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from Base import base_rol as rol
from Base.base_exportacion import (
    generar_pdf_socios,
    generar_xlsx_socios,
    nombre_archivo_exportacion,
)
from auth import validar_sesion

# router_rol.py lo publica bajo /rol/exportar: GET /rol/exportar/xlsx y GET /rol/exportar/pdf.
router = APIRouter()
logger = logging.getLogger(__name__)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Armar el PDF es lo más pesado de la exportación: por encima de este tope conviene usar Excel.
MAX_FILAS_PDF = 2000


async def _socios_a_exportar(
    request: Request,
    access_token: str,
    estado: str | None,
    id_sede: int | None,
    buscar: str | None,
    id_plan: int | None,
    uuid_clase: UUID | None,
):
    """Todos los socios que cumplen los filtros, sin paginar. El rol va fijo: solo socios."""
    return await rol.obtener_usuarios_para_exportar(
        env=request.scope["env"],
        access_token=access_token,
        rol="socio",
        estado=estado,
        id_sede=id_sede,
        buscar=buscar,
        id_plan=id_plan,
        uuid_clase=uuid_clase,
    )


def _filtros_aplicados(
    usuarios: list,
    estado: str | None,
    id_sede: int | None,
    id_plan: int | None,
    buscar: str | None,
    uuid_clase: UUID | None,
) -> dict[str, str]:
    """Filtros que se muestran en el encabezado del archivo.

    Si el filtro dejó resultados, el nombre de la clase/sede/plan sale del primer socio
    (todos comparten ese valor por el filtro); si no, se muestra el ID.
    """
    primero = usuarios[0] if usuarios else None
    filtros: dict[str, str] = {}
    if uuid_clase:
        filtros["Clase"] = (primero.clase if primero else None) or str(uuid_clase)
    if estado and estado.strip().lower() not in ("", "todos", "todas"):
        filtros["Estado"] = estado.strip().capitalize()
    if id_sede and id_sede > 0:
        filtros["Sede"] = (primero.sede if primero else None) or f"N° {id_sede}"
    if id_plan and id_plan > 0:
        filtros["Plan"] = (primero.plan if primero else None) or f"N° {id_plan}"
    if buscar and buscar.strip():
        filtros["Búsqueda"] = buscar.strip()
    return filtros


def _generar(generador, usuarios: list, filtros: dict[str, str], formato: str):
    """Arma el archivo. Si falla responde un error claro en JSON en vez de un 500 sin detalle."""
    try:
        return generador(usuarios, filtros)
    except Exception:
        logger.exception("Error al generar el archivo %s de socios", formato)
        raise HTTPException(status_code=500, detail=f"No se pudo generar el archivo {formato}.")


def _respuesta_descarga(contenido: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=contenido,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # Es el padrón de socios (DNI, cuotas): que no quede guardado en cachés.
            "Cache-Control": "no-store",
        },
    )


@router.get("/xlsx", summary="Exportar socios filtrados a XLSX")
async def exportar_usuarios_xlsx(
    request: Request,
    estado: str | None = Query(
        None,
        description="Estado: Todos, Activos, Inactivos, Morosos, Pendientes, Al dia",
    ),
    id_sede: int | None = Query(
        None,
        description="ID de la sede (omitir o 0 para Todas las sedes)",
    ),
    buscar: str | None = Query(
        None,
        max_length=100,
        description="Buscar por nombre, apellido o DNI",
    ),
    id_plan: int | None = Query(
        None,
        description="Opcional: filtrar socios por ID de plan de membresía",
    ),
    uuid_clase: UUID | None = Query(
        None,
        description="Opcional: exportar solo los socios de esta clase (UUID de la clase)",
    ),
    id_clase: UUID | None = Query(
        None,
        include_in_schema=False,
    ),
    access_token: str = Depends(validar_sesion),
):
    uuid_clase = uuid_clase or id_clase
    usuarios = await _socios_a_exportar(
        request, access_token, estado, id_sede, buscar, id_plan, uuid_clase
    )
    filtros = _filtros_aplicados(usuarios, estado, id_sede, id_plan, buscar, uuid_clase)
    archivo_xlsx = _generar(generar_xlsx_socios, usuarios, filtros, "XLSX")
    clase = usuarios[0].clase if (uuid_clase and usuarios) else None
    filename = nombre_archivo_exportacion(clase, estado, "xlsx")
    return _respuesta_descarga(archivo_xlsx.getvalue(), XLSX_MEDIA_TYPE, filename)


@router.get("/pdf", summary="Exportar socios filtrados a PDF")
async def exportar_usuarios_pdf(
    request: Request,
    estado: str | None = Query(
        None,
        description="Estado: Todos, Activos, Inactivos, Morosos, Pendientes, Al dia",
    ),
    id_sede: int | None = Query(
        None,
        description="ID de la sede (omitir o 0 para Todas las sedes)",
    ),
    buscar: str | None = Query(
        None,
        max_length=100,
        description="Buscar por nombre, apellido o DNI",
    ),
    id_plan: int | None = Query(
        None,
        description="Opcional: filtrar socios por ID de plan de membresía",
    ),
    uuid_clase: UUID | None = Query(
        None,
        description="Opcional: exportar solo los socios de esta clase (UUID de la clase)",
    ),
    id_clase: UUID | None = Query(
        None,
        include_in_schema=False,
    ),
    access_token: str = Depends(validar_sesion),
):
    uuid_clase = uuid_clase or id_clase
    usuarios = await _socios_a_exportar(
        request, access_token, estado, id_sede, buscar, id_plan, uuid_clase
    )
    if len(usuarios) > MAX_FILAS_PDF:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El PDF admite hasta {MAX_FILAS_PDF} socios y estos filtros devuelven "
                f"{len(usuarios)}. Filtrá por clase o sede, o exportá a Excel."
            ),
        )
    filtros = _filtros_aplicados(usuarios, estado, id_sede, id_plan, buscar, uuid_clase)
    archivo_pdf = _generar(generar_pdf_socios, usuarios, filtros, "PDF")
    clase = usuarios[0].clase if (uuid_clase and usuarios) else None
    filename = nombre_archivo_exportacion(clase, estado, "pdf")
    return _respuesta_descarga(archivo_pdf.getvalue(), "application/pdf", filename)