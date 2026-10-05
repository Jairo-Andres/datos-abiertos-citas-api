"""Normaliza los nombres de especialidad que cada hospital escribe a su manera."""

import re
import unicodedata

TODAS = "Todas las especialidades"

# clave sin tildes ni mayúsculas -> nombre canónico
_CANONICAS = {
    "anestesiologia": "Anestesiología",
    "cardiologia": "Cardiología",
    "fisiatria": "Fisiatría",
    "oftalmologia": "Oftalmología",
    "ortopedia": "Ortopedia",
    "otorrinolaringologia": "Otorrinolaringología",
    "urologia": "Urología",
    "cirugia general": "Cirugía general",
    "ecografia": "Ecografía",
    "enfermeria": "Enfermería",
    "fisioterapia": "Fisioterapia",
    "ginecologia": "Ginecología",
    "medicina general": "Medicina general",
    "medicina interna": "Medicina interna",
    "nutricion": "Nutrición",
    "nutricionista": "Nutrición",
    "obstetricia": "Obstetricia",
    "odontologia": "Odontología",
    "odontologia general": "Odontología",
    "pediatria": "Pediatría",
    "psicologia": "Psicología",
    "psiquiatria": "Psiquiatría",
    "radiologia e imagenes diagnosticas": "Radiología e imágenes diagnósticas",
}

# palabras clave para nombres largos de servicio (se prueban en orden)
_PISTAS = [
    ("odontolog", "Odontología"),
    ("medico general", "Medicina general"),
    ("medicina general", "Medicina general"),
]


def sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


def normalizar(nombre: str) -> str:
    clave = re.sub(r"\s+", " ", sin_tildes(nombre)).strip(" .")
    if clave in _CANONICAS:
        return _CANONICAS[clave]
    for pista, canonica in _PISTAS:
        if pista in clave:
            return canonica
    # Sin equivalencia conocida: se conserva con mayúscula inicial para revisarlo en el reporte del ETL.
    return clave[:1].upper() + clave[1:]


def desde_indicador(texto: str) -> str:
    """'Tiempo promedio de espera para la asignación de cita de Medicina Interna' -> 'Medicina interna'."""
    m = re.search(r"\bcita (?:de |en |con )?(?:la |el )?(.+)$", texto, flags=re.IGNORECASE)
    return normalizar(m.group(1) if m else texto)
