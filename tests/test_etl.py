"""Pruebas del ETL con filas que imitan el formato real de cada fuente (valores como texto, igual que Socrata)."""

from datetime import date

from etl.especialidades import TODAS, desde_indicador, normalizar
from etl.transformar import transformar


def test_normaliza_especialidades():
    assert desde_indicador("Tiempo promedio de espera para la asignación de cita de medicina interna") == "Medicina interna"
    assert desde_indicador("Oportunidad de cita de Enfermería") == "Enfermería"
    assert normalizar("CITA ODONTOLOGICA 20 MIN") == "Odontología"
    assert normalizar("CONSULTA 1RA VEZ - 1ra INFANCIA x MEDICO GENERAL") == "Medicina general"
    assert normalizar("Consulta ambulatoria de medicina general") == "Medicina general"


def test_popayan():
    filas = [
        {"a_o": "2022", "mes": "Enero", "nombre_del_indicador": "Tiempo promedio de espera para la asignación de cita de pediatría",
         "meta": "5", "numerador": "594", "denominador": "189", "resultado": "3.14"},
    ]
    df = transformar("indicador_mensual_popayan", filas)
    f = df.iloc[0]
    assert (f.especialidad, f.periodo, f.granularidad, f.dias_espera, f.citas) == ("Pediatría", date(2022, 1, 1), "mes", 3.14, 189)


def test_neiva_separa_definiciones_y_descarta_meses_duplicados():
    def fila(anio, mes, ind, res):
        texto = {"3.2": "Tiempo promedio de espera, según fecha en que se solicita la cita (3.2)/(3.1)",
                 "3.3": "Tiempo promedio de espera, según fecha para la cual se solicita la cita (3.3)/(3.1)"}[ind]
        return {"a_o": anio, "mes": mes, "indicador_citas_medicas": texto, "numerador": "1", "denominador": "10", "resultado": res}

    filas = [
        fila("2018", "1M", "3.2", "14.1"), fila("2018", "1M", "3.3", "3.3"),
        # 2020: el mismo mes aparece dos veces con valores intercambiados
        fila("2020", "1M", "3.2", "1.0"), fila("2020", "1M", "3.2", "7.0"),
    ]
    df = transformar("indicador_mensual_neiva", filas)
    assert set(df["especialidad"]) == {TODAS}
    assert sorted(zip(df["periodo"], df["definicion"], df["dias_espera"])) == [
        (date(2018, 1, 1), "fecha_deseada", 3.3),
        (date(2018, 1, 1), "solicitud", 14.1),
    ]


def test_colon_trimestral_descarta_vigencia_y_denominador_cero():
    base = {"anio": "2021", "codigo_indicador": "I.1552.1", "numerador": "128", "max_dias_espera": "6",
            "min_dias_espera": "0", "horas_promedio": "35"}
    filas = [
        {**base, "periodo": "III TRIMESTRE", "nombre_indicador": "Oportunidad de cita de Anestesiología", "denominador": "80", "resultado_dias": "2"},
        {**base, "periodo": "VIGENCIA", "nombre_indicador": "Oportunidad de cita de Anestesiología", "denominador": "300", "resultado_dias": "2"},
        {**base, "periodo": "I TRIMESTRE", "nombre_indicador": "Oportunidad de cita de Pediatría", "denominador": "0", "resultado_dias": "0"},
    ]
    df = transformar("indicador_trimestral_colon", filas)
    assert len(df) == 1
    f = df.iloc[0]
    assert (f.especialidad, f.periodo, f.granularidad, f.citas) == ("Anestesiología", date(2021, 7, 1), "trimestre", 80)


def test_aguadas_agrega_por_mes_y_servicio():
    def cita(fecha, servicio, dias):
        return {"a_o": "2026", "trimestre": "1", "sexo": "H", "regimen": "Subsidiado", "fecha_solicitud": f"{fecha}T00:00:00.000",
                "fecha_asignacion": f"{fecha}T00:00:00.000", "servicio": servicio, "dias_oportunidad": dias}

    filas = [
        cita("2026-01-02", "Consulta ambulatoria de medicina general", "0"),
        cita("2026-01-20", "Consulta ambulatoria de medicina general", "3"),
        cita("2026-01-21", "CITA ODONTOLOGICA 20 MIN", "1"),
        cita("2026-01-22", "CITA ODONTOLOGICA 40 MIN", "2"),
        cita("2026-02-01", "Consulta ambulatoria de medicina general", "4"),
    ]
    df = transformar("microdato_aguadas", filas).sort_values(["periodo", "especialidad"])
    assert list(zip(df["especialidad"], df["periodo"], df["dias_espera"], df["citas"])) == [
        ("Medicina general", date(2026, 1, 1), 1.5, 2),
        ("Odontología", date(2026, 1, 1), 1.5, 2),
        ("Medicina general", date(2026, 2, 1), 4.0, 1),
    ]
    # El microdato trae sexo y régimen; el resultado no debe arrastrar datos por paciente.
    assert "sexo" not in df.columns and "regimen" not in df.columns
