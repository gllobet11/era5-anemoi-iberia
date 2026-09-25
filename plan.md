# plan.md — era5-anemoi-iberia

## Objetivo y criterio de éxito
Tener antes del **viernes 16/10/2026** (margen de 6 días sobre el cierre del 22/10) un repo público que permita decir, sin exagerar:

> "He construido un pipeline reproducible de ERA5 (GRIB/NetCDF → Zarr) con Xarray y CDO, con QC, tests y CI, y lo he exportado a un dataset compatible con anemoi-datasets."

**Éxito mínimo (MVP = F0–F5):** `anemoi-datasets inspect` sobre un dataset generado por la receta del repo pasa, CI en verde, README con arquitectura y limitaciones.
**Éxito ampliado:** + Slurm simulado (F6) y/o subconjunto CERRA (F7).

## Alcance
| Dentro | Fuera |
|---|---|
| ERA5 single levels + 2 niveles de presión, dominio Iberia | Entrenar modelos (AIFS, etc.) |
| 3 años (2020–2022), 6 h | ERA5 global o resoluciones altas |
| Pipeline propio Xarray/CDO + receta anemoi | Infra cloud de pago |
| QC, tests, CI, Docker | HPC real (solo simulación local) |

**Dominio inicial:** N 45, W −10, S 35, E 5 (Península + Baleares, incluye Catalunya).
**Variables:** `2t`, `10u`, `10v`, `msl`, `tp`, `sp`; `t` y `z` en 500 y 850 hPa. Volumen estimado: < 1 GB, cabe en local y en cola del CDS razonable.

## Fases

| Fase | Contenido | Duración | Fecha objetivo | Definition of Done |
|---|---|---|---|---|
| **F0 Setup** | Repo, `environment.yml` (micromamba), estructura, pre-commit, ruff, `.gitignore`, cuenta CDS + licencia ERA5 + `~/.cdsapirc`. **Lanzar ya la primera descarga** (colas). | 0,5 d | sáb 26/09 | `pytest` vacío pasa; `cdo --version` y `import cfgrib` OK; 1 mes descargado |
| **F1 Ingesta** | `ingest.py`: descarga por mes y tipo (single/pressure), GRIB como formato canónico + 1 mes en NetCDF para comparar. Manifest JSON con checksum, reintentos, skip si ya existe. | 1 d | mar 29/09 | Relanzar no descarga nada nuevo; manifest completo; 36 meses en `data/raw/` |
| **F2 Transformación** | `transform.py`: abrir GRIB con cfgrib, normalizar (nombres CF, unidades, lat ascendente, lon −180..180, `valid_time`→`time`), `tp` horaria→6 h por suma, merge single+pressure, chunking, escritura Zarr. Un paso hecho con **CDO** (p. ej. `remapbil` a rejilla regular o `sellonlatbox`) y comparación con el equivalente en Xarray. Inspección con **NCO** (`ncdump -h`, `ncks`). | 2 d | jue 01/10 | Zarr abre con `xr.open_zarr`; dims/coords correctas; diferencia CDO vs Xarray documentada |
| **F3 QC + tests** | `qc.py`: timesteps faltantes, % NaN, rangos físicos por variable, unidades, coords monótonas, estadísticos por variable vs periodo. Informe JSON+md. Tests unitarios con fixtures pequeños + 1 e2e sobre fixture GRIB. | 1,5 d | lun 05/10 | Cobertura de transform/qc ≥ 80 %; QC detecta un fallo inyectado a propósito |
| **F4 CI/CD** | GitHub Actions: ruff + pytest en env micromamba (con caché), build de imagen Docker, e2e sobre fixture. Badge en README. | 1 d | mar 06/10 | CI verde en `main`; imagen construye; ningún job toca el CDS |
| **F5 Anemoi** | Receta YAML en `recipes/` usando fuente `grib` sobre los ficheros locales (join single+pressure, accumulations para `tp`). `anemoi-datasets create` + `inspect`. Comparar estadísticos con el Zarr propio. Notebook corto que abre el dataset con `anemoi.datasets.open_dataset`. | 2 d | vie 09/10 | `inspect` OK; tabla de estadísticos comparados en README |
| **F6 Slurm (stretch)** | `slurm-docker-cluster` en local; `sbatch` con **job array** por mes para ingest/transform; logs y dependencias entre jobs (`--dependency=afterok`). Etiquetado como simulación. | 1,5 d | mar 13/10 | Job array ejecuta el pipeline completo en el clúster simulado |
| **F7 CERRA (stretch)** | Subconjunto CERRA (reanálisis regional europeo, rejilla Lambert) para 1 mes; entender la proyección y cómo regridearla con CDO. | 1 d | mié 14/10 | Zarr CERRA + nota de diferencias vs ERA5 |
| **F8 Cierre** | README en inglés (arquitectura, decisiones clave, resultados QC, limitaciones honestas), actualizar `master_cv.md`, recalcular encaje. | 0,5 d | jue 15/10 | Repo público; CV actualizado |

Nota: el lunes 12/10 es festivo; cuenta como día de colchón.

## Riesgos
| Riesgo | Impacto | Mitigación |
|---|---|---|
| Colas del CDS de horas/días | Bloquea F1 | Lanzar descargas en F0; empezar con 1 mes; ARCO-ERA5 (Zarr en Google Cloud) como plan B documentado |
| eccodes/cfgrib/CDO difíciles de instalar | Bloquea F0 | micromamba + imagen Docker desde el día 1 |
| Incompatibilidades de versión de anemoi-datasets (zarr, fuentes NetCDF) | Bloquea F5 | Fuente GRIB (la más usada en la doc), fijar versión, spike de 1 h al inicio de F5 con la receta de ejemplo |
| `tp` mal agregada | Datos incorrectos silenciosos | Test específico: suma 6 h == suma horaria |
| Scope creep (Slurm, CERRA, modelo) | No llegar al MVP | Stretch solo si F5 cerrada antes del 09/10 |

## Mensaje para el CV (a validar al final)
"ERA5 → Zarr pipeline (Xarray, CDO, cfgrib) with QC, pytest and GitHub Actions CI; exported anemoi-datasets-compatible training dataset for the Iberian domain." Slurm solo si F6 está hecha, y como "simulated cluster".
