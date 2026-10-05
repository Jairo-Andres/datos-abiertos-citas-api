"""Filas que la fuente publica con errores evidentes y que el ETL no carga.

Cada regla está verificada contra la fuente original; el detalle está en docs/verificacion.md.
No se corrige ningún valor: lo que no se puede confirmar, no se publica.
"""

from datetime import date

import pandas as pd

MIN_CITAS = 10  # por debajo, un promedio depende de una o dos personas y no es representativo
MAX_DIAS = 365  # un promedio de más de un año de espera en un periodo de 3 o 6 meses no es posible


def _entre(df: pd.DataFrame, desde: date, hasta: date) -> pd.Series:
    return (df["periodo"] >= desde) & (df["periodo"] <= hasta)


def _es(df: pd.DataFrame, columna: str, valores: set[str]) -> pd.Series:
    return df[columna].isin(valores)


# dataset_id -> lista de (motivo, función que marca las filas a excluir)
REGLAS = {
    "2hbw-r639": [
        ("Neiva jul-2020 a dic-2021: los dos indicadores aparecen con las etiquetas invertidas",
         lambda df: _entre(df, date(2020, 7, 1), date(2021, 12, 1))),
        ("Neiva oct-2023, indicador 3.2: denominador 97794 en vez de 9794 (error de digitación)",
         lambda df: (df["periodo"] == date(2023, 10, 1)) & (df["definicion"] == "solicitud")),
    ],
    "thui-g47e": [
        (f"Clicsalud: promedio de más de {MAX_DIAS} días, imposible en un periodo de 3 o 6 meses",
         lambda df: df["dias_espera"] > MAX_DIAS),
    ],
    "dt6u-2gkm": [
        ("Colón 2021-T4 Psiquiatría: 24.156 citas, unas 20 veces lo normal",
         lambda df: (df["periodo"] == date(2021, 10, 1)) & _es(df, "especialidad", {"Psiquiatría"})),
        ("Colón 2021-T4 Ginecología, Ecografía y Obstetricia: valores idénticos copiados entre filas",
         lambda df: (df["periodo"] == date(2021, 10, 1)) & _es(df, "especialidad", {"Ginecología", "Ecografía", "Obstetricia"})),
        ("Colón 2023-T4: las citas suman más que T1 a T3 juntos; parece el total anual cargado como trimestre",
         lambda df: df["periodo"] == date(2023, 10, 1)),
    ],
}


def aplicar(df: pd.DataFrame, dataset_id: str) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """Devuelve el DataFrame sin las filas excluidas y la lista de (motivo, filas descartadas)."""
    descartes = []
    for motivo, regla in REGLAS.get(dataset_id, []):
        marca = regla(df)
        if marca.any():
            descartes.append((motivo, int(marca.sum())))
            df = df[~marca]
    pocas = df["citas"].notna() & (df["citas"] < MIN_CITAS)
    if pocas.any():
        descartes.append((f"menos de {MIN_CITAS} citas en el periodo", int(pocas.sum())))
        df = df[~pocas]
    return df, descartes
