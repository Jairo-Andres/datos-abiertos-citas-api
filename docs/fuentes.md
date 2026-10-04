# Fuentes de datos

Todas vienen de [datos.gov.co](https://www.datos.gov.co) y corresponden a los indicadores de oportunidad de la Resolución 1552 de 2013, que cada hospital publica por su cuenta. No existe un consolidado nacional verificado: por eso este proyecto los unifica.

| Dataset | Hospital | Periodo | Formato original | Licencia |
|---|---|---|---|---|
| [5wj9-wrmj](https://www.datos.gov.co/d/5wj9-wrmj) | E.S.E. Hospital Susana López de Valencia (Popayán, Cauca) | ene-2022 a mar-2026, mensual | promedio mensual por especialidad | CC BY-SA 4.0 |
| [mq52-ekyw](https://www.datos.gov.co/d/mq52-ekyw) | E.S.E. Hospital San José de Aguadas (Caldas) | ene a jun-2026 | una fila por cita; se agrega a promedio mensual | CC BY-SA 4.0 |
| [2hbw-r639](https://www.datos.gov.co/d/2hbw-r639) | E.S.E. Hospital Universitario Hernando Moncaleano Perdomo (Neiva, Huila) | ene-2018 a dic-2024, mensual | promedio mensual de todo el hospital, sin especialidad | CC BY-SA 4.0 |
| [dt6u-2gkm](https://www.datos.gov.co/d/dt6u-2gkm) | E.S.E. Hospital Pío XII de Colón (Putumayo) | 2021-T1 a 2026-T2, trimestral | promedio trimestral por especialidad | CC BY-SA 4.0 |

Revisados y no usados por ahora:

- [k5bd-cym5](https://www.datos.gov.co/d/k5bd-cym5), Hospital Universitario de Santander: trae la fecha de cada cita cumplida, pero no la fecha de solicitud ni el tiempo de espera, así que no permite calcular oportunidad.
- [8fpf-y7z5](https://www.datos.gov.co/d/8fpf-y7z5), red pública de Bogotá: en datos.gov.co es solo un enlace al portal de datos abiertos de Bogotá (CC BY 4.0).

## Decisiones y supuestos

- **Dos definiciones de espera.** La resolución mide la espera desde la fecha en que se pide la cita (`solicitud`) y desde la fecha para la cual el paciente la pidió (`fecha_deseada`). Neiva publica ambas; las demás fuentes no lo aclaran y se asume `solicitud` (**por confirmar**). En Aguadas está verificado: los días coinciden con asignación menos solicitud en el 100 % de las filas.
- **Granularidad mixta.** Colón publica por trimestre y las demás por mes. Cada registro dice su `granularidad`; no se reparten trimestres en meses.
- **Valor publicado.** Se usa el resultado que publica el hospital, aunque a veces no coincide exactamente con numerador/denominador (redondeo en Popayán, hasta 2,9 días de diferencia en Colón).
- **Neiva 2020.** De enero a junio de 2020 cada mes aparece dos veces con los valores de los dos indicadores intercambiados. Como no hay forma de saber cuál es el correcto, esos meses se descartan. Desde mediados de 2020 los valores de los dos indicadores parecen invertidos respecto a 2018 (**por confirmar** con el hospital); se publican tal como vienen.
- **Colón.** Se descartan las filas anuales (`VIGENCIA`) y las de denominador 0. Las especialidades se unen por nombre, porque el código del indicador cambia de especialidad entre periodos. Falta el primer trimestre de 2024 en la fuente.
- **Privacidad.** Aguadas publica una fila por cita con sexo, régimen y EPS. El ETL solo guarda promedios mensuales por servicio; ningún dato por paciente llega a la base ni a la API.

## Licencia y atribución

Los datos se redistribuyen bajo CC BY-SA 4.0, con atribución a cada hospital y a datos.gov.co. El código del repositorio tiene su propia licencia (ver `LICENSE`).
