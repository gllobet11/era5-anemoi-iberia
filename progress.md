# progress.md — era5-anemoi-iberia

Diario de ejecución. Recoge **estado por fase**, **bugs importantes resueltos** y **puntos de inflexión** (algo descubierto que cambió el rumbo o el entendimiento) que **no** estén ya en `Decisions.md`. Si un hallazgo acaba generando una decisión, aquí solo se enlaza: `→ D-0XX`.

No es un log de commits: una entrada por sesión, 5–15 líneas.

## Estado

| Fase | Estado | Fecha cierre | Notas |
|---|---|---|---|
| F0 Setup | ✅ cerrada | 2026-09-25 | 1 mes (ene-2020 single levels) vía web |
| F1 Ingesta | ✅ cerrada | 2026-09-25 | 74/74 ficheros, 875 MB; relanzar = 0 descargas |
| F2 Transformación | ✅ cerrada | 2026-09-25 | `iberia.zarr` 4384×41×61, 221 MB; CDO y NetCDF comparados |
| F3 QC + tests | ✅ cerrada | 2026-09-27 | 5 checks críticos; QC real OK; cobertura qc 100 %, transform 85 % |
| F4 CI/CD | 🔄 en curso | | Todo verde en local; falta el repo en GitHub para validar la CI |
| F5 Anemoi | ⏳ | | |
| F6 Slurm (stretch) | ⏳ | | |
| F7 CERRA (stretch) | ⏳ | | |
| F8 Cierre | ⏳ | | |

Leyenda: ⏳ pendiente · 🔄 en curso · ✅ cerrada · ⛔ bloqueada · ⏭️ descartada

---

## Plantilla de entrada
```
### AAAA-MM-DD — Fase FX
**Hecho:**
-
**Bugs resueltos** (síntoma → causa → arreglo → cómo se evita que vuelva):
-
**Puntos de inflexión** (qué se descubrió y qué cambió):
-
**Decisiones generadas:** → D-0XX (o "ninguna")
**Siguiente paso:**
```

---

## Entradas

### 2026-09-25 — Planificación
**Hecho:**
- Creados `CLAUDE.md`, `plan.md`, `Kickoff.md`, `Decisions.md` (D-001 a D-006 en estado Propuesta) y este fichero.
**Bugs resueltos:** ninguno.
**Puntos de inflexión:**
- Encaje inicial con la plaza del BSC estimado en ~40–45 %; gaps esenciales en formatos científicos y HPC. El proyecto apunta a ~55 % cerrando formatos + Anemoi; HPC seguirá siendo gap parcial.
**Decisiones generadas:** → D-001 a D-006
**Siguiente paso:** F0, y lanzar la primera descarga del CDS el mismo día por las colas.

### 2026-09-25 — Fase F0
**Hecho:**
- Renombrados `*_1.md` → `plan.md`, `Kickoff.md`, `progress.md`; `git init` (sin commits).
- Estructura de carpetas, `environment.yml` (entorno `era5` creado con mamba), `pyproject.toml` (paquete `era5_pipeline`, ruff, pytest), `.gitignore`, `.pre-commit-config.yaml` (ruff + ficheros > 1 MB) instalado.
- Versiones resueltas: anemoi-datasets 0.5.44, zarr 2.18.7, xarray 2026.7.0, cfgrib 0.9.15.1, eccodes 2.48.0, CDO 2.6.1.
- `configs/iberia.yaml` + `config.load_config`; `tests/test_smoke.py` (imports, cdo/ncks, config): 3 passed; `ruff check` limpio.
- `scripts/first_download.py`: descarga desechable ene-2020 single levels GRIB (F1 lo sustituye).
**Bugs resueltos:** ninguno.
**Puntos de inflexión:**
- anemoi-datasets fija zarr v2 → D-007.
**Decisiones generadas:** → D-007, D-008 (D-003 aceptada con matiz mamba local).
- Peticiones de la web del CDS revisadas (notas para F1): usar siempre `download_format: unarchived` (si no, puede llegar `.zip`); el área sale de `cfg["area"]` (en la web se usó W−11 por error en pressure levels, no mezclar esos ficheros).
- Primer mes descargado desde la web (`data/raw/db96b3b8….grib`, 30 MB, 8184 mensajes, ene-2020 horario, rejilla 61×41, área correcta). Incluye extras (`2d`, `sst`, olas `swh/mwd/mwp`). Inspección con `grib_ls` + `cfgrib.open_datasets` → notas para F2:
  - cfgrib separa el fichero en 3 datasets: olas (`typeOfLevel=meanSea`, rejilla **0,5°** 21×31), superficie instantánea y `tp` aparte → hace falta `filter_by_keys`; las olas quedan fuera del alcance.
  - `tp` no viene como serie horaria: dims `(time=63, step=12)` = pasadas de 06/18 UTC con pasos de 1 h (`stepRange` 5-6, 6-7…). El primer mensaje (base 2019-12-31 18:00, paso 5-6) es la acumulación 23:00→00:00 del 01-01. Hay que apilar por `valid_time` antes de sumar a 6 h.
  - cfgrib renombra: `2t→t2m`, `10u→u10`, `10v→v10`, `2d→d2m`. Normalizar nombres en F2.
- `scripts/first_download.py` OK (Request ID 97760465…, ~10 min en cola): `data/raw/single_2020-01.grib`, 22 MB, solo las 6 variables × 744 h.
**Siguiente paso:** F1 (ingesta).

### 2026-09-25 — Fase F1
**Hecho:**
- `ingest.py` (meses del periodo, petición por (tipo, mes, formato), manifest sha256, reintentos, `.part`+rename, concurrencia) y CLI `python -m era5_pipeline.cli ingest --config …`. Diseño → D-009.
- `tests/test_ingest.py` con `FakeClient` (nunca toca el CDS): idempotencia (2ª ejecución 0 llamadas), fichero corrupto se re-descarga, reintento sin dejar `.part`, reintentos agotados propagan error, días por mes (bisiesto). 9 tests en verde.
- `scripts/first_download.py` eliminado (sustituido por F1). Borrado el GRIB descargado desde la web; `single_2020-01.grib` registrado en el manifest.
- Seguido en la misma sesión que F0 por decisión del usuario (excepción a la regla "una fase por sesión").
**Bugs resueltos:** ninguno.
**Puntos de inflexión:**
- Inspeccionado GRIB de pressure levels bajado desde la web (`13d45…grib`, ene-2020, W−11 → 65×41, no usable tal cual): GRIB **edición 1**, `t`/`z` × 500/850 × 124 pasos (6 h). cfgrib lo abre en un único dataset limpio (sin `filter_by_keys`): dims `(time, isobaricInhPa, latitude, longitude)`, `isobaricInhPa` **descendente** (850, 500), latitud descendente, `step=0`, `valid_time == time`. Para F2: renombrar `isobaricInhPa→level`, ordenar niveles y latitudes; `z` es geopotencial (m²/s²), no altura.
**Decisiones generadas:** → D-009
**Siguiente paso:** lanzar la descarga real (`python -m era5_pipeline.cli ingest --config configs/iberia.yaml`), verificar 74 entradas en el manifest y que relanzar da `downloaded: 0`. Entonces cerrar F1.

### 2026-09-25 — Fase F2 (iniciada con la ingesta F1 en curso)
**Hecho:**
- `transform.py`: `open_single` (instant + accum por `filter_by_keys`), `stack_accum`, `tp_to_6h`, `open_pressure`, `normalize` (GRIB y NetCDF), `build` (merge + CF + chunks), `write_zarr` atómico; CLI `transform`. Diseño → D-010, D-011.
- Probado sobre ene-2020 real: 124 pasos × 41 × 61 (+2 niveles), lat ascendente, CF OK; `tp` NaN solo en 2020-01-01 00 UTC (esperado).
- Fixtures versionados (494 KB): `tests/fixtures/single_2020-01.grib` (84 mensajes, válidas 00–13 UTC del 01-01) y `pressure_2020-01.grib` (12 mensajes del GRIB web con W−11, que ejercita el recorte). 16 tests en verde.
- `scripts/compare_cdo_xarray.py` → `reports/cdo_vs_xarray.md`: `remapbil` vs `interp(linear)` difiere en ~1 ulp de float32 (t2m 1.5e-5 K, msl 3.7e-3 Pa); `tp` 6 h CDO `timselsum,6,1` vs Xarray: 0 exacto.
- `scripts/compare_grib_netcdf.py` preparado (acepta `.nc.zip`, incluye `ncdump -h`); pendiente de que la ingesta descargue el NetCDF.
**Bugs resueltos:**
- Metadatos perdidos: `xr.merge(combine_attrs="drop")` borraba también los atributos de las variables (units = None) → `override` + atributos globales fijados después. Cubierto por `test_build_structure`.
- `GRIB_Nx`/`numberOfPoints` obsoletos tras recortar (65 vs 61) → se eliminan los `GRIB_*` de rejilla en `normalize`. Test `test_no_stale_grib_grid_attrs`. También se perdían los atributos de `longitude` al recalcularla.
**Puntos de inflexión:**
- Una comparación con rejilla destino a mitad de celda daba diferencia 0 exacta CDO vs Xarray (pesos 0,25 → mismo redondeo): no discriminaba. Rejilla 0,3° con pesos asimétricos.
- CDO lee el GRIB con códigos de parámetro (`var167`, `var228`…) y ve `tp` directamente como serie horaria; cfgrib como `(time, step)`. Mismo resultado tras normalizar.
- `pressure_2020-01.grib` (ingesta) vs GRIB web recortado: `z` idéntico; `t` difiere en 1 LSB (2⁻¹² K) en el 1,2 % de puntos: el CDS reempaqueta a 16 bits según el área pedida. No es bit-reproducible entre áreas distintas.
**Decisiones generadas:** → D-010, D-011
**Siguiente paso:** cuando acabe la ingesta: `compare_grib_netcdf.py` para single y pressure → `reports/`; `cli transform` sobre los 36 meses y comprobar `xr.open_zarr`. Entonces cerrar F1 y F2.

### 2026-09-25 — Cierre F1 + F2
**Hecho:**
- Ingesta completa: 74/74 (72 GRIB + 2 NetCDF), 875 MB. Relanzada: `{'downloaded': 0, 'skipped': 74}` en 8 s (verifica sha256). Ritmo real ~20 ficheros/h con 4 workers (cola del CDS).
- `single_2020-01.nc` llegó como `.nc.zip` (2 ficheros: `stepType-instant` y `stepType-accum`) pese a `download_format: unarchived`; pressure llegó como `.nc` simple. Previsto en D-009.
- `reports/grib_vs_netcdf_{single,pressure}.md`: diferencia **0** en las 8 variables. El NetCDF del CDS es una conversión con cfgrib del mismo GRIB (lleva los mismos `GRIB_*`). Diferencias solo de forma: `valid_time`/`pressure_level` en vez de `time`/`isobaricInhPa`, coord `expver` (string) y `number`, `tp` ya como serie horaria, deflate 1 + shuffle con 1 chunk por variable (≈20 % menos que GRIB 16 bits), `standard_name = "unknown"` en t2m/u10/v10/tp igual que cfgrib. Inspección con `ncdump -h` y `ncks --hdn -m`.
- `cli transform` sobre 36 meses → `data/zarr/iberia.zarr` (zarr v2, consolidado): 4384 pasos 6 h regulares 2020-01-01 00 → 2022-12-31 18, 41×61, niveles 500/850, 221 MB. Único NaN: `tp` 2020-01-01 00 UTC (D-010). 5 min 41 s, pico de RAM 5,2 GB.
**Bugs resueltos:**
- `tp` salía `(lat, lon, time)` de `stack_accum` (`stack` pone la dim nueva al final); se había parcheado en `tp_to_6h`, pero `open_single` seguía devolviéndola mal y rompió la comparación con NetCDF → `transpose` en `stack_accum` (origen) y test `test_open_single_tp_is_time_first`.
- La ingesta fue matada una vez por Claude Code por falta de memoria del sistema (no del proceso); al relanzar se saltaron los 18 ficheros del manifest sin incidencias. Valida D-009.
**Puntos de inflexión:**
- Pico de 5,2 GB de RAM para 875 MB de GRIB: cfgrib materializa `tp` al apilar `(time, step)` y el concat carga cada mes. Techo conocido; si el dominio/periodo crece, abrir con `chunks={}` o procesar por año.
**Decisiones generadas:** D-002 y D-008 → Aceptadas.
**Siguiente paso:** F3 (QC + tests, cobertura ≥ 80 % en transform/qc).

### 2026-09-27 — Fase F3
**Hecho:**
- `qc.py`: checks de tiempo, coordenadas monótonas, unidades, NaN y rangos, más estadísticos por variable/nivel. Informe `reports/qc_<fecha>.{json,md}`. CLI `qc --zarr … [--config]` con exit 1 si falla algo. Diseño → D-012.
- Sección `qc` en `configs/iberia.yaml` (umbrales, exención de NaN de `tp`, rangos).
- `tests/test_qc.py`: dataset sintético válido, un test por check, inyección combinada de fallos (NaN + timestep eliminado + unidad errónea → fallan exactamente `time`, `nan` y `units`) y e2e GRIB fixture → `build` → Zarr → CLI (detecta solo el paso de 18 UTC que falta en el fixture). El test de conservación de la suma de `tp` ya existía (`test_tp_6h_window_is_right_closed`). 26 tests en verde.
- Cobertura: `qc` 100 %, `transform` 85 % (sin cubrir solo `transform()`, que lee `data/raw`).
- QC sobre `iberia.zarr` real: todo OK, 4384/4384 pasos, 0 % NaN tras la exención, todas las variables dentro de rango. 6,5 s, 0,8 GB.
**Bugs resueltos:** ninguno.
**Puntos de inflexión:**
- `test_cli_tools` falla si se ejecuta el Python del entorno sin activarlo (`cdo` no está en PATH): usar `mamba run -n era5 pytest` o activar el entorno. Relevante para la CI (F4).
**Decisiones generadas:** → D-012
**Siguiente paso:** F4 (CI/CD). Resolver antes `master` frente a `main` como rama por defecto.

### 2026-09-27 — Fase F4
**Hecho:**
- Rama `master` → `main`.
- `.github/workflows/ci.yml` con los jobs `lint`, `test`, `e2e` y `docker`. Diseño → D-013.
- `tests/test_e2e.py` (marker `e2e`): ingesta con `FixtureClient` (idempotente: la 2ª pasada da 4 skipped), CLI `transform` → Zarr 3×41×61×2, CLI `qc` → exit 1 solo por el paso de 18 UTC que falta en el fixture. Sustituye al e2e parcial de `test_qc.py`.
- `Dockerfile` (micromamba 2.3.2) + `.dockerignore`: construye en ~2,5 min, 1,9 GB, 26 tests pasan dentro.
- `README.md` mínimo con badge (el completo, en inglés, en F8).
- Local: 26 passed; cobertura qc 100 %, transform 99 %; ruff limpio.
**Bugs resueltos:**
- `docker build` fallaba en el `pip install -e .` del `environment.yml`: `WORKDIR /app` crea el directorio como root y micromamba (usuario `mambauser`) no puede escribir su requirements temporal → `COPY --chown … /app/` antes de `WORKDIR`.
**Puntos de inflexión:** ninguno.
**Decisiones generadas:** → D-013
**Siguiente paso:** crear el repo en GitHub, hacer push y confirmar la CI verde en `main`; entonces cerrar F4 y pasar a F5 (Anemoi).
