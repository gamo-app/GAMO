from fastapi import APIRouter, Depends
from supabase import Client
from app.database import get_supabase
from . import admin, recepcion

router = APIRouter()


@router.get("/sedes", tags=["Sedes"])
def listar_sedes(supabase: Client = Depends(get_supabase)):
    res = (
        supabase.table("sede")
        .select("id_sede, nombre, direccion, mail, telefono")
        .eq("activo", True)
        .order("nombre")
        .execute()
    )
    return res.data or []


@router.get("/deportes", tags=["Deportes"])
def listar_deportes(supabase: Client = Depends(get_supabase)):
    res = (
        supabase.table("deporte")
        .select("id_deporte, nombre, descripcion")
        .eq("activo", True)
        .order("nombre")
        .execute()
    )
    return res.data or []


router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["Usuarios - Administrador"]
)
router.include_router(
    recepcion.router, 
    prefix="/recepcion", 
    tags=["Usuarios - Recepción"]
)

__all__ = ["router"]