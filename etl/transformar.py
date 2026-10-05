"""Una función por fuente: convierte las filas crudas de Socrata al esquema común.

Esquema común (una fila por hospital × especialidad × periodo × definición):
    especialidad, periodo (date), granularidad ("mes" | "trimestre" | "semestre"),
    definicion ("solicitud" | "fecha_deseada"), dias_espera (float), citas (int | None)
"""

import logging
import re

import pandas as pd

from etl import exclusiones
from etl.especialidades import TODAS, desde_indicador, normalizar, sin_tildes
from etl.fuentes import Fuente

log = logging.getLogger("etl")

COLUMNAS = ["especialidad", "periodo", "granularidad", "definicion", "dias_espera", "citas"]

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
TRIMESTRES = {"I": 1, "II": 4, "III": 7, "IV": 10}
SEMESTRES = {"I": 1, "II": 7, "1": 1, "2": 7}


def _num(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce")


def _fecha(anio: pd.Series, mes: pd.Series) -> pd.Series:
    return pd.to_datetime(pd.DataFrame({"year": anio, "month": mes, "day": 1})).dt.date


def _avisar(dataset: str, mensaje: str, filas: int) -> None:
    if filas:
        log.warning(mensaje, extra={"extra_campos": {"dataset": dataset, "filas": int(filas)}})


def _descartar_duplicados(df: pd.DataFrame, claves: list[str], dataset: str) -> pd.DataFrame:
    """Si la fuente trae el mismo periodo dos veces con valores distintos, no hay cómo saber cuál es
    el correcto: se descartan ambas filas y se deja constancia en el log."""
    dup = df.duplicated(claves, keep=False)
    _avisar(dataset, "periodo duplicado en la fuente: se descarta", dup.sum())
    return df[~dup]


def indicador_mensual_popayan(filas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(filas)
    mes = df["mes"].str.strip().str.lower().map(MESES)
    out = pd.DataFrame({
        "especialidad": df["nombre_del_indicador"].map(desde_indicador),
        "periodo": _fecha(_num(df["a_o"]), mes),
        "granularidad": "mes",
        # Supuesto por confirmar: la fuente no aclara la definición; se asume la estándar (desde la solicitud).
        "definicion": "solicitud",
        "dias_espera": _num(df["resultado"]),
        "citas": _num(df["denominador"]),
    })
    return _descartar_duplicados(out.dropna(subset=["dias_espera"]), ["especialidad", "periodo"], "5wj9-wrmj")


def indicador_mensual_neiva(filas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(filas)
    texto = df["indicador_citas_medicas"].str.lower()
    definicion = pd.Series(None, index=df.index, dtype="object")
    definicion[texto.str.contains("para la cual") | texto.str.contains(r"\(3\.3\)")] = "fecha_deseada"
    definicion[texto.str.contains("en que se solicita") | texto.str.contains(r"\(3\.2\)")] = "solicitud"
    _avisar("2hbw-r639", "indicador no reconocido: se descarta", definicion.isna().sum())
    out = pd.DataFrame({
        "especialidad": TODAS,
        "periodo": _fecha(_num(df["a_o"]), _num(df["mes"].str.extract(r"(\d+)")[0])),
        "granularidad": "mes",
        "definicion": definicion,
        "dias_espera": _num(df["resultado"]),
        "citas": _num(df["denominador"]),
    }).dropna(subset=["definicion", "dias_espera"])
    return _descartar_duplicados(out, ["periodo", "definicion"], "2hbw-r639")


def indicador_trimestral_colon(filas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(filas)
    romano = df["periodo"].str.extract(r"^\s*(IV|I{1,3})\s+TRIMESTRE", expand=False)
    denominador = _num(df["denominador"])
    validas = romano.notna() & (denominador > 0)
    _avisar("dt6u-2gkm", "fila anual (VIGENCIA) o con denominador 0: se descarta", (~validas).sum())
    df, romano, denominador = df[validas], romano[validas], denominador[validas]
    out = pd.DataFrame({
        # Se une por nombre: el código del indicador cambia de especialidad entre periodos.
        "especialidad": df["nombre_indicador"].map(desde_indicador),
        "periodo": _fecha(_num(df["anio"]), romano.map(TRIMESTRES)),
        "granularidad": "trimestre",
        "definicion": "solicitud",  # supuesto por confirmar, igual que en Popayán
        "dias_espera": _num(df["resultado_dias"]),
        "citas": denominador,
    })
    return _descartar_duplicados(out.dropna(subset=["dias_espera"]), ["especialidad", "periodo"], "dt6u-2gkm")


def trimestral_bogota(filas: list[dict], area: str) -> pd.DataFrame:
    """CSV del portal de Bogotá: una fila por área (subred), trimestre y especialidad, sin número de citas."""
    df = pd.DataFrame(filas)
    df.columns = [sin_tildes(c) for c in df.columns]  # "Año" y "Días" vienen con tilde
    df = df[df["area"].map(lambda v: sin_tildes(str(v)).replace(" ", "")) == area.replace(" ", "")]
    romano = df["periodo"].str.extract(r"^\s*(IV|I{1,3})\s+Trim", expand=False)
    dias = _num(df["dias"].astype(str).str.replace(",", ".", regex=False))
    validas = romano.notna() & dias.notna()
    _avisar("8fpf-y7z5", f"{area}: fila sin días o con periodo no reconocido: se descarta", (~validas).sum())
    df, romano, dias = df[validas], romano[validas], dias[validas]
    out = pd.DataFrame({
        "especialidad": df["especialidad"].map(normalizar),
        "periodo": _fecha(_num(df["ano"]), romano.map(TRIMESTRES)),
        "granularidad": "trimestre",
        # El metadato de Bogotá define la espera desde la solicitud, en días calendario.
        "definicion": "solicitud",
        "dias_espera": dias,
        "citas": pd.NA,
    })
    return _descartar_duplicados(out, ["especialidad", "periodo"], "8fpf-y7z5")


def semestral_neiva_res256(filas: list[dict]) -> pd.DataFrame:
    """Res. 256 de Neiva: formato largo, con el numerador y el denominador de cada especialidad en filas aparte.

    "Sumatoria de la diferencia de días calendario entre la fecha en la que se asignó la cita de X de primera
    vez y la fecha en la cual el usuario la solicitó" / "Número total de citas de X de primera vez asignadas".
    La fuente no publica el resultado: se calcula numerador / denominador.
    """
    df = pd.DataFrame(filas)
    texto = df["indicador_de_calidad"].astype(str)
    df["esp"] = texto.str.extract(r"citas? de (.+?) de primera vez", flags=re.IGNORECASE)[0]
    df["parte"] = None
    df.loc[texto.str.match(r"\s*sumatoria", case=False), "parte"] = "dias"
    df.loc[texto.str.match(r"\s*n[uú]mero total de citas", case=False), "parte"] = "citas"
    df["sem"] = df["semestre"].str.extract(r"^\s*(II|I)\s+SEMESTRE", flags=re.IGNORECASE, expand=False).str.upper()
    df = df.dropna(subset=["esp", "parte", "sem"])
    # El numerador dice "Medicina Interna" y el denominador "Medicina interna": se unen por el nombre normalizado.
    df["especialidad"] = df["esp"].map(normalizar)
    df["valor"] = _num(df["dato"])
    claves = ["especialidad", "a_o", "sem", "parte"]
    repetidas = df.duplicated(claves + ["valor"])
    _avisar("jxjp-6542", "fila repetida idéntica en la fuente: se deja una", repetidas.sum())
    df = _descartar_duplicados(df[~repetidas], claves, "jxjp-6542")
    ancho = df.pivot_table(index=["especialidad", "a_o", "sem"], columns="parte", values="valor", aggfunc="first").reset_index()
    if not {"dias", "citas"} <= set(ancho.columns):
        return pd.DataFrame(columns=COLUMNAS)
    ancho = ancho.dropna(subset=["dias", "citas"])
    ancho = ancho[ancho["citas"] > 0]
    return pd.DataFrame({
        "especialidad": ancho["especialidad"],
        "periodo": _fecha(_num(ancho["a_o"]), ancho["sem"].map(SEMESTRES)),
        "granularidad": "semestre",
        "definicion": "solicitud",  # explícita en la fuente: desde la solicitud, días calendario, primera vez
        "dias_espera": ancho["dias"] / ancho["citas"],
        "citas": ancho["citas"],
    })


def semestral_pereira(filas: list[dict]) -> pd.DataFrame:
    """E.S.E. Salud Pereira: indicadores de calidad por semestre; se usan los de oportunidad en consulta."""
    df = pd.DataFrame(filas)
    texto = df["descripcion_del_indicador"].astype(str).str.strip()
    df = df[texto.str.match(r"oportunidad en consulta de ", case=False) & df["tipo_de_medida"].str.strip().str.lower().eq("dias")]
    out = pd.DataFrame({
        "especialidad": df["descripcion_del_indicador"].str.strip()
        .str.replace(r"(?i)^oportunidad en consulta de ", "", regex=True).map(normalizar),
        "periodo": _fecha(_num(df["a_o"]), df["semestre"].astype(str).str.strip().map(SEMESTRES)),
        "granularidad": "semestre",
        "definicion": "solicitud",  # supuesto por confirmar: la fuente cita la Res. 256 pero no define la espera
        "dias_espera": _num(df["resultado"]),
        "citas": _num(df["denominador"]),
    })
    return _descartar_duplicados(out.dropna(subset=["dias_espera", "periodo"]), ["especialidad", "periodo"], "k226-53hw")


def microdato_aguadas(filas: list[dict]) -> pd.DataFrame:
    """Una fila por cita: se agrega a promedio mensual por servicio, según el mes de la solicitud."""
    df = pd.DataFrame(filas)
    df["dias"] = _num(df["dias_oportunidad"])
    df["periodo"] = pd.to_datetime(df["fecha_solicitud"]).dt.to_period("M").dt.to_timestamp().dt.date
    df["especialidad"] = df["servicio"].map(normalizar)
    out = (
        df.dropna(subset=["dias", "periodo"])
        .groupby(["especialidad", "periodo"], as_index=False)
        .agg(dias_espera=("dias", "mean"), citas=("dias", "size"))
    )
    out["granularidad"] = "mes"
    out["definicion"] = "solicitud"  # verificado: dias_oportunidad = fecha_asignacion - fecha_solicitud
    return out


def transformar(fuente: Fuente, filas: list[dict]) -> pd.DataFrame:
    funcion = globals()[fuente.transformador]
    df = funcion(filas, fuente.area) if fuente.area else funcion(filas)
    df["dias_espera"] = df["dias_espera"].astype(float).round(2)
    df["citas"] = df["citas"].astype("Int64")
    df, descartes = exclusiones.aplicar(df, fuente.dataset_id)
    for motivo, filas_descartadas in descartes:
        _avisar(fuente.dataset_id, f"excluido: {motivo}", filas_descartadas)
    return df[COLUMNAS].reset_index(drop=True)
