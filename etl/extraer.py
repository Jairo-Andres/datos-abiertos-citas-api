import io
import json
import logging
import time
from pathlib import Path

import pandas as pd
import requests

log = logging.getLogger("etl")

BASE = "https://www.datos.gov.co/resource/{id}.json"
CKAN_BOGOTA = "https://datosabiertos.bogota.gov.co/api/3/action/package_show"
PAQUETE_BOGOTA = "oportunidad-de-la-atencion-ambulatoria-red-publica-de-bogota-d-c"
USER_AGENT = "datos-abiertos-citas-api/0.1 (portafolio academico; github.com/Jairo-Andres)"
PAGINA = 50_000
PAUSA_S = 1.0


def descargar(dataset_id: str, destino: Path, sesion: requests.Session | None = None, filtro: str | None = None) -> list[dict]:
    """Descarga todas las filas de un dataset Socrata paginando, y las guarda en destino/ID.json.

    filtro es un $where de SoQL para traer solo las filas útiles de datasets grandes.
    """
    sesion = sesion or requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT
    filas: list[dict] = []
    offset = 0
    while True:
        params = {"$limit": PAGINA, "$offset": offset, "$order": ":id"}
        if filtro:
            params["$where"] = filtro
        r = sesion.get(BASE.format(id=dataset_id), params=params, timeout=120)
        r.raise_for_status()
        lote = r.json()
        filas.extend(lote)
        log.info("descarga", extra={"extra_campos": {"dataset": dataset_id, "offset": offset, "filas": len(lote)}})
        if len(lote) < PAGINA:
            break
        offset += PAGINA
        time.sleep(PAUSA_S)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{dataset_id}.json").write_text(json.dumps(filas, ensure_ascii=False), encoding="utf-8")
    return filas


def descargar_bogota(dataset_id: str, destino: Path, sesion: requests.Session | None = None) -> list[dict]:
    """Descarga el CSV de oportunidad del portal de Bogotá (CKAN) y lo guarda como destino/ID.json.

    El archivo viene en Latin-1, separado por punto y coma y con coma decimal; se guarda todo como texto.
    """
    sesion = sesion or requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT
    r = sesion.get(CKAN_BOGOTA, params={"id": PAQUETE_BOGOTA}, timeout=60)
    r.raise_for_status()
    recursos = [
        x for x in r.json()["result"]["resources"]
        if (x.get("format") or "").upper() == "CSV" and "metadato" not in (x.get("name") or "").lower()
    ]
    if not recursos:
        raise ValueError("el paquete de Bogotá no trae un CSV de datos")
    time.sleep(PAUSA_S)
    archivo = sesion.get(recursos[0]["url"], timeout=60)
    archivo.raise_for_status()
    df = pd.read_csv(io.BytesIO(archivo.content), sep=";", encoding="latin-1", dtype=str)
    filas = df.where(df.notna(), None).to_dict(orient="records")
    log.info("descarga", extra={"extra_campos": {"dataset": dataset_id, "filas": len(filas)}})
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{dataset_id}.json").write_text(json.dumps(filas, ensure_ascii=False), encoding="utf-8")
    return filas


def leer_local(dataset_id: str, origen: Path) -> list[dict]:
    return json.loads((origen / f"{dataset_id}.json").read_text(encoding="utf-8"))
