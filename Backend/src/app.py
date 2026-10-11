from fastapi import FastAPI
from contextlib import asynccontextmanager
from Socios import asistencia,clase,cuota,deporte,grupos_roles,importacion,inscripcion,persona,profesor,representante,sede,socio,usuario


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

app.include_router(cuota.router,
                   prefix='/cuota',
                   tags=['cuota'],
                   responses={404: {"cuota": "Not Found"}})

app.include_router(deporte.router,
                   prefix='/deporte',
                   tags=['deporte'],
                   responses={404: {"deporte": "Not Found"}})

app.include_router(grupos_roles.router,
                   prefix='/grupos_roles',
                   tags=['grupos_roles'],
                   responses={404: {"grupos_roles": "Not Found"}})

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

app.include_router(socio.router,
                   prefix='/socio',
                   tags=['Socio'],
                   responses={404: {"Socio": "Not Found"}})

app.include_router(usuario.router,
                   prefix='/usuario',
                   tags=['Usuario'],
                   responses={404: {"Usuario": "Not Found"}})


