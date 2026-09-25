# Kickoff.md — era5-anemoi-iberia

Un prompt por fase para Claude Code. Copia el bloque de la fase, no más. Cada sesión empieza leyendo `CLAUDE.md`, `plan.md`, `Decisions.md` y la última entrada de `progress.md`, y termina actualizando esos dos últimos.

---

## F0 — Setup
```
Lee CLAUDE.md y plan.md. Fase F0.
1. Crea la estructura de carpetas de CLAUDE.md, environment.yml (python 3.11, xarray, cfgrib, eccodes,
   netcdf4, zarr, dask, cdsapi, cdo, nco, pytest, ruff, pre-commit; anemoi-datasets fijado a la última
   versión estable que resuelva con el resto), pyproject.toml con el paquete era5_pipeline, .gitignore
   (data/, *.grib, *.nc salvo tests/fixtures), .pre-commit-config.yaml con ruff.
2. configs/iberia.yaml con dominio, variables, niveles, periodo 2020-2022, frecuencia 6h y chunks.
3. Script mínimo de smoke test: importa cfgrib, xarray, zarr y ejecuta `cdo --version`.
4. Dime qué comprobar a mano: cuenta CDS, licencia ERA5 aceptada, ~/.cdsapirc.
No escribas lógica de ingesta todavía. Al acabar: entrada en progress.md y decisiones nuevas en Decisions.md.
```

## F1 — Ingesta
```
Fase F1. Implementa src/era5_pipeline/ingest.py:
- Una petición por (mes, tipo) donde tipo ∈ {single-levels, pressure-levels}, leyendo configs/iberia.yaml.
- Formato GRIB; además un único mes en NetCDF para comparar formatos.
- Idempotente: manifest data/raw/manifest.json con ruta, tamaño, sha256, fecha; si el fichero existe y el
  checksum coincide, skip. Reintentos con backoff. Escritura atómica (fichero temporal + rename).
- CLI `ingest` en cli.py.
Tests: unitarios del manifest y la lógica de skip con cdsapi mockeado. Ningún test llama al CDS.
Después, lanzo yo la descarga real. Actualiza progress.md/Decisions.md.
```

## F2 — Transformación
```
Fase F2. Implementa src/era5_pipeline/transform.py:
- Abrir GRIB con cfgrib (single y pressure por separado; ojo a filter_by_keys si hay mezcla de typeOfLevel).
- Normalizar: nombres, unidades, lat ascendente, lon en -180..180, dimensión temporal única `time`.
- tp: agregar a 6 h sumando las horas correspondientes (define y documenta la convención de ventana).
- Merge single + pressure, chunking según config, escritura a data/zarr/iberia.zarr con consolidated metadata.
- Un paso equivalente hecho con CDO (sellonlatbox o remapbil) sobre un mes, y script que compare el
  resultado con el de Xarray (diferencia máxima por variable).
- Comparar GRIB vs NetCDF del mismo mes: ¿mismos valores, mismos metadatos? Documentar diferencias.
Tests con fixtures pequeños en tests/fixtures. Actualiza progress.md/Decisions.md.
```

## F3 — QC y tests
```
Fase F3. Implementa src/era5_pipeline/qc.py con checks: timesteps esperados vs presentes, % NaN por
variable, rangos físicos plausibles por variable (defínelos en config, no hardcodeados), unidades
esperadas, coordenadas monótonas, estadísticos (media, std, min, max) por variable.
Salida: reports/qc_<fecha>.json y .md. Exit code != 0 si falla un check crítico.
Tests: uno por check + un test que inyecta un fallo (NaN, timestep eliminado, unidad errónea) y verifica
que se detecta. Test específico de que la suma de tp a 6 h conserva la suma horaria.
Objetivo cobertura ≥ 80 % en transform y qc. Actualiza progress.md/Decisions.md.
```

## F4 — CI/CD
```
Fase F4. GitHub Actions en .github/workflows/ci.yml:
- Job lint (ruff) y job test (pytest con cobertura) usando setup-micromamba con caché del entorno.
- Job e2e: ingest mockeado → transform → qc sobre fixtures.
- Dockerfile (base micromamba) y job que construye la imagen (sin push).
- Badge en README. Nada de secretos del CDS en CI.
Actualiza progress.md/Decisions.md.
```

## F5 — Anemoi
```
Fase F5. Primero, spike de 1 h: reproduce la receta de ejemplo de la documentación de anemoi-datasets
con el mínimo de datos y confirma versión, fuentes y formato Zarr que produce.
Luego recipes/iberia.yaml:
- Fuente `grib` sobre data/raw, join de single + pressure levels, tratamiento de tp como acumulación.
- dates 2020-2022, frequency 6h; name/description/attribution/licence correctos (ERA5, C3S, CC-BY-4.0).
- `anemoi-datasets create` + `inspect`; guarda la salida de inspect en reports/.
- Script que compara estadísticos del dataset anemoi con los de mi Zarr (qc.py) y explica diferencias.
- notebooks/01_open_anemoi.ipynb: abrir con anemoi.datasets.open_dataset, mostrar shape, variables,
  subset por fechas y un mapa de 2t.
Añade un test que valida la receta (parseo YAML + campos obligatorios). Actualiza progress.md/Decisions.md.
```

## F6 — Slurm (stretch)
```
Fase F6. Levanta un clúster Slurm local con slurm-docker-cluster (documenta cómo).
slurm/ingest_array.sbatch y slurm/transform.sbatch: job array por mes, logs por tarea, transform con
--dependency=afterok sobre el array de ingest, y un job final de QC.
README: sección "Running on a Slurm cluster (simulated locally)" dejando claro que no es HPC real.
Actualiza progress.md/Decisions.md.
```

## F7 — CERRA (stretch)
```
Fase F7. Descarga 1 mes de CERRA (single levels, variables equivalentes) para el dominio Iberia.
Explica la rejilla (Lambert conformal, coordenadas 2D), regridea a la rejilla del ERA5 del proyecto con
CDO y compara 2t entre ambos reanálisis (bias medio, mapa de diferencias).
Actualiza progress.md/Decisions.md.
```

## F8 — Cierre
```
Fase F8. README en inglés: motivación, diagrama del pipeline, cómo reproducir, decisiones clave
(resumen de Decisions.md), resultados de QC, limitaciones honestas y próximos pasos.
Revisa que no haya claims que el código no respalde. Genera una lista de 3-4 bullets para el CV
con verbos concretos y sin inflar (Slurm solo si F6 está hecha).
```
