from datetime import date

from pydantic import BaseModel, ConfigDict


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    departamento: str
    municipio: str
    fuente_url: str


class OportunidadOut(BaseModel):
    hospital: str
    departamento: str
    municipio: str
    especialidad: str
    periodo: date
    granularidad: str
    definicion: str
    dias_espera: float
    citas: int | None


class Pagina(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OportunidadOut]
