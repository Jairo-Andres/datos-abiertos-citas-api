# API de oportunidad de citas · datos abiertos Colombia

![CI](https://github.com/Jairo-Andres/datos-abiertos-citas-api/actions/workflows/ci.yml/badge.svg)

**Español** · [English](#english)

¿Cuántos días espera un paciente por una cita médica en un hospital público de Colombia? Cada hospital publica su propio indicador en datos.gov.co, con columnas, periodos y formatos distintos. Este proyecto los **descarga, limpia y unifica** con un ETL en pandas y los sirve en una API REST pública.

```
datos.gov.co (un dataset por hospital) → ETL con pandas (GitHub Actions, semanal) → PostgreSQL (Supabase) → API FastAPI (Render)
```

- **Demo:** [https://datos-abiertos-citas-api.onrender.com](https://datos-abiertos-citas-api.onrender.com) · documentación en [/docs](https://datos-abiertos-citas-api.onrender.com/docs) (plan gratis: la primera petición puede tardar hasta un minuto)
- **Fuentes, licencias y supuestos:** [docs/fuentes.md](docs/fuentes.md)

## Endpoints

| Ruta | Qué devuelve |
|---|---|
| `GET /` | Página con ejemplos en vivo y panel de estado |
| `GET /docs` | Documentación interactiva (OpenAPI) |
| `GET /health` | Estado de la API y de la base de datos |
| `GET /estado` | Hospitales, registros, última carga del ETL y latencia p50/p95 |
| `GET /hospitales?depto=` | Hospitales incluidos |
| `GET /especialidades` | Especialidades disponibles |
| `GET /oportunidad?especialidad=&depto=&hospital_id=&definicion=&limit=&offset=` | Días promedio de espera por hospital, especialidad y periodo |

Ejemplo:

```bash
curl "https://datos-abiertos-citas-api.onrender.com/oportunidad?especialidad=pedia&limit=2"
```

Cada registro trae `granularidad` (`mes` o `trimestre`) y `definicion` (`solicitud`: desde que se pide la cita; `fecha_deseada`: desde la fecha para la cual se pidió), porque los hospitales no publican igual. Ver [docs/fuentes.md](docs/fuentes.md).

## Correrlo en local

Requisitos: Python 3.12. Docker es opcional.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements-dev.txt

python -m etl.run                 # descarga los datasets y llena data/local.db (SQLite)
uvicorn app.main:app --reload     # http://localhost:8000
pytest                            # pruebas
```

Sin `DATABASE_URL` todo usa SQLite en `data/local.db`. Con Docker se levanta Postgres + API: `docker compose up --build` y luego `DATABASE_URL=postgresql+psycopg://citas:citas_local@localhost:5432/citas python -m etl.run`.

## Despliegue (planes gratis)

1. **Supabase (base de datos).** Crea un proyecto y copia la cadena de conexión en *Project Settings → Database → Connection string*, modo **Session pooler** (Render no tiene IPv6 y la conexión directa de Supabase la usa).
2. **GitHub Actions (ETL).** En el repo: *Settings → Secrets and variables → Actions → New repository secret*, nombre `DATABASE_URL`, valor la cadena del paso 1. Corre el workflow **ETL semanal** a mano una vez (*Actions → ETL semanal → Run workflow*). Después corre solo cada lunes.
3. **Render (API).** *New → Web Service*, conecta este repo, elige **Docker** y el plan **Free**. En *Environment* agrega `DATABASE_URL`. En *Settings → Health Check Path* pon `/health`.

Los secretos van solo en Render y en GitHub Secrets, nunca en el código. Copia `.env.example` a `.env` si quieres una base remota en local.

## Qué revisar si algo se cae

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La primera petición tarda 30–60 s | Render duerme el servicio gratis tras ~15 min sin uso | Es normal; la landing lo avisa. Para la demo, abre la URL un minuto antes |
| `/health` responde `"db": "error"` | Supabase pausó el proyecto (~7 días sin actividad) o cambió la contraseña | Reactívalo en el panel de Supabase y revisa `DATABASE_URL` en Render y en GitHub Secrets |
| `/estado` muestra una última carga vieja | El workflow del ETL falló o GitHub lo desactivó (60 días sin commits en el repo) | Mira *Actions → ETL semanal*; si está desactivado, actívalo y córrelo a mano |
| El ETL termina con `"errores": 1` o más | Un hospital cambió columnas o datos.gov.co no respondió | El log dice qué dataset falló (`fuente con error`); las demás fuentes sí se cargan. Ajusta su función en `etl/transformar.py` |
| Aparece una especialidad rara (en minúsculas o duplicada) | Un hospital escribió el nombre distinto | Agrega la equivalencia en `etl/especialidades.py` |
| Render falla al construir | Cambió una dependencia | Revisa el job `docker` del CI, que construye la misma imagen |

Los logs de la API y del ETL son JSON (una línea por evento): en Render están en *Logs* y en GitHub en la ejecución del workflow.

## Estructura

```
app/        API FastAPI (rutas, modelos, logs y métricas de latencia, landing)
etl/        fuentes, descarga, transformación por hospital y carga
tests/      pytest de la API y del ETL
docs/       fuentes, licencias y supuestos
.github/    CI (tests + build Docker) y ETL semanal
```

## Licencia

Código bajo licencia MIT. Los datos son de cada hospital vía datos.gov.co, bajo CC BY-SA 4.0 (ver [docs/fuentes.md](docs/fuentes.md)).

---

## English

How many days does a patient wait for a medical appointment at a public hospital in Colombia? Each hospital publishes its own indicator on datos.gov.co, with different columns, periods and formats. This project **downloads, cleans and unifies** them with a pandas ETL and serves them through a public REST API.

```
datos.gov.co (one dataset per hospital) → pandas ETL (GitHub Actions, weekly) → PostgreSQL (Supabase) → FastAPI (Render)
```

- **Demo:** [https://datos-abiertos-citas-api.onrender.com](https://datos-abiertos-citas-api.onrender.com) · docs at [/docs](https://datos-abiertos-citas-api.onrender.com/docs) (free tier: the first request may take up to a minute)
- **Sources, licenses and assumptions** (Spanish): [docs/fuentes.md](docs/fuentes.md)

### Endpoints

| Route | Returns |
|---|---|
| `GET /` | Landing page with live examples and a status panel |
| `GET /docs` | Interactive OpenAPI docs |
| `GET /health` | API and database health |
| `GET /estado` | Hospitals, records, last ETL run and p50/p95 latency |
| `GET /hospitales?depto=` | Hospitals included |
| `GET /especialidades` | Available specialties |
| `GET /oportunidad?especialidad=&depto=&hospital_id=&definicion=&limit=&offset=` | Average waiting days by hospital, specialty and period |

Each record includes `granularidad` (`mes` = month, `trimestre` = quarter) and `definicion` (`solicitud`: from the day the appointment was requested; `fecha_deseada`: from the date the patient asked for), because hospitals don't publish the same way.

### Run locally

Requirements: Python 3.12. Docker is optional.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements-dev.txt

python -m etl.run                 # downloads the datasets into data/local.db (SQLite)
uvicorn app.main:app --reload     # http://localhost:8000
pytest
```

Without `DATABASE_URL` everything uses SQLite at `data/local.db`. With Docker: `docker compose up --build` starts Postgres + API.

### Deployment (free tiers)

1. **Supabase (database).** Create a project and copy the connection string from *Project Settings → Database → Connection string*, **Session pooler** mode (Render has no IPv6, which Supabase's direct connection uses).
2. **GitHub Actions (ETL).** In the repo: *Settings → Secrets and variables → Actions → New repository secret*, name `DATABASE_URL`. Run the **ETL semanal** workflow once by hand; it then runs every Monday.
3. **Render (API).** *New → Web Service*, connect this repo, choose **Docker** and the **Free** plan. Add `DATABASE_URL` under *Environment* and set *Health Check Path* to `/health`.

Secrets live only in Render and GitHub Secrets, never in the code.

### What to check if something goes down

| Symptom | Likely cause | What to do |
|---|---|---|
| First request takes 30–60 s | Render's free service sleeps after ~15 min idle | Expected; the landing page says so. Open the URL a minute before a demo |
| `/health` returns `"db": "error"` | Supabase paused the project (~7 days idle) or the password changed | Restore it in Supabase and check `DATABASE_URL` in Render and GitHub Secrets |
| `/estado` shows an old last ETL run | The ETL workflow failed or GitHub disabled it (60 days without commits) | Check *Actions → ETL semanal*; re-enable and run it by hand |
| ETL ends with `"errores": 1` or more | A hospital changed its columns or datos.gov.co didn't respond | The log names the failing dataset (`fuente con error`); the others still load. Fix its function in `etl/transformar.py` |
| A strange specialty shows up | A hospital spelled it differently | Add the mapping in `etl/especialidades.py` |
| Render build fails | A dependency changed | Check the CI `docker` job, which builds the same image |

API and ETL logs are JSON lines: in Render under *Logs*, and in GitHub inside each workflow run.

### License

Code under the MIT license. Data belongs to each hospital via datos.gov.co, under CC BY-SA 4.0.
