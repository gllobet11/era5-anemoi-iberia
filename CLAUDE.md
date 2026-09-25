# CLAUDE.md — era5-anemoi-iberia

Contexto persistente para Claude Code. Léelo entero al empezar cada sesión, junto con `plan.md`, `Decisions.md` y la última entrada de `progress.md`.

## Qué es este proyecto
Pipeline reproducible que descarga un subconjunto regional de ERA5 (Península Ibérica) desde Copernicus CDS, lo transforma con Xarray/CDO desde GRIB/NetCDF a Zarr, aplica controles de calidad, y genera además un dataset en formato **anemoi-datasets** listo para entrenar modelos de ML meteorológicos.

**Objetivo real:** cerrar gaps de la candidatura a Data/ML Engineer — Regional AI Weather/Climate Forecasting Datasets (BSC, ref. 421_26_ES_CES_RE2, cierre 22/10/2026): formatos científicos (NetCDF, GRIB, Zarr), Xarray/CDO/NCO, datos de reanálisis (ERA5), ecosistema Anemoi y, como stretch, Slurm.
**No es** un proyecto de modelado: no se entrena ningún modelo.

## Stack
- Python 3.11, entorno con **micromamba** (`environment.yml`) — eccodes, CDO y NCO no se instalan bien vía pip.
- Datos: `cdsapi`, `xarray`, `cfgrib`/`eccodes`, `netCDF4`, `zarr`, `dask`, `cdo`, `nco`.
- Anemoi: `anemoi-datasets` (versión fijada en `environment.yml`).
- Calidad: `pytest`, `ruff`, `pre-commit`.
- CI: GitHub Actions + Docker (imagen base micromamba).
- Stretch: Slurm en contenedores (`slurm-docker-cluster`).

## Estructura
```
src/era5_pipeline/   ingest.py · transform.py · qc.py · config.py · cli.py
recipes/             recetas YAML de anemoi-datasets
configs/             dominio, variables, periodo (YAML)
tests/               unit + e2e con fixtures pequeños
tests/fixtures/      GRIB/NetCDF sintéticos o recortados (< 1 MB, versionados)
data/                raw/ interim/ zarr/  → NUNCA en git
reports/             informes QC (JSON + md)
slurm/               scripts sbatch (stretch)
```

## Comandos
```bash
micromamba env create -f environment.yml && micromamba activate era5
python -m era5_pipeline.cli ingest  --config configs/iberia.yaml
python -m era5_pipeline.cli transform --config configs/iberia.yaml
python -m era5_pipeline.cli qc --zarr data/zarr/iberia.zarr
anemoi-datasets create recipes/iberia.yaml data/zarr/iberia-anemoi.zarr
anemoi-datasets inspect data/zarr/iberia-anemoi.zarr
pytest -q && ruff check .
```

## Reglas de trabajo
1. **Una fase por sesión.** El prompt de cada fase está en `Kickoff.md`. No empieces la siguiente sin cumplir el Definition of Done de la actual (`plan.md`).
2. **Idempotencia:** cada paso puede relanzarse sin duplicar ni corromper. Descarga por mes con manifest + checksum; escritura de Zarr por región/append controlado.
3. **Los tests nunca llaman al CDS.** Solo fixtures locales. La descarga real se prueba a mano.
4. **Nada de datos en git** (`data/` en `.gitignore`). Solo fixtures < 1 MB.
5. **Configuración, no constantes:** dominio, variables, fechas y chunks viven en `configs/`.
6. **Ediciones quirúrgicas.** No reescribas módulos enteros para cambiar una función.
7. **Honestidad técnica:** si algo no funciona o se simplifica (p. ej. Slurm simulado en local), se documenta como tal. Nada de overclaiming en README.
8. **Documentación viva al cerrar cada sesión:**
   - Decisión de diseño con alternativas descartadas → nueva entrada en `Decisions.md`.
   - Bug importante resuelto o punto de inflexión que **no** sea ya una decisión → `progress.md`.
   - Si algo ya está en `Decisions.md`, en `progress.md` solo se enlaza (`ver D-00X`), no se repite.

## Trampas conocidas (verificar, no asumir)
- CDS: las peticiones pueden quedarse horas en cola; hay que aceptar la licencia de ERA5 en la web antes de usar la API.
- NetCDF del CDS nuevo: la dimensión temporal puede llamarse `valid_time` y aparecer `expver`; normalizar.
- `tp` (precipitación) es acumulada: al pasar de horario a 6 h hay que **sumar**, no submuestrear.
- Latitud del ERA5 viene descendente; ordenar para slicing consistente.
- Compatibilidad zarr v2/v3 con anemoi-datasets: comprobar antes de fijar versión.
