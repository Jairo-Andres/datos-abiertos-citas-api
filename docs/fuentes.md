# Fuentes de datos

Todas vienen de [datos.gov.co](https://www.datos.gov.co) y corresponden a los indicadores de oportunidad de la Resolución 1552 de 2013, que cada hospital publica por su cuenta. No existe un consolidado nacional verificado: por eso este proyecto los unifica.

| Dataset | Hospital | Periodo | Formato original | Licencia |
|---|---|---|---|---|
| [5wj9-wrmj](https://www.datos.gov.co/d/5wj9-wrmj) | E.S.E. Hospital Susana López de Valencia (Popayán, Cauca) | ene-2022 a mar-2026, mensual | promedio mensual por especialidad | CC BY-SA 4.0 |
| [mq52-ekyw](https://www.datos.gov.co/d/mq52-ekyw) | E.S.E. Hospital San José de Aguadas (Caldas) | ene a jun-2026 | una fila por cita; se agrega a promedio mensual | CC BY-SA 4.0 |
| [2hbw-r639](https://www.datos.gov.co/d/2hbw-r639) | E.S.E. Hospital Universitario Hernando Moncaleano Perdomo (Neiva, Huila) | ene-2018 a dic-2024, mensual | promedio mensual de todo el hospital, sin especialidad | CC BY-SA 4.0 |
| [jxjp-6542](https://www.datos.gov.co/d/jxjp-6542) | El mismo hospital de Neiva: indicadores de la Res. 256 de 2016 | 2016-S1 a 2024-S2, semestral | numerador y denominador por especialidad, en filas separadas | CC BY-SA 4.0 |
| [dt6u-2gkm](https://www.datos.gov.co/d/dt6u-2gkm) | E.S.E. Hospital Pío XII de Colón (Putumayo) | 2021-T1 a 2026-T2, trimestral | promedio trimestral por especialidad | CC BY-SA 4.0 |
| [k226-53hw](https://www.datos.gov.co/d/k226-53hw) | E.S.E. Salud Pereira (Risaralda), red municipal | 2015-S1 a 2026-S1, semestral | indicadores de calidad de la Res. 256; se usan los de medicina general y odontología | CC BY-SA 4.0 |
| [8fpf-y7z5](https://www.datos.gov.co/d/8fpf-y7z5) → [portal de Bogotá](https://datosabiertos.bogota.gov.co/dataset/oportunidad-de-la-atencion-ambulatoria-red-publica-de-bogota-d-c) | Las 4 subredes de la red pública de Bogotá (Centro Oriente, Norte, Sur y Sur Occidente) | 2021-T1 a 2025-T1, trimestral (2025-T2 a T4 vienen vacíos en la fuente) | promedio trimestral por subred y especialidad complementaria, sin número de citas | CC BY 4.0 |

### Neiva por especialidad (Res. 256)

El Hospital Universitario de Neiva publica dos datasets. El mensual (`2hbw-r639`) es el promedio de todo el hospital; el de la Res. 256 (`jxjp-6542`) trae, por semestre, el numerador y el denominador de cinco especialidades: Ginecología, Obstetricia, Pediatría, Medicina interna y Cirugía general.

- Es la definición más explícita de todas las fuentes: "Sumatoria de la diferencia de días calendario entre la fecha en la que se asignó la cita de [especialidad] de primera vez y la fecha en la cual el usuario la solicitó" dividida por el "Número total de citas de [especialidad] de primera vez asignadas". Es decir: desde la solicitud, en días calendario y solo citas de primera vez.
- La fuente no publica el resultado: el ETL calcula numerador ÷ denominador.
- En la API es la misma unidad que el Neiva mensual. Los registros semestrales se distinguen por `granularidad = "semestre"` y por la especialidad.

### Salud Pereira

La E.S.E. Salud Pereira es la red pública municipal de Pereira: según su propio portafolio en datos.gov.co ([wyej-f7s7](https://www.datos.gov.co/d/wyej-f7s7)) tiene 24 sedes (Hospital de Kennedy, Hospital del Centro, Hospital de San Joaquín y 21 centros y puestos de salud). Por eso en la API es una unidad con `tipo = "red"`.

- De sus indicadores de calidad se usan "Oportunidad en Consulta de Medicina General" y "Oportunidad en Consulta de odontología General", en días, con numerador y denominador, por semestre.
- La descripción enmarca los indicadores en la Res. 0256 de 2016 pero no define la espera. Se asume `solicitud` (**por confirmar**).

### Bogotá

En datos.gov.co el registro `8fpf-y7z5` es solo un enlace: los datos están en el portal de datos abiertos de Bogotá, publicados por la Secretaría Distrital de Salud como un CSV (Latin-1, separado por punto y coma, coma decimal). El ETL lo descarga por la API CKAN del portal.

- **No es un hospital sino una subred**, que agrupa varias sedes. En la API cada subred es una unidad con `tipo = "subred"`.
- La fila "Distrito" es el agregado de las cuatro subredes y **no se carga**, para no contar dos veces.
- Trae 7 especialidades complementarias (Cardiología, Cirugía general, Fisiatría, Oftalmología, Ortopedia, Otorrinolaringología y Urología). Solo Cirugía general coincide con otros hospitales.
- **No publica el número de citas**, así que no se puede ponderar ni aplicar el mínimo de citas.
- Las filas sin días se descartan: 2025-T2 a T4 llegan vacíos en la fuente y en Sur Occidente falta una especialidad por trimestre entre 2024-T2 y 2025-T1.
- El metadato define la espera desde la solicitud en días calendario, pero describe otra versión del dataset (especialidades básicas, semestral, desde 2016). Se asume que la fórmula es la misma (**por confirmar**).

### Revisado y descartado

[k5bd-cym5](https://www.datos.gov.co/d/k5bd-cym5), Hospital Universitario de Santander. Se descargaron las 236.023 filas y se revisaron los metadatos:

- Cada fila es una cita **cumplida** con su fecha (día, mes y año). No hay fecha de solicitud ni de asignación, ni ninguna columna de espera, y las columnas no tienen descripción. **Sin la fecha de solicitud no hay forma de calcular la oportunidad**, así que no entra en la tabla de espera.
- La entidad no publica otro dataset con tiempos de espera en datos.gov.co (sus otros datasets son urgencias, egresos, nacimientos y documentos de transparencia).
- Lo único que permitiría es contar citas cumplidas por especialidad y mes (2020–2025), que es otra medida. Además trae edad, sexo, tipo de documento y asegurador de cada paciente, así que solo podría publicarse agregado.

## Decisiones y supuestos

- **Dos definiciones de espera.** La resolución mide la espera desde la fecha en que se pide la cita (`solicitud`) y desde la fecha para la cual el paciente la pidió (`fecha_deseada`). Neiva publica ambas; las demás fuentes no lo aclaran y se asume `solicitud` (**por confirmar**). En Aguadas está verificado: los días coinciden con asignación menos solicitud en el 100 % de las filas.
- **Granularidad mixta.** Hay fuentes mensuales (Popayán, Aguadas, Neiva mensual), trimestrales (Colón, Bogotá) y semestrales (Neiva por especialidad, Pereira). Cada registro dice su `granularidad` y su `periodo` es el primer día del mes, del trimestre o del semestre (1 de enero o 1 de julio). No se reparten periodos largos en meses.
- **Valor publicado.** Se usa el resultado que publica el hospital, aunque a veces no coincide exactamente con numerador/denominador (redondeo en Popayán, hasta 2,9 días de diferencia en Colón).
- **Neiva 2020–2021.** De enero a junio de 2020 cada mes aparece dos veces con valores contradictorios, y de julio de 2020 a diciembre de 2021 los dos indicadores parecen tener las etiquetas invertidas. Esos 24 meses no se cargan. Ver [verificacion.md](verificacion.md).
- **Colón.** Se descartan las filas anuales (`VIGENCIA`), las de denominador 0 y las de errores evidentes (2021-T4 en cuatro especialidades y todo 2023-T4). Las especialidades se unen por nombre, porque el código del indicador cambia de especialidad entre periodos. Falta el primer trimestre de 2024 en la fuente.
- **Neiva Res. 256, 2020-S1.** Ese semestre viene dos veces: cuatro especialidades con valores idénticos (se deja una copia) y Ginecología con valores distintos (37 citas y 120 días frente a 173 citas y 998 días), que no se carga.
- **Mínimo de citas.** No se publican periodos con menos de 10 citas.
- **Privacidad.** Aguadas publica una fila por cita con sexo, régimen y EPS. El ETL solo guarda promedios mensuales por servicio; ningún dato por paciente llega a la base ni a la API.

## Licencia y atribución

Los datos de datos.gov.co se redistribuyen bajo CC BY-SA 4.0 y los de Bogotá bajo CC BY 4.0, con atribución a cada hospital, a la Secretaría Distrital de Salud y a los portales de origen. El código del repositorio tiene su propia licencia (ver `LICENSE`).
