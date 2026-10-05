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


def test_carga_por_dataset_no_borra_otras_fuentes_de_la_misma_unidad():
    principal = Fuente("aaaa-1111", "Hospital compartido", "Huila", "Neiva", "x")
    secundaria = Fuente("bbbb-2222", "Hospital compartido", "Huila", "Neiva", "x", principal=False)
    db.Base.metadata.drop_all(db.engine)
    db.Base.metadata.create_all(db.engine)
    with db.SessionLocal() as s:
        h = Hospital(nombre="Hospital compartido", departamento="Huila", municipio="Neiva", dataset_id="aaaa-1111", fuente_url="u")
        s.add(h)
        s.flush()
        # fila de una carga anterior a la columna dataset_id
        s.add(Oportunidad(hospital_id=h.id, especialidad="Vieja", periodo=date(2020, 1, 1), granularidad="mes",
                          definicion="solicitud", dias_espera=9.0))
        s.commit()

        cargar_fuente(s, principal, _df(3.0))
        s.commit()
        semestral = _df(5.0).assign(granularidad="semestre")
        cargar_fuente(s, secundaria, semestral)
        s.commit()
        cargar_fuente(s, principal, _df(4.0))  # recarga de la principal: no toca la secundaria
        s.commit()

        filas = s.scalars(select(Oportunidad).order_by(Oportunidad.dataset_id)).all()
        assert [(f.dataset_id, f.granularidad, f.dias_espera) for f in filas] == [
            ("aaaa-1111", "mes", 4.0),
            ("bbbb-2222", "semestre", 5.0),
        ]
        hospital = s.scalars(select(Hospital)).one()
        assert hospital.dataset_id == "aaaa-1111"  # la fuente secundaria no cambia el origen de la unidad


def test_carga_multiunidad_reemplaza_y_borra_unidades_que_desaparecen():
    from etl.cargar import cargar_multiunidad

    fuente = Fuente("cccc-3333", "Clicsalud", "", "", "x", tipo="ips", multiunidad=True)

    def df(unidades):
        return pd.DataFrame([{"unidad": u, "departamento": "Antioquia", "municipio": "Medellín", "especialidad": "Odontología",
                              "periodo": date(2020, 1, 1), "granularidad": "trimestre", "definicion": "solicitud",
                              "dias_espera": 2.0, "citas": 50} for u in unidades])

    db.Base.metadata.drop_all(db.engine)
    db.Base.metadata.create_all(db.engine)
    with db.SessionLocal() as s:
        cargar_fuente(s, FUENTE, _df(3.0))  # otra fuente, no debe tocarse
        cargar_multiunidad(s, fuente, df(["IPS A", "IPS B"]))
        s.commit()
        cargar_multiunidad(s, fuente, df(["IPS A", "IPS C"]))
        s.commit()
        nombres = sorted(h.nombre for h in s.scalars(select(Hospital)))
        assert nombres == ["Hospital de prueba", "IPS A", "IPS C"]
        assert {h.tipo for h in s.scalars(select(Hospital).where(Hospital.nombre.like("IPS%")))} == {"ips"}
        assert s.scalar(select(func.count(Oportunidad.id)).where(Oportunidad.dataset_id == "cccc-3333")) == 2
        assert s.scalar(select(func.count(Oportunidad.id)).where(Oportunidad.dataset_id == "abcd-1234")) == 1
