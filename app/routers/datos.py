from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Hospital, Oportunidad
from app.schemas import HospitalOut, OportunidadOut, Pagina

router = APIRouter(tags=["datos"])


@router.get("/hospitales", response_model=list[HospitalOut])
def hospitales(
    depto: str | None = Query(None, description="Departamento, sin importar mayúsculas"),
    session: Session = Depends(get_session),
):
    consulta = select(Hospital).order_by(Hospital.nombre)
    if depto:
        consulta = consulta.where(func.lower(Hospital.departamento) == depto.lower())
    return session.scalars(consulta).all()


@router.get("/especialidades", response_model=list[str])
def especialidades(session: Session = Depends(get_session)):
    return session.scalars(select(Oportunidad.especialidad).distinct().order_by(Oportunidad.especialidad)).all()


@router.get("/oportunidad", response_model=Pagina)
def oportunidad(
    especialidad: str | None = Query(None, description="Coincidencia parcial, p. ej. 'gine'"),
    depto: str | None = Query(None, description="Departamento exacto, sin importar mayúsculas"),
    hospital_id: int | None = None,
    definicion: str | None = Query(None, pattern="^(solicitud|fecha_deseada)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    filtros = []
    if especialidad:
        filtros.append(func.lower(Oportunidad.especialidad).contains(especialidad.lower()))
    if depto:
        filtros.append(func.lower(Hospital.departamento) == depto.lower())
    if hospital_id is not None:
        filtros.append(Hospital.id == hospital_id)
    if definicion:
        filtros.append(Oportunidad.definicion == definicion)

    base = select(Oportunidad, Hospital).join(Hospital).where(*filtros)
    total = session.scalar(select(func.count()).select_from(base.subquery()))
    filas = session.execute(
        base.order_by(Oportunidad.periodo.desc(), Hospital.nombre, Oportunidad.especialidad).limit(limit).offset(offset)
    ).all()
    items = [
        OportunidadOut(
            hospital=h.nombre,
            tipo=h.tipo,
            departamento=h.departamento,
            municipio=h.municipio,
            especialidad=o.especialidad,
            periodo=o.periodo,
            granularidad=o.granularidad,
            definicion=o.definicion,
            dias_espera=o.dias_espera,
            citas=o.citas,
        )
        for o, h in filas
    ]
    return Pagina(total=total, limit=limit, offset=offset, items=items)
