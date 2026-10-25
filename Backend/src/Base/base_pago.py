from supabase import create_async_client

from supabase_config import get_supabase_config


async def get_all_pagos(env):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        response = await (
            supabase.table("pago")
            .select("id_pago,id_membresia,monto")
            .execute()
        )
        return response.data
    finally:
        await supabase.postgrest.aclose()


async def get_pagos_by_socio(env, codigo_credencial: str):
    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)

    try:
        membresias = await (
            supabase.table("membresia")
            .select("id_membresia")
            .eq("codigo_credencial", codigo_credencial)
            .execute()
        )
        ids_membresias = [
            membresia["id_membresia"] for membresia in membresias.data
        ]
        if not ids_membresias:
            return []

        response = await (
            supabase.table("pago")
            .select("id_pago,id_membresia,monto")
            .in_("id_membresia", ids_membresias)
            .execute()
        )
        return response.data
    finally:
        await supabase.postgrest.aclose()
