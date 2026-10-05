from datetime import date


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["db"] == "ok"


def test_hospitales_filtra_por_depto_sin_mayusculas(client):
    r = client.get("/hospitales", params={"depto": "HUILA"})
    assert [h["nombre"] for h in r.json()] == ["Hospital B"]


def test_oportunidad_filtra_por_especialidad_parcial(client):
    r = client.get("/oportunidad", params={"especialidad": "gine"})
    cuerpo = r.json()
    assert cuerpo["total"] == 2
    assert {i["hospital"] for i in cuerpo["items"]} == {"Hospital A", "Hospital B"}


def test_oportunidad_combina_filtros(client):
    r = client.get("/oportunidad", params={"especialidad": "gine", "depto": "cauca"})
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["dias_espera"] == 12.5


def test_oportunidad_paginacion(client):
    r = client.get("/oportunidad", params={"limit": 1, "offset": 1})
    cuerpo = r.json()
    assert cuerpo["total"] == 3 and len(cuerpo["items"]) == 1


def test_oportunidad_rechaza_limit_invalido(client):
    assert client.get("/oportunidad", params={"limit": 0}).status_code == 422


def test_estado_reporta_volumen_y_metricas(client):
    client.get("/health")
    e = client.get("/estado").json()
    assert e["hospitales"] == 2 and e["registros"] == 3
    assert e["ultima_carga_etl"] is None
    assert e["metricas"]["peticiones"] >= 1


def test_landing(client):
    r = client.get("/")
    assert r.status_code == 200 and "oportunidad de citas" in r.text


def test_oportunidad_filtra_por_definicion(client):
    items = client.get("/oportunidad", params={"definicion": "fecha_deseada"}).json()["items"]
    assert [i["hospital"] for i in items] == ["Hospital B"]
    assert client.get("/oportunidad", params={"definicion": "otra"}).status_code == 422


def test_tipo_de_unidad_en_respuestas(client):
    assert {h["tipo"] for h in client.get("/hospitales").json()} == {"hospital"}
    assert client.get("/oportunidad", params={"limit": 1}).json()["items"][0]["tipo"] == "hospital"


def _agregar_ips(client):
    import app.db as db
    from app.models import Hospital, Oportunidad
    with db.SessionLocal() as s:
        h = Hospital(nombre="IPS Prueba", tipo="ips", departamento="Antioquia", municipio="Medellín", dataset_id="x3", fuente_url="u3")
        s.add(h)
        s.flush()
        s.add(Oportunidad(hospital_id=h.id, especialidad="Odontología", periodo=date(2021, 1, 1), granularidad="trimestre",
                          definicion="solicitud", dias_espera=1.5, citas=30, dataset_id="x3"))
        s.commit()


def test_hospitales_filtra_por_tipo_y_municipio_y_pagina(client):
    _agregar_ips(client)
    assert [h["nombre"] for h in client.get("/hospitales", params={"tipo": "ips"}).json()] == ["IPS Prueba"]
    assert [h["nombre"] for h in client.get("/hospitales", params={"municipio": "MEDELLÍN"}).json()] == ["IPS Prueba"]
    assert [h["nombre"] for h in client.get("/hospitales", params={"limit": 1, "offset": 1}).json()] == ["Hospital B"]
    assert client.get("/hospitales", params={"limit": 1001}).status_code == 422
    assert client.get("/hospitales", params={"tipo": "otro"}).status_code == 422


def test_oportunidad_filtra_por_tipo_y_municipio(client):
    _agregar_ips(client)
    ips = client.get("/oportunidad", params={"tipo": "ips"}).json()
    assert ips["total"] == 1 and ips["items"][0]["tipo"] == "ips"
    assert client.get("/oportunidad", params={"municipio": "neiva"}).json()["total"] == 1
    assert client.get("/oportunidad", params={"tipo": "hospital"}).json()["total"] == 3
