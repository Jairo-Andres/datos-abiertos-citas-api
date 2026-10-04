from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import APP_VERSION
from app.db import get_session
from app.models import CargaETL, Hospital, Oportunidad
from app.observability import latencias

router = APIRouter(tags=["estado"])


@router.get("/health")
def health(session: Session = Depends(get_session)):
    try:
        session.execute(text("SELECT 1"))
        db = "ok"
    except Exception:
        db = "error"
    return {"status": "ok" if db == "ok" else "degradado", "db": db, "version": APP_VERSION}


@router.get("/estado")
def estado(session: Session = Depends(get_session)):
    """Datos para el panel de estado: última carga del ETL, volumen y latencias."""
    ultima = session.scalars(select(CargaETL).order_by(CargaETL.ejecutada_en.desc()).limit(1)).first()
    return {
        "hospitales": session.scalar(select(func.count(Hospital.id))),
        "registros": session.scalar(select(func.count(Oportunidad.id))),
        "ultima_carga_etl": None if ultima is None else {
            "fecha": ultima.ejecutada_en,
            "filas": ultima.filas,
            "datasets_ok": ultima.datasets_ok,
            "datasets_error": ultima.datasets_error,
        },
        "metricas": latencias.resumen(),
    }
