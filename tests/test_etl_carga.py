from datetime import date

import pandas as pd
from sqlalchemy import func, select

import app.db as db
from app.models import Hospital, Oportunidad
from etl.cargar import cargar_fuente
from etl.fuentes import Fuente

FUENTE = Fuente("abcd-1234", "Hospital de prueba", "Cauca", "Popayán", "x")


def _df(dias):
    return pd.DataFrame([{"especialidad": "Pediatría", "periodo": date(2024, 1, 1), "granularidad": "mes",
                          "definicion": "solicitud", "dias_espera": dias, "citas": pd.NA}])


def test_carga_es_idempotente():
    db.Base.metadata.drop_all(db.engine)
    db.Base.metadata.create_all(db.engine)
    with db.SessionLocal() as s:
        cargar_fuente(s, FUENTE, _df(3.0))
        s.commit()
        cargar_fuente(s, FUENTE, _df(4.0))
        s.commit()
        assert s.scalar(select(func.count(Hospital.id))) == 1
        filas = s.scalars(select(Oportunidad)).all()
        assert [(f.dias_espera, f.citas) for f in filas] == [(4.0, None)]
