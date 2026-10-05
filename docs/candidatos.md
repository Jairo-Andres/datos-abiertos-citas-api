# Candidatos para ampliar la API (borrador)

Búsqueda hecha el 5 de octubre de 2026 en el catálogo de datos.gov.co (API de catálogo de Socrata: búsquedas por texto y recorrido completo de la categoría "Salud y Protección Social", 669 datasets) y en el portal CKAN de Bogotá. Para cada candidato se descargaron los metadatos y una muestra (en `data/raw/candidatos/`, que no se versiona). No se cambió código.

Estado: jxjp-6542 y k226-53hw ya están integrados en el ETL (5 de octubre de 2026). Clicsalud (thui-g47e): Jairo decidió incluirlo con todas las IPS; se integra en un cambio aparte. Facatativá, La Virginia y Sogamoso quedan fuera por ahora.

Clases: **A** = se integra con un transformador nuevo sencillo · **B** = se integra con trabajo o supuestos · **C** = no sirve para medir la espera.

## Resumen

| id | Entidad | Ciudad | Granularidad | Rango | Especialidad | Citas | Clase | Motivo |
|---|---|---|---|---|---|---|---|---|
| thui-g47e | MinSalud, Clicsalud (indicadores de calidad de IPS) | Todo el país: 952 municipios, unas 1.400 IPS | semestre (2016–2019), trimestre (2020–2021) | 2016-S1 a 2021-T3 | Solo medicina general y odontología | Sí (num/den) | **B** | La única fuente con las ciudades principales y la sabana. Pero termina en 2021, es casi todo IPS privadas y hay que limpiarla |
| jxjp-6542 | HU Hernando Moncaleano Perdomo | Neiva | semestre | 2016-S1 a 2024-S2 | Sí: Ginecología, Obstetricia, Pediatría, Medicina interna, Cirugía general | Sí (num/den) | **A, integrado** | Res. 256: desde la solicitud, días calendario, primera vez (explícito). Le agrega especialidades a Neiva |
| k226-53hw | E.S.E. Salud Pereira | Pereira | semestre | 2015-S1 a 2026-S1 | Medicina general y odontología | Sí (num/den) | **A, integrado** | Serie larga y actual de una ciudad principal |
| 2r4c-xrfz | Hospital San Pedro y San Pablo | La Virginia (Risaralda) | mes | ene a jun, **sin año** | Sí, 15 | Sí | **B** | No trae el año. Tiene dos esperas ("Espera 1" y "Espera 2") sin decir cuál es cuál |
| geiy-4gjn / 9fk3-4e6r / dvpc-mj2r | Hospital San Rafael de Facatativá | Facatativá (Cundinamarca) y sedes (Subachoque, Albán, Guayabal de Síquima) | trimestre | 2022-T1 a 2023-T2 | Medicina general, odontología, medicina interna | No | **B** | Tres versiones del mismo archivo en formato ancho, sin numerador ni denominador. Muchos 0 que pueden ser "sin servicio" |
| cgvt-kh9a | E.S.E. Salud Sogamoso | Sogamoso (Boyacá) | semestre (códigos 18/24) | 2017 a 2019 | Sí, P.3.1 a P.3.7 | Sí (num/den) | **B** | Definición explícita, pero el texto está mal codificado, es viejo y no se ha actualizado desde 2020 |
| vw9t-pugy | MinSalud, Clicsalud EPS | Nacional | semestre | 2016 en adelante | Medicina general y otras | No | **C** | Es por EPS (aseguradora), no por hospital |
| m8se-7v3b | Hospital Pío XII | Colón | trimestre | 2021 a 2026 | — | Sí | **C** | Res. 256 del mismo hospital que ya está cargado. Sirve solo para cruzar datos |
| 5k38-dew4 / b4p8-yp25 | HU San Jorge | Pereira | mes / anual | 2021 a 2022 | — | — | **C** | Producción y otros indicadores, sin tiempos de espera de citas |
| n3bh-hczp | Hospital de Guarne | Guarne (Antioquia) | mes | solo 2019 | — | — | **C** | Un solo año, formato ancho y sin actualizar |
| mac2-w53m / bz7r-3h5j | Hospital Militar Central | Bogotá | anual | 2018 a 2020 | Sí | Solo conteos | **C** | Cuenta citas asignadas; no trae espera |
| e2bt-r7a6 | Hospital Regional de San Gil | San Gil | anual | 2022 | Sí | Solo conteos | **C** | Igual: no trae espera |
| twnk-hika | Hospital de Puerto Boyacá | Puerto Boyacá | por cita | 2022 | Sí | — | **C** | Solo la fecha de la cita, sin fecha de solicitud. Trae fecha de nacimiento por paciente |
| g4vd-w4ip | Alcaldía de Bucaramanga | Bucaramanga | por atención | 2016 a 2021 | — | — | **C** | Urgencias por accidentes de tránsito, no citas. Además es microdato con datos personales |

En el portal de Bogotá (CKAN) no hay otro dataset de oportunidad de citas aparte del que ya usamos (subredes). Los otros resultados de "tiempo de espera" son el tiempo de viaje a un centro médico, los trasplantes y temas de movilidad.

## Detalle de los candidatos A y B

### thui-g47e: Clicsalud, indicadores de calidad de IPS (MinSalud)
- 301.240 filas en total. **56.359** son de "TIEMPOS DE ESPERA" en días: medicina general (31.805) y odontología general (24.554). Hay además 14.848 de triage 2, en minutos, que no son citas.
- Columnas: departamento, municipio (con código DANE), idips, ips, indicador, numerador, denominador, resultado y periodo (AAAAMMDD). El resultado es igual a numerador ÷ denominador en el 100 % de las filas.
- Licencia CC BY-SA 4.0. Actualizado el 26-05-2022; frecuencia declarada: anual. **Los datos llegan hasta 2021-T3.**
- **Cobertura** (IPS por nombre / filas):
  - Bogotá 628 / 4.441 · Medellín 256 / 1.997 · Cali 298 / 2.429 · Barranquilla 227 / 1.436 · Cartagena 156 / 1.098 · Bucaramanga 137 / 1.072
  - Cúcuta 110 / 882 · Pereira 91 / 691 · Manizales 78 / 676 · Ibagué 111 / 743 · Villavicencio 91 / 653 · Pasto 62 / 525 · Santa Marta 98 / 692 · Montería 109 / 676
  - Sabana y alrededores: Soacha 27 / 252 · Chía 37 / 298 · Zipaquirá 12 / 91 · Fusagasugá 32 / 279 · Facatativá 15 / 150 · Girardot 31 / 219 · Mosquera, Funza, Madrid, Cajicá, Sopó, Tenjo, Tabio y Tocancipá con menos de 100 filas cada uno
- **Problemas:**
  - El `idips` viene en notación científica (`1.30E+11`) en el 83 % de las filas, así que no sirve como llave. Hay que identificar cada IPS por nombre y municipio, y los nombres cambian entre periodos.
  - Mezcla IPS públicas y privadas. Las públicas reconocibles (ESE, subred, hospital, Metrosalud, MiRed) son pocas: unas 93 IPS y 1.026 filas en las ciudades objetivo. En Bogotá los hospitales públicos solo aparecen en 2016.
  - Trae filas de total departamental (`municipio = "Total"`, 1.002 filas) que no hay que cargar.
  - Tiene valores imposibles (máximo 10.417 días; 120 filas con más de 60 días) y 2.872 filas con menos de 10 citas.
  - La granularidad cambia: semestral hasta 2019 y trimestral en 2020–2021.
  - No dice la definición. Por la Res. 256 (P.3.1 y P.3.2) sería desde la solicitud, en días calendario y primera vez (**por confirmar**).
- **Decisión para Jairo:**
  - ¿Se incluyen IPS privadas? Hasta ahora el proyecto habla de "hospitales públicos".
  - ¿Vale la pena publicar datos que terminan en 2021?
  - Si se usa, propongo una tabla con `tipo = "ips"`, sin mezclarla con hospitales, más un filtro de valores imposibles y el mínimo de 10 citas.

### jxjp-6542: Neiva, indicadores de la Res. 256
- 418 filas, en formato largo. Cada indicador viene en dos filas: "Sumatoria de la diferencia de días calendario entre la fecha en la que se asignó la cita de X de primera vez y la fecha en la cual el usuario la solicitó" y "Número total de citas de X de primera vez asignadas".
- Especialidades: Ginecología, Obstetricia, Pediatría, Medicina interna y Cirugía general. Va de 2016-S1 a 2024-S2.
- 2020-S1 trae 44 filas en vez de 22: está duplicado y hay que revisarlo como en 2hbw-r639.
- Es la definición más explícita de todas las fuentes: desde la solicitud, en días calendario y solo primera vez.

### k226-53hw: E.S.E. Salud Pereira
- 159 filas con 7 indicadores. Los dos que sirven son "Oportunidad en Consulta de Medicina General" y "…de odontología General", en días, con numerador y denominador, por semestre de 2015-S1 a 2026-S1 (23 semestres cada uno).
- Ejemplo: 2026-S1, medicina general 37246 / 26518 = 1,40 días.
- Raro: odontología en 2020-S2 tiene solo 16 citas y en 2021-S1, 279 (por la pandemia). El mínimo de citas las filtra si hace falta.
- La descripción la enmarca en la Res. 0256 de 2016, pero no dice la definición de la espera (**por confirmar**).

### 2r4c-xrfz: La Virginia (Risaralda)
- 90 filas: 15 especialidades × 6 meses (enero a junio). **No hay columna de año.** Se publicó o actualizó el 03-11-2022; ¿será 2022? **Por confirmar**.
- Trae dos bloques ("Espera 1" / "Promedio espera 1" y "Espera 2" / "Promedio espera 2"), con el mismo número de citas. Probablemente son las dos definiciones de la circular, pero no dice cuál es cuál.

### Facatativá (geiy-4gjn, 9fk3-4e6r, dvpc-mj2r)
- Son tres publicaciones del mismo cuadro de la Res. 256 por sede (hospital y 6 centros o puestos), por trimestre, en columnas: 2022-T1 a 2022-T2 en uno y hasta 2023-T2 en otro. 9fk3-4e6r está en porcentaje en lugar de proporción.
- P.3.1 medicina general, P.3.2 odontología y P.3.3 medicina interna. Ejemplo: hospital, medicina general, 2023-T2: 2,97 días.
- No trae citas, así que no se puede aplicar el mínimo de citas. Los 0 en sedes sin el servicio no se distinguen de "espera 0".

### cgvt-kh9a: Salud Sogamoso
- 174 filas, de 2017 a 2019. El "mes" vale 18 o 24, que parece ser un corte semestral acumulado (**por confirmar**).
- Trae numerador y denominador de P.3.1 a P.3.7 (medicina general, odontología, medicina interna, pediatría, ginecología, obstetricia y cirugía general) con la definición explícita. El texto viene en doble UTF-8 ("dÃ­as").

## Lo que no existe en datos.gov.co

Sin contar Clicsalud (que tiene datos de todas, pero solo hasta 2021 y casi todo de IPS privadas):

- **Ciudades principales:** de las 14 del plan, solo Neiva (ya cargada, más jxjp-6542) y Pereira (k226-53hw) tienen datos de espera de hospitales públicos. **Las otras 12 no tienen nada:** Medellín, Cali, Barranquilla, Cartagena, Bucaramanga (el HUS no trae la espera), Cúcuta, Manizales, Ibagué, Villavicencio, Pasto, Santa Marta y Montería. En Bogotá solo están las 4 subredes agregadas que ya usamos.
- **Municipios cerca de Bogotá:** solo Facatativá (B, con sus sedes en Subachoque y Guayabal de Síquima). **Soacha, Chía, Zipaquirá, Fusagasugá, Girardot, Mosquera, Funza, Madrid, Cajicá, Sopó, Tenjo, Tabio, Cota, Tocancipá y La Calera no tienen nada.**
