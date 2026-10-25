from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager
from Routers import (
    router_asistencia as asistencia,
    router_clase as clase,
    router_deporte as deporte,
    router_profesor as profesor,
    router_representante as representante,
    router_rol as rol,
    router_sede as sede,
    router_socio as socio,
    router_usuario as usuario,
    router_login as login,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from auth import validar_sesion


@asynccontextmanager
async def lifespan(app:FastAPI):
    yield


app = FastAPI(title="GAMO API", version="0.1.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://gamo-ekk.pages.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router,
                   prefix='/login',
                   tags=['login'],
                   responses={404: {"login": "Not Found"}})

app.include_router(asistencia.router,
                   prefix='/asistencia',
                   tags=['asistencia'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"asistencia": "Not Found"}})

app.include_router(clase.router,
                   prefix='/clase',
                   tags=['clase'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"clase": "Not Found"}})

app.include_router(deporte.router,
                   prefix='/deporte',
                   tags=['deporte'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"deporte": "Not Found"}})

app.include_router(profesor.router,
                   prefix='/profesor',
                   tags=['profesor'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"profesor": "Not Found"}})


app.include_router(representante.router,
                   prefix='/representante',
                   tags=['representante'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"representante": "Not Found"}})

app.include_router(sede.router,
                   prefix='/sede',
                   tags=['sede'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"sede": "Not Found"}})

app.include_router(socio.router,
                   prefix='/socio',
                   tags=['Socio'],
                   dependencies=[Depends(validar_sesion)],
                   responses={404: {"Socio": "Not Found"}})

app.include_router(usuario.router,
                   prefix='/usuario',
                   tags=['Usuario'],
                    # dependencies=[Depends(validar_sesion)],
                   responses={404: {"Usuario": "Not Found"}})

