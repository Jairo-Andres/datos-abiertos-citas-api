"""Fuentes que usa el ETL. Ver docs/fuentes.md para el detalle, las licencias y lo que se descartó."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    dataset_id: str
    hospital: str  # nombre de la unidad: un hospital o una subred
    departamento: str
    municipio: str
    transformador: str  # nombre de la función en etl/transformar.py
    tipo: str = "hospital"  # "hospital" | "subred" (agrupa varias sedes)
    formato: str = "socrata"  # "socrata" (datos.gov.co) | "ckan_bogota" (datosabiertos.bogota.gov.co)
    area: str | None = None  # para fuentes que traen varias unidades en el mismo archivo

    @property
    def url(self) -> str:
        if self.formato == "ckan_bogota":
            return "https://datosabiertos.bogota.gov.co/dataset/oportunidad-de-la-atencion-ambulatoria-red-publica-de-bogota-d-c"
        return f"https://www.datos.gov.co/d/{self.dataset_id}"


def _subred(area: str, nombre: str) -> Fuente:
    return Fuente(
        "8fpf-y7z5", f"Subred Integrada de Servicios de Salud {nombre} E.S.E.", "Bogotá D.C.", "Bogotá",
        "trimestral_bogota", tipo="subred", formato="ckan_bogota", area=area,
    )


FUENTES = [
    Fuente("5wj9-wrmj", "E.S.E. Hospital Susana López de Valencia", "Cauca", "Popayán", "indicador_mensual_popayan"),
    Fuente("mq52-ekyw", "E.S.E. Hospital San José de Aguadas", "Caldas", "Aguadas", "microdato_aguadas"),
    Fuente("2hbw-r639", "E.S.E. Hospital Universitario Hernando Moncaleano Perdomo", "Huila", "Neiva", "indicador_mensual_neiva"),
    Fuente("dt6u-2gkm", "E.S.E. Hospital Pío XII de Colón", "Putumayo", "Colón", "indicador_trimestral_colon"),
    # La red pública de Bogotá publica por subred, no por hospital. La fila "Distrito" es el agregado
    # de las cuatro y no se carga para no contar dos veces.
    _subred("centro oriente", "Centro Oriente"),
    _subred("norte", "Norte"),
    _subred("sur", "Sur"),
    _subred("suroccidente", "Sur Occidente"),
]

# Revisado y descartado (ver docs/fuentes.md):
# k5bd-cym5 (HU de Santander): solo trae la fecha de la cita cumplida; sin fecha de solicitud no hay
# forma de calcular la espera.
