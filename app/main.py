from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import APP_VERSION
from app.db import Base, engine
from app.observability import LatenciaMiddleware, configurar_logs
from app.routers import datos, health

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="API de oportunidad de citas · datos abiertos Colombia",
    description="Días de espera para citas médicas en hospitales públicos de Colombia, unificados desde datos.gov.co.",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.add_middleware(LatenciaMiddleware, logger=configurar_logs())
# Solo lectura y datos públicos: se permite cualquier origen para que el dashboard la consuma.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
app.include_router(health.router)
app.include_router(datos.router)


@app.get("/", include_in_schema=False)
def landing():
    return FileResponse(STATIC / "index.html")
