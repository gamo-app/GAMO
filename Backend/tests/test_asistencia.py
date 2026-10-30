import sys
import types
import unittest
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

sys.path.insert(0, "src")
workers = types.ModuleType("workers")
workers.fetch = None
sys.modules.setdefault("workers", workers)

from Base import base_asistencia
from model import AsistenciaRegistro


class Resultado:
    def __init__(self, data):
        self.data = data


class ConsultaFalsa:
    def __init__(self, cliente, tabla):
        self.cliente = cliente
        self.tabla = tabla
        self.filtros = {}

    def select(self, *_):
        return self

    def eq(self, columna, valor):
        self.filtros[columna] = valor
        return self

    def limit(self, *_):
        return self

    def insert(self, datos):
        self.cliente.inserciones.append(datos)
        return self

    async def execute(self):
        clave = (self.tabla, tuple(sorted(self.filtros.items())))
        return Resultado(self.cliente.respuestas.get(clave, []))


class ClienteFalso:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.inserciones = []
        self.postgrest = types.SimpleNamespace(
            auth=lambda _: None,
            aclose=AsyncMock(),
        )

    def table(self, nombre):
        return ConsultaFalsa(self, nombre)


def clave(tabla, **filtros):
    return tabla, tuple(sorted(filtros.items()))


class TestRegistroAsistencia(unittest.IsolatedAsyncioTestCase):
    async def test_profesor_no_puede_registrar_en_clase_ajena(self):
        uuid_usuario = str(uuid.uuid4())
        uuid_clase = str(uuid.uuid4())
        codigo = str(uuid.uuid4())
        cliente = ClienteFalso({
            clave("socio", uuid_usuario=uuid_usuario): [
                {"codigo_credencial": codigo}
            ],
            clave("socio", codigo_credencial=codigo): [
                {"codigo_credencial": codigo}
            ],
            clave("clase", uuid_clase=uuid_clase): [
                {"uuid_clase": uuid_clase, "id_profesor": 10}
            ],
            clave("profesor", uuid_usuario=uuid_usuario): [
                {"id_profesor": 11}
            ],
        })

        with (
            patch.object(base_asistencia, "get_supabase_config", return_value=("url", "key")),
            patch.object(base_asistencia, "create_async_client", new=AsyncMock(return_value=cliente)),
        ):
            with self.assertRaises(HTTPException) as error:
                await base_asistencia.registrar_asistencia(
                    object(),
                    AsistenciaRegistro(
                        uuid_clase=uuid_clase,
                        fecha=date.today(),
                        codigo_credencial=codigo,
                    ),
                    uuid_usuario,
                    "Profesor",
                    "token",
                )

        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(cliente.inserciones, [])
        cliente.postgrest.aclose.assert_awaited_once()

    async def test_asistencia_manual_duplicada_es_rechazada(self):
        uuid_usuario = str(uuid.uuid4())
        uuid_clase = str(uuid.uuid4())
        codigo = str(uuid.uuid4())
        cliente = ClienteFalso({
            clave("socio", uuid_usuario=uuid_usuario): [
                {"codigo_credencial": codigo}
            ],
            clave("socio", codigo_credencial=codigo): [
                {"codigo_credencial": codigo}
            ],
            clave("clase", uuid_clase=uuid_clase): [
                {"uuid_clase": uuid_clase, "id_profesor": 10}
            ],
            clave(
                "asistencia",
                uuid_clase=uuid_clase,
                codigo_credencial=codigo,
                fecha=date.today().isoformat(),
            ): [{"id_asistencia": 1}],
        })

        with (
            patch.object(base_asistencia, "get_supabase_config", return_value=("url", "key")),
            patch.object(base_asistencia, "create_async_client", new=AsyncMock(return_value=cliente)),
        ):
            with self.assertRaises(HTTPException) as error:
                await base_asistencia.registrar_asistencia(
                    object(),
                    AsistenciaRegistro(
                        uuid_clase=uuid_clase,
                        fecha=date.today(),
                        codigo_credencial=codigo,
                    ),
                    uuid_usuario,
                    "Admin",
                    "token",
                )

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(cliente.inserciones, [])
        cliente.postgrest.aclose.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
