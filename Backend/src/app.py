from fastapi import FastAPI
from contextlib import asynccontextmanager
from Routers import (
    router_asistencia as asistencia,
    router_clase as clase,
    router_deporte as deporte,
    router_pago as pago,
    router_persona as persona,
    router_profesor as profesor,
    router_representante as representante,
    router_rol as rol,
    router_sede as sede,
    router_socio as socio,
    router_usuario as usuario,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app:FastAPI):
    yield


app = FastAPI(title="GAMO API", version="0.1.0", lifespan=lifespan)

app.include_router(asistencia.router,
                   prefix='/asistencia',
                   tags=['asistencia'],
                   responses={404: {"asistencia": "Not Found"}})

app.include_router(clase.router,
                   prefix='/clase',
                   tags=['clase'],
                   responses={404: {"clase": "Not Found"}})

app.include_router(pago.router,
                   prefix='/pago',
                   tags=['pago'],
                   responses={404: {"pago": "Not Found"}})

app.include_router(deporte.router,
                   prefix='/deporte',
                   tags=['deporte'],
                   responses={404: {"deporte": "Not Found"}})

app.include_router(rol.router,
                   prefix='/rol',
                   tags=['rol'],
                   responses={404: {"rol": "Not Found"}})

# app.include_router(importacion.router,
#                    prefix='/importacion',
#                    tags=['importacion'],
#                    responses={404: {"importacion": "Not Found"}})

app.include_router(persona.router,
                   prefix='/persona',
                   tags=['persona'],
                   responses={404: {"persona": "Not Found"}})


app.include_router(profesor.router,
                   prefix='/profesor',
                   tags=['profesor'],
                   responses={404: {"profesor": "Not Found"}})


app.include_router(representante.router,
                   prefix='/representante',
                   tags=['representante'],
                   responses={404: {"representante": "Not Found"}})

app.include_router(sede.router,
                   prefix='/sede',
                   tags=['sede'],
                   responses={404: {"sede": "Not Found"}})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://gamo-ekk.pages.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(socio.router,
                   prefix='/socio',
                   tags=['Socio'],
                   responses={404: {"Socio": "Not Found"}})

app.include_router(usuario.router,
                   prefix='/usuario',
                   tags=['Usuario'],
                   responses={404: {"Usuario": "Not Found"}})

