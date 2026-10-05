import pandas as pd
from sqlalchemy import delete, insert, or_, select
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


def cargar_multiunidad(session: Session, fuente: Fuente, df: pd.DataFrame) -> int:
    """Carga una fuente con muchas unidades (Clicsalud): crea o actualiza cada unidad, reemplaza todos los
    registros de ese dataset con una inserción por lotes y borra las unidades que ya no aparecen."""
    existentes = {h.nombre: h for h in session.scalars(select(Hospital))}
    unidades = df[["unidad", "departamento", "municipio"]].drop_duplicates("unidad")
    for u in unidades.itertuples(index=False):
        hospital = existentes.get(u.unidad)
        if hospital is None:
            hospital = existentes[u.unidad] = Hospital(nombre=u.unidad)
            session.add(hospital)
        hospital.tipo = fuente.tipo
        hospital.departamento = u.departamento
        hospital.municipio = u.municipio
        hospital.dataset_id = fuente.dataset_id
        hospital.fuente_url = fuente.url
    session.flush()

    session.execute(delete(Oportunidad).where(Oportunidad.dataset_id == fuente.dataset_id))
    filas = [
        {
            "hospital_id": existentes[f.unidad].id,
            "especialidad": f.especialidad,
            "periodo": f.periodo,
            "granularidad": f.granularidad,
            "definicion": f.definicion,
            "dias_espera": float(f.dias_espera),
            "citas": None if pd.isna(f.citas) else int(f.citas),
            "dataset_id": fuente.dataset_id,
        }
        for f in df.itertuples(index=False)
    ]
    if filas:
        session.execute(insert(Oportunidad), filas)
    vigentes = set(unidades["unidad"])
    for hospital in existentes.values():
        if hospital.dataset_id == fuente.dataset_id and hospital.nombre not in vigentes:
            session.delete(hospital)
    return len(filas)


def registrar_carga(session: Session, filas: int, ok: int, errores: int) -> None:
    session.add(CargaETL(filas=filas, datasets_ok=ok, datasets_error=errores))
