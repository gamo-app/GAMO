from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.socios.sfiltro import router as socios_router
from app.representantes.recepcion import router as representantes_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    socios_router,
    prefix="/api/socios",
    tags=["Socios"],
)
app.include_router(
    representantes_router,
    prefix="/api/representantes",
    tags=["Representantes"],
)