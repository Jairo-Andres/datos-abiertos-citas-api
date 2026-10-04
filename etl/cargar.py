import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CargaETL, Hospital, Oportunidad
from etl.fuentes import Fuente


def cargar_fuente(session: Session, fuente: Fuente, df: pd.DataFrame) -> int:
    """Reemplaza todos los registros del hospital con lo que trae la fuente hoy (carga idempotente)."""
    hospital = session.scalars(select(Hospital).where(Hospital.dataset_id == fuente.dataset_id)).first()
    if hospital is None:
        hospital = Hospital(dataset_id=fuente.dataset_id, nombre=fuente.hospital)
        session.add(hospital)
    hospital.nombre = fuente.hospital
    hospital.departamento = fuente.departamento
    hospital.municipio = fuente.municipio
    hospital.fuente_url = fuente.url
    session.flush()

    session.execute(delete(Oportunidad).where(Oportunidad.hospital_id == hospital.id))
    session.add_all(
        Oportunidad(
            hospital_id=hospital.id,
            especialidad=f.especialidad,
            periodo=f.periodo,
            granularidad=f.granularidad,
            definicion=f.definicion,
            dias_espera=float(f.dias_espera),
            citas=None if pd.isna(f.citas) else int(f.citas),
        )
        for f in df.itertuples(index=False)
    )
    return len(df)


def registrar_carga(session: Session, filas: int, ok: int, errores: int) -> None:
    session.add(CargaETL(filas=filas, datasets_ok=ok, datasets_error=errores))
