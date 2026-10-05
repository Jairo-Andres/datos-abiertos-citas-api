# Verificación de datos

Revisión hecha el 5 de octubre de 2026 contra las fuentes originales (datos.gov.co y el portal de datos abiertos de Bogotá), descargadas de nuevo ese día. Para cada valor atípico se volvió a la fila original. No se corrigió ningún valor: lo que es un error evidente se excluye del ETL (`etl/exclusiones.py`) y lo que no se puede confirmar se publica tal como viene, con la nota aquí.

## Psiquiatría en Colón (50–57 días)

**Conclusión: el dato es coherente con la propia fuente y se publica.**

- El dataset en vivo es idéntico al descargado antes (299 filas).
- El resultado coincide con numerador ÷ denominador en todos los trimestres, salvo 2023-T2 (publica 56; la división da 53,1).
- La serie es estable durante cinco años: entre 36 y 57 días, con máximo de espera de unos 184 días en todos los trimestres. No hay señales de numerador y denominador intercambiados.
- Es la especialidad con más espera del hospital (mediana 44 días; las demás están entre 0 y 4).
- Las citas por trimestre (mediana 1.305) son altas para Colón, pero parecidas a Psicología (1.253). Sin confirmación del hospital no se puede saber si atiende pacientes de otros municipios; queda **por confirmar**.

| Trimestre | Numerador | Denominador | Resultado publicado |
|---|---|---|---|
| 2021-T1 | 55.970 | 1.056 | 53 |
| 2021-T2 | 59.560 | 1.158 | 51 |
| 2022-T1 | 55.455 | 1.305 | 42 |
| 2023-T1 | 63.587 | 1.117 | 57 |
| 2023-T2 | 60.882 | 1.146 | 56 |
| 2025-T4 | 60.028 | 1.370 | 44 |
| 2026-T2 | 21.879 | 1.038 | 21 |

## Errores evidentes (excluidos)

| Fuente | Filas | Problema | Evidencia |
|---|---|---|---|
| Colón | 2021-T4 Psiquiatría | 24.156 citas, unas 20 veces lo normal, con resultado de 2 días | Los trimestres vecinos tienen entre 1.056 y 1.325 citas y entre 42 y 51 días |
| Colón | 2021-T4 Ginecología, Ecografía y Obstetricia | Las tres filas tienen exactamente los mismos valores (1535 / 961 / 2 / 8) | Copiado entre filas |
| Colón | 2023-T4, todas las especialidades | Las citas del trimestre suman 1,2 a 1,6 veces lo de T1 a T3 juntos (Medicina general: 20.323) | 2023 no tiene fila anual (VIGENCIA); parece el total anual cargado como IV trimestre |
| Neiva | oct-2023, indicador desde la solicitud | Denominador 97.794 con resultado 1,4 | El otro indicador del mismo mes tiene denominador 9.794; con ese valor daría 14,0 días. Se excluye en vez de corregir |
| Neiva | jul-2020 a dic-2021, ambos indicadores | La espera desde la fecha deseada sale mayor que desde la solicitud, al revés de 2018–2019 y 2022–2024 | Lo más probable es que las etiquetas estén intercambiadas en esos 18 meses; no se puede confirmar cuál es cuál |
| Neiva | ene–jun 2020 | Cada mes aparece dos veces con valores contradictorios | Ya se descartaba antes |
| Todas | Periodos con menos de 10 citas | El promedio depende de una o dos personas | Por ejemplo Radiología en Colón 2022-T4: 21 días con 1 cita. No aplica a Bogotá, que no publica citas |

## Valores raros que se publican (no se pueden confirmar ni descartar)

- **Colón 2026-T2:** en el mismo trimestre suben Anestesiología (3 a 20 días), Pediatría (3 a 17), Odontología (4 a 11), Radiología (12) y Medicina interna (11). Numerador ÷ denominador cuadra. Es el dato más reciente; puede ser real.
- **Colón 2024-T2:** las columnas de máximo y mínimo de días no cuadran con el promedio. La API no usa esas columnas, así que no afecta.
- **Colón, columna horas_promedio:** no guarda relación con el resultado en días (Psiquiatría: unas 168 horas frente a 44 días). No se usa.
- **Neiva dic-2022:** 699 citas en vez de unas 8.900, con resultados de 14,9 y 4,7 días. Los dos indicadores son coherentes entre sí.
- **Popayán, Medicina interna 2026:** entre 240 y 347 citas al mes, frente a 68–100 en 2022–2025. El resultado sigue en 6,4–6,9 días.
- **Aguadas, Odontología mar–may 2026:** 0 días con 102 a 143 citas. Plausible: la cita se asigna el mismo día.

## Cómo se buscaron los atípicos

Por hospital y especialidad: valores por encima de Q3 + 3 × IQR, saltos de más de 3 veces entre periodos consecutivos, ceros con muchas citas y número de citas muy distinto de lo habitual. Cada caso se revisó en la fila original de la fuente.
