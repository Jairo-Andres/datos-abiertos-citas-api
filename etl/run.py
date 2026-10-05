"""Ejecuta el ETL completo: descarga, transforma y carga en la base definida por DATABASE_URL.

Uso:
    python -m etl.run              # descarga de datos.gov.co y carga
    python -m etl.run --local      # usa los JSON ya descargados en data/raw (sin red)
    python -m etl.run --csv salida.csv   # además exporta el resultado unificado a CSV
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from app.db import Base, SessionLocal, engine
from app.observability import JsonFormatter
from etl.cargar import cargar_fuente, cargar_multiunidad, registrar_carga
from etl.extraer import descargar, descargar_bogota, leer_local
from etl.fuentes import FUENTES
from etl.transformar import transformar

RAW = Path("data/raw")
log = logging.getLogger("etl")


def configurar_logs() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    log.handlers = [handler]
    log.setLevel(logging.INFO)
    log.propagate = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--local", action="store_true", help="leer data/raw en vez de descargar")
    parser.add_argument("--csv", type=Path, help="exportar el resultado unificado a este CSV")
    args = parser.parse_args(argv)
    configurar_logs()
    Base.metadata.create_all(engine)

    total, ok, errores, partes = 0, 0, 0, []
    crudos: dict[str, list[dict]] = {}  # varias unidades pueden salir del mismo archivo (Bogotá)
    with SessionLocal() as session:
        for fuente in FUENTES:
            try:
                if fuente.dataset_id not in crudos:
                    if args.local:
                        crudos[fuente.dataset_id] = leer_local(fuente.dataset_id, RAW)
                    elif fuente.formato == "ckan_bogota":
                        crudos[fuente.dataset_id] = descargar_bogota(fuente.dataset_id, RAW)
                    else:
                        crudos[fuente.dataset_id] = descargar(fuente.dataset_id, RAW, filtro=fuente.filtro)
                df = transformar(fuente, crudos[fuente.dataset_id])
                n = (cargar_multiunidad if fuente.multiunidad else cargar_fuente)(session, fuente, df)
                session.commit()
                total += n
                ok += 1
                if fuente.multiunidad:
                    partes.append(df.rename(columns={"unidad": "hospital"}))
                else:
                    partes.append(df.assign(hospital=fuente.hospital, departamento=fuente.departamento))
                log.info("fuente cargada", extra={"extra_campos": {
                    "dataset": fuente.dataset_id, "unidad": fuente.hospital, "registros": n,
                    "unidades": int(df["unidad"].nunique()) if fuente.multiunidad else 1,
                    "especialidades": sorted(df["especialidad"].unique().tolist()),
                }})
            except Exception as e:  # una fuente caída no debe tumbar las demás
                session.rollback()
                errores += 1
                log.error("fuente con error", extra={"extra_campos": {
                    "dataset": fuente.dataset_id, "unidad": fuente.hospital, "error": repr(e),
                }})
        registrar_carga(session, total, ok, errores)
        session.commit()

    if args.csv and partes:
        pd.concat(partes).to_csv(args.csv, index=False)
    log.info("etl terminado", extra={"extra_campos": {"registros": total, "ok": ok, "errores": errores}})
    return 1 if ok == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
