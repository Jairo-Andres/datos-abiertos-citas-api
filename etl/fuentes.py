"""Fuentes que usa el ETL. Ver docs/fuentes.md para el detalle, las licencias y lo que se descartó."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    dataset_id: str
    hospital: str  # nombre de la unidad: un hospital, una subred o una red
    departamento: str
    municipio: str
    transformador: str  # nombre de la función en etl/transformar.py
    tipo: str = "hospital"  # "hospital" | "subred" | "red" (agrupan varias sedes) | "ips" (Clicsalud)
    formato: str = "socrata"  # "socrata" (datos.gov.co) | "ckan_bogota" (datosabiertos.bogota.gov.co)
    area: str | None = None  # para fuentes que traen varias unidades en el mismo archivo
    # False cuando la unidad ya tiene otra fuente principal: así no se cambia el enlace de origen de la unidad.
    principal: bool = True
    # True cuando el archivo trae muchas unidades y el transformador devuelve sus columnas (Clicsalud).
    multiunidad: bool = False
    filtro: str | None = None  # $where de SoQL para descargar solo las filas útiles

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


NEIVA = "E.S.E. Hospital Universitario Hernando Moncaleano Perdomo"

FUENTES = [
    Fuente("5wj9-wrmj", "E.S.E. Hospital Susana López de Valencia", "Cauca", "Popayán", "indicador_mensual_popayan"),
    Fuente("mq52-ekyw", "E.S.E. Hospital San José de Aguadas", "Caldas", "Aguadas", "microdato_aguadas"),
    Fuente("2hbw-r639", NEIVA, "Huila", "Neiva", "indicador_mensual_neiva"),
    # Mismo hospital, otra publicación: indicadores de la Res. 256 de 2016, por semestre y especialidad.
    Fuente("jxjp-6542", NEIVA, "Huila", "Neiva", "semestral_neiva_res256", principal=False),
    Fuente("dt6u-2gkm", "E.S.E. Hospital Pío XII de Colón", "Putumayo", "Colón", "indicador_trimestral_colon"),
    # Red municipal: 3 hospitales y 21 centros y puestos de salud (portafolio wyej-f7s7 en datos.gov.co).
    Fuente("k226-53hw", "E.S.E. Salud Pereira", "Risaralda", "Pereira", "semestral_pereira", tipo="red"),
    # La red pública de Bogotá publica por subred, no por hospital. La fila "Distrito" es el agregado
    # de las cuatro y no se carga para no contar dos veces.
    _subred("centro oriente", "Centro Oriente"),
    _subred("norte", "Norte"),
    _subred("sur", "Sur"),
    _subred("suroccidente", "Sur Occidente"),
]

# Fuente agregada del Ministerio de Salud: miles de IPS públicas y privadas, histórica (2016 a 2021-T3).
CLICSALUD = Fuente(
    "thui-g47e", "Clicsalud - MinSalud", "", "", "clicsalud_ips", tipo="ips", multiunidad=True,
    filtro="nomcategorias = 'TIEMPOS DE ESPERA' AND nomunidad = 'DÍAS'",
)
FUENTES.append(CLICSALUD)

# Revisado y descartado (ver docs/fuentes.md):
# k5bd-cym5 (HU de Santander): solo trae la fecha de la cita cumplida; sin fecha de solicitud no hay
# forma de calcular la espera.
