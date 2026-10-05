import pandas as pd
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models import CargaETL, Hospital, Oportunidad
from etl.fuentes import Fuente


def cargar_fuente(session: Session, fuente: Fuente, df: pd.DataFrame) -> int:
    """Reemplaza los registros que esta fuente aportó a la unidad con lo que trae hoy (carga idempotente)."""
    # Se identifica por nombre: un mismo dataset puede traer varias unidades (las subredes de Bogotá).
    hospital = session.scalars(select(Hospital).where(Hospital.nombre == fuente.hospital)).first()
    if hospital is None:
        hospital = Hospital(nombre=fuente.hospital)
        session.add(hospital)
    if fuente.principal or not hospital.dataset_id:
        hospital.dataset_id = fuente.dataset_id
        hospital.fuente_url = fuente.url
    hospital.tipo = fuente.tipo
    hospital.departamento = fuente.departamento
    hospital.municipio = fuente.municipio
    session.flush()

    # Las filas sin dataset_id son de cargas anteriores a esa columna: la primera carga nueva las reemplaza.
    session.execute(delete(Oportunidad).where(
        Oportunidad.hospital_id == hospital.id,
        or_(Oportunidad.dataset_id == fuente.dataset_id, Oportunidad.dataset_id.is_(None)),
    ))
    session.add_all(
        Oportunidad(
            hospital_id=hospital.id,
            especialidad=f.especialidad,
            periodo=f.periodo,
            granularidad=f.granularidad,
            definicion=f.definicion,
            dias_espera=float(f.dias_espera),
            citas=None if pd.isna(f.citas) else int(f.citas),
            dataset_id=fuente.dataset_id,
        )
        for f in df.itertuples(index=False)
    )
    return len(df)


def registrar_carga(session: Session, filas: int, ok: int, errores: int) -> None:
    session.add(CargaETL(filas=filas, datasets_ok=ok, datasets_error=errores))
