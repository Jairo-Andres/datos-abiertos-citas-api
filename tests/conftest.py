import os
from datetime import date

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.db as db  # noqa: E402

# Una sola conexión compartida para que la base en memoria sobreviva entre peticiones.
db.engine = db.create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db.SessionLocal.configure(bind=db.engine)

import app.main as main  # noqa: E402
from app.models import Hospital, Oportunidad  # noqa: E402

main.engine = db.engine


@pytest.fixture()
def client():
    db.Base.metadata.drop_all(db.engine)
    db.Base.metadata.create_all(db.engine)
    with db.SessionLocal() as s:
        h1 = Hospital(nombre="Hospital A", departamento="Cauca", municipio="Popayán", dataset_id="x1", fuente_url="u1")
        h2 = Hospital(nombre="Hospital B", departamento="Huila", municipio="Neiva", dataset_id="x2", fuente_url="u2")
        s.add_all([h1, h2])
        s.flush()
        s.add_all([
            Oportunidad(hospital_id=h1.id, especialidad="Ginecología", periodo=date(2024, 1, 1), granularidad="mes", definicion="solicitud", dias_espera=12.5, citas=40),
            Oportunidad(hospital_id=h1.id, especialidad="Pediatría", periodo=date(2024, 2, 1), granularidad="mes", definicion="solicitud", dias_espera=8, citas=None),
            Oportunidad(hospital_id=h2.id, especialidad="Ginecología", periodo=date(2024, 1, 1), granularidad="trimestre", definicion="fecha_deseada", dias_espera=20, citas=10),
        ])
        s.commit()
    with TestClient(main.app) as c:
        yield c
