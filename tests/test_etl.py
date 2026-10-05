"""Pruebas del ETL con filas que imitan el formato real de cada fuente (valores como texto, igual que Socrata)."""

from datetime import date

from etl.especialidades import TODAS, desde_indicador, normalizar
from etl.fuentes import FUENTES
from etl.transformar import microdato_aguadas, transformar

FUENTE = {f.transformador if not f.area else f.area: f for f in FUENTES}


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
    df = transformar(FUENTE["indicador_mensual_popayan"], filas)
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
    df = transformar(FUENTE["indicador_mensual_neiva"], filas)
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
    df = transformar(FUENTE["indicador_trimestral_colon"], filas)
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
    # Se prueba la agregación sola: con tan pocas citas, transformar() las excluiría por el mínimo.
    df = microdato_aguadas(filas).sort_values(["periodo", "especialidad"])
    assert list(zip(df["especialidad"], df["periodo"], df["dias_espera"], df["citas"])) == [
        ("Medicina general", date(2026, 1, 1), 1.5, 2),
        ("Odontología", date(2026, 1, 1), 1.5, 2),
        ("Medicina general", date(2026, 2, 1), 4.0, 1),
    ]
    # El microdato trae sexo y régimen; el resultado no debe arrastrar datos por paciente.
    assert "sexo" not in df.columns and "regimen" not in df.columns


def test_bogota_separa_subredes_y_descarta_distrito_y_vacios():
    def fila(area, periodo, anio, esp, dias):
        return {"Area": area, "Periodo": periodo, "Año": anio, "Especialidad": esp, "Días": dias}

    filas = [
        fila("Norte", "I Trim", "2021", "Cardiología", "7,09"),
        fila("Norte", "II Trim", "2025", "Urología", None),
        fila("Suroccidente", "IV Trim", "2024", "Ortopedia", "4,87"),
        fila("Distrito", "I Trim", "2021", "Cardiología", "6,00"),
    ]
    norte = transformar(FUENTE["norte"], filas)
    assert list(zip(norte["especialidad"], norte["periodo"], norte["dias_espera"])) == [("Cardiología", date(2021, 1, 1), 7.09)]
    assert norte["citas"].isna().all() and set(norte["granularidad"]) == {"trimestre"}
    sur_occ = transformar(FUENTE["suroccidente"], filas)
    assert list(sur_occ["periodo"]) == [date(2024, 10, 1)]


def test_exclusiones_neiva_y_minimo_de_citas():
    def fila(anio, mes, ind, num, den, res):
        texto = {"3.2": "según fecha en que se solicita la cita (3.2)/(3.1)",
                 "3.3": "según fecha para la cual se solicita la cita (3.3)/(3.1)"}[ind]
        return {"a_o": anio, "mes": mes, "indicador_citas_medicas": texto, "numerador": num, "denominador": den, "resultado": res}

    filas = [
        fila("2021", "3M", "3.2", "1000", "900", "1.1"),     # etiquetas invertidas jul-2020 a dic-2021
        fila("2023", "10M", "3.2", "137066", "97794", "1.4"),  # error de digitación
        fila("2023", "10M", "3.3", "50000", "9794", "5.1"),
        fila("2023", "11M", "3.2", "40", "5", "8.0"),          # menos de 10 citas
    ]
    df = transformar(FUENTE["indicador_mensual_neiva"], filas)
    assert list(zip(df["periodo"], df["definicion"])) == [(date(2023, 10, 1), "fecha_deseada")]


def test_exclusiones_colon():
    def fila(periodo, anio, esp, den, res):
        return {"periodo": periodo, "anio": anio, "nombre_indicador": f"Oportunidad de cita de {esp}",
                "numerador": "1", "denominador": den, "resultado_dias": res}

    filas = [
        fila("IV TRIMESTRE", "2021", "Psiquiatría", "24156", "2"),
        fila("IV TRIMESTRE", "2021", "Ginecología", "961", "2"),
        fila("IV TRIMESTRE", "2021", "Pediatría", "400", "3"),
        fila("IV TRIMESTRE", "2023", "Pediatría", "2000", "3"),
        fila("I TRIMESTRE", "2022", "Psiquiatría", "1305", "42"),
    ]
    df = transformar(FUENTE["indicador_trimestral_colon"], filas)
    assert sorted(zip(df["especialidad"], df["periodo"])) == [
        ("Pediatría", date(2021, 10, 1)),
        ("Psiquiatría", date(2022, 1, 1)),
    ]


def test_neiva_res256_une_numerador_y_denominador_por_semestre():
    def fila(anio, sem, texto, dato):
        return {"a_o": anio, "semestre": sem, "indicador_de_calidad": texto, "dato": dato}

    suma = ("Sumatoria de la diferencia de días calendario entre la fecha en la que se asignó la cita de {} de primera vez "
            "y la fecha en la cual el usuario la solicitó.")
    total = "Número total de citas de {} de primera vez asignadas."
    filas = [
        fila("2016", "I SEMESTRE", suma.format("Medicina Interna"), "21618"),
        fila("2016", "I SEMESTRE", total.format("Medicina interna"), "2115"),
        fila("2016", "II SEMESTRE", suma.format("Pediatría"), "6545"),
        fila("2016", "II SEMESTRE", total.format("Pediatría"), "1587"),
        fila("2016", "II SEMESTRE", total.format("Pediatría"), "1587"),  # repetida idéntica: se deja una
        # 2020-I: Ginecología aparece dos veces con valores distintos; no se sabe cuál es la buena
        fila("2020", "I SEMESTRE", suma.format("Ginecología"), "120"),
        fila("2020", "I SEMESTRE", total.format("Ginecología"), "37"),
        fila("2020", "I SEMESTRE", suma.format("Ginecología"), "998"),
        fila("2020", "I SEMESTRE", total.format("Ginecología"), "173"),
        fila("2020", "I SEMESTRE", "Número total de pacientes hospitalizados que sufren caídas en el periodo.", "39"),
    ]
    df = transformar(FUENTE["semestral_neiva_res256"], filas).sort_values("periodo")
    assert list(zip(df["especialidad"], df["periodo"], df["dias_espera"], df["citas"])) == [
        ("Medicina interna", date(2016, 1, 1), 10.22, 2115),
        ("Pediatría", date(2016, 7, 1), 4.12, 1587),
    ]
    assert set(df["granularidad"]) == {"semestre"} and set(df["definicion"]) == {"solicitud"}


def test_pereira_semestral_toma_solo_oportunidad_en_consulta():
    def fila(anio, sem, desc, num, den, res, medida="Dias"):
        return {"a_o": anio, "semestre": sem, "descripcion_del_indicador": desc, "numerador": num,
                "denominador": den, "resultado": res, "tipo_de_medida": medida}

    filas = [
        fila("2026", "1", "Oportunidad en Consulta de Medicina General", "37246", "26518", "1.40"),
        fila("2025", "2", "Oportunidad en Consulta de odontología General", "15862", "7806", "2.03"),
        fila("2026", "1", "Oportunidad en Imagenología", "2246", "1718", "1.31"),
        fila("2026", "1", "Oportunidad en la Atención de Urgencias Triage II", "79259", "3381", "23.44", "Minutos"),
    ]
    df = transformar(FUENTE["semestral_pereira"], filas).sort_values("periodo")
    assert list(zip(df["especialidad"], df["periodo"], df["dias_espera"], df["citas"])) == [
        ("Odontología", date(2025, 7, 1), 2.03, 7806),
        ("Medicina general", date(2026, 1, 1), 1.4, 26518),
    ]
    assert set(df["granularidad"]) == {"semestre"}


def test_clicsalud_unidades_periodos_y_limpieza():
    def fila(ips, mun, cod, esp, periodo, num, den, res, depto="Antioquia"):
        return {"coddepartamento": "5", "departamento": depto, "codmunicipio": cod, "municipio": mun, "idips": "1.30E+11",
                "ips": ips, "nomcategorias": "TIEMPOS DE ESPERA", "nomservicio": "CONSULTAS", "nomespecifique": esp,
                "nomindicador": "Tiempo promedio de espera", "numerador": num, "denominador": den, "resultado": res,
                "nomunidad": "DÍAS", "nomfuente": "MinSalud", "periodo": periodo}

    filas = [
        fila("IPS  Uno ", "Medellín", "5001", "MÉDICO GENERAL", "20190630", "300", "100", "3"),
        fila("IPS UNO", "Medellín", "5001", "MÉDICO GENERAL", "20191231", "200", "100", "2"),  # mismo nombre normalizado
        fila("IPS Dos", "Medellín", "5001", "ODONTOLOGÍA", "20200930", "150", "100", "1.5"),
        fila("IPS Dos", "Envigado", "5266", "ODONTOLOGÍA", "20200331", "100", "50", "2"),   # se repite en otro municipio
        fila("Total", "Total", "0", "MÉDICO GENERAL", "20190630", "9", "3", "3"),          # total departamental
        fila("IPS Tres", "Bogotá, D.C.", "11001", "MÉDICO GENERAL", "20210331", "200000", "100", "2000",
             depto="Bogotá, D.C."),                                                       # imposible: más de 365 días
        fila("IPS Cuatro", "Medellín", "5001", "MÉDICO GENERAL", "20190630", "20", "5", "4"),  # menos de 10 citas
        fila("IPS Cinco", "Bogotá, D.C.", "11001", "ODONTOLOGÍA", "20210630", "120", "60", "2", depto="Bogotá, D.C."),
    ]
    df = transformar(FUENTE["clicsalud_ips"], filas).sort_values(["unidad", "periodo"])
    assert list(zip(df["unidad"], df["municipio"], df["especialidad"], df["periodo"], df["granularidad"], df["dias_espera"])) == [
        ("IPS Cinco", "Bogotá", "Odontología", date(2021, 4, 1), "trimestre", 2.0),
        ("IPS Dos (Envigado)", "Envigado", "Odontología", date(2020, 1, 1), "trimestre", 2.0),
        ("IPS Dos (Medellín)", "Medellín", "Odontología", date(2020, 7, 1), "trimestre", 1.5),
        ("IPS Uno", "Medellín", "Medicina general", date(2019, 1, 1), "semestre", 3.0),
        ("IPS Uno", "Medellín", "Medicina general", date(2019, 7, 1), "semestre", 2.0),
    ]
    # "IPS  Uno " e "IPS UNO" son la misma IPS: se muestra la primera forma con que aparece.
    assert set(df["departamento"][df["municipio"].eq("Bogotá")]) == {"Bogotá D.C."}
