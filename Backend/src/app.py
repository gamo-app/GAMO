from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from Socios import socio, usuario, profesores, representante


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
app.include_router(socio.router,
                   prefix='/socio',
                   tags=['Socio'],
                   responses={404: {"Socio": "Not Found"}})

app.include_router(usuario.router,
                   prefix='/usuario',
                   tags=['Usuario'],
                   responses={404: {"Usuario": "Not Found"}})

app.include_router(profesores.router,
                   prefix='/profesores',
                   tags=['profesores'],
                   responses={404: {"profesores": "Not Found"}})

app.include_router(representante.router,
                   prefix='/representante',
                   tags=['Representante'],
                   responses={404: {"Representante": "Not Found"}})
