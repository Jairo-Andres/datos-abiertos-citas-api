from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Hospital(Base):
    __tablename__ = "hospitales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), unique=True)
    tipo: Mapped[str] = mapped_column(String(20), default="hospital", server_default="hospital")  # "hospital" | "subred"
    departamento: Mapped[str] = mapped_column(String(80), index=True)
    municipio: Mapped[str] = mapped_column(String(80))
    dataset_id: Mapped[str] = mapped_column(String(20))
    fuente_url: Mapped[str] = mapped_column(String(300))

    registros: Mapped[list["Oportunidad"]] = relationship(back_populates="hospital")


class Oportunidad(Base):
    """Un registro = días promedio de espera de un hospital, para una especialidad, en un periodo.

    Las fuentes publican con granularidad distinta (mes o trimestre) y con dos definiciones de
    espera de la Resolución 1552 de 2013: desde la fecha en que se pide la cita ("solicitud") o
    desde la fecha para la cual el paciente la pidió ("fecha_deseada").
    """

    __tablename__ = "oportunidad"
    __table_args__ = (UniqueConstraint("hospital_id", "especialidad", "periodo", "granularidad", "definicion"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitales.id"), index=True)
    especialidad: Mapped[str] = mapped_column(String(120), index=True)
    periodo: Mapped[date] = mapped_column(Date, index=True)  # primer día del mes o del trimestre
    granularidad: Mapped[str] = mapped_column(String(10))  # "mes" | "trimestre"
    definicion: Mapped[str] = mapped_column(String(20))  # "solicitud" | "fecha_deseada"
    dias_espera: Mapped[float] = mapped_column(Float)
    citas: Mapped[int | None] = mapped_column(Integer, nullable=True)  # citas usadas en el promedio, si la fuente lo da

    hospital: Mapped[Hospital] = relationship(back_populates="registros")


class CargaETL(Base):
    """Bitácora de cada ejecución del ETL, para el panel de estado."""

    __tablename__ = "cargas_etl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ejecutada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    filas: Mapped[int] = mapped_column(Integer)
    datasets_ok: Mapped[int] = mapped_column(Integer)
    datasets_error: Mapped[int] = mapped_column(Integer)
