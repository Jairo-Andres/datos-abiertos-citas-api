"""Datasets de datos.gov.co que usa el ETL. Ver docs/fuentes.md para el detalle y las licencias."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    dataset_id: str
    hospital: str
    departamento: str
    municipio: str
    transformador: str  # nombre de la función en etl/transformar.py

    @property
    def url(self) -> str:
        return f"https://www.datos.gov.co/d/{self.dataset_id}"


FUENTES = [
    Fuente("5wj9-wrmj", "E.S.E. Hospital Susana López de Valencia", "Cauca", "Popayán", "indicador_mensual_popayan"),
    Fuente("mq52-ekyw", "E.S.E. Hospital San José de Aguadas", "Caldas", "Aguadas", "microdato_aguadas"),
    Fuente("2hbw-r639", "E.S.E. Hospital Universitario Hernando Moncaleano Perdomo", "Huila", "Neiva", "indicador_mensual_neiva"),
    Fuente("dt6u-2gkm", "E.S.E. Hospital Pío XII de Colón", "Putumayo", "Colón", "indicador_trimestral_colon"),
]

# Revisados y descartados por ahora (ver docs/fuentes.md):
# k5bd-cym5 (HU de Santander): no trae tiempo de espera, solo la fecha de la cita cumplida.
# 8fpf-y7z5 (red pública de Bogotá): en datos.gov.co es solo un enlace al portal de Bogotá.
