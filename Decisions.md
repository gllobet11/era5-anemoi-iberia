# Decisions.md — era5-anemoi-iberia

Registro de decisiones de arquitectura (formato ADR ligero). Una entrada por decisión con alternativas reales descartadas. Si una decisión se revierte, no se borra: se marca **Sustituida por D-0XX**.

Estados: `Propuesta` (pendiente de validar en la fase indicada) · `Aceptada` · `Sustituida`.

Plantilla:
```
## D-0XX — Título
- Fecha / Fase:
- Estado:
- Contexto:
- Decisión:
- Alternativas descartadas:
- Consecuencias:
```

---

## D-001 — Dominio y periodo: Iberia 2020–2022 a 6 h
- Fecha / Fase: 25/09/2026 · planificación
- Estado: Propuesta
- Contexto: el puesto es de datasets **regionales**; hay que mantener volumen y colas del CDS manejables en 1–2 semanas.
- Decisión: caja N45 W−10 S35 E5, 2020–2022, frecuencia 6 h (timestep típico de AIFS), 6 variables de superficie + `t`/`z` en 500 y 850 hPa.
- Alternativas descartadas: global a baja resolución (menos alineado con "regional"); solo Catalunya (demasiado pequeño para que chunking y QC sean interesantes); horario (x6 volumen sin aportar señal para el CV).
- Consecuencias: < 1 GB; pipeline ejecutable en portátil y CI con fixtures.

## D-002 — GRIB como formato raw canónico; NetCDF solo para comparación
- Fecha / Fase: 25/09/2026 · planificación (validar en F1–F2)
- Estado: Aceptada (F2: valores GRIB y NetCDF idénticos, ver `reports/grib_vs_netcdf_*.md`)
- Contexto: el puesto pide NetCDF y GRIB; anemoi-datasets documenta mejor la fuente GRIB y ha tenido incidencias con NetCDF.
- Decisión: descargar todo en GRIB; un mes en NetCDF para demostrar ambos formatos y documentar diferencias.
- Alternativas descartadas: todo NetCDF (más cómodo en Xarray pero riesgo en F5); ambos para todo (doble descarga sin valor).
- Consecuencias: dependencia de eccodes/cfgrib → ver D-003.

## D-003 — Entorno con micromamba + imagen Docker
- Fecha / Fase: 25/09/2026 · planificación
- Estado: Aceptada (F0)
- Contexto: eccodes, CDO y NCO son binarios de sistema; pip no los resuelve de forma fiable.
- Decisión: `environment.yml` con conda-forge vía micromamba, misma definición en Docker y en CI.
- Alternativas descartadas: `uv`/pip + apt (dos fuentes de verdad, versiones de eccodes divergentes); Poetry (mismo problema).
- Consecuencias: CI algo más lento → cachear el entorno (F4).
- Nota F0 (25/09/2026): en local se usa `mamba` (miniforge ya instalado) con el mismo `environment.yml`; micromamba queda para Docker/CI. Estado → Aceptada.

## D-004 — Los tests y la CI nunca acceden al CDS
- Fecha / Fase: 25/09/2026 · planificación
- Estado: Propuesta
- Contexto: el CDS tiene colas y requiere credenciales; tests dependientes de red serían lentos y frágiles.
- Decisión: `cdsapi` mockeado en unit tests; e2e sobre fixtures GRIB/NetCDF < 1 MB versionados.
- Alternativas descartadas: secreto del CDS en GitHub Actions con descarga mínima (lento, no determinista).
- Consecuencias: la descarga real se valida a mano y queda registrada en `progress.md`.

## D-005 — Dos salidas: Zarr propio (Xarray) + dataset anemoi desde receta
- Fecha / Fase: 25/09/2026 · planificación (validar en F5)
- Estado: Aceptada (F5: mismos valores en 9 de 10 variables, `tp` < 1 paso de cuantización; ver D-014)
- Contexto: el pipeline propio demuestra dominio de Xarray/CDO; anemoi demuestra encaje con el ecosistema del puesto.
- Decisión: mantener ambos a partir de los mismos GRIB raw y comparar estadísticos entre ellos.
- Alternativas descartadas: solo anemoi (oculta el trabajo de transformación); solo Zarr propio (pierde el valorable principal).
- Consecuencias: la comparación de estadísticos actúa como test de consistencia cruzado.

## D-006 — Slurm solo como simulación local y como stretch
- Fecha / Fase: 25/09/2026 · planificación
- Estado: Aceptada (F6, implementación → D-015)
- Contexto: sin acceso a HPC real; Slurm es gap esencial pero no cerrable de verdad en 2 semanas.
- Decisión: F6 con `slurm-docker-cluster` solo si el MVP (F0–F5) está cerrado el 09/10; se etiqueta como simulación en README y CV.
- Alternativas descartadas: omitirlo (deja el gap intacto); presentarlo como experiencia HPC (overclaiming).
- Consecuencias: el gap de HPC se reduce en la narrativa de entrevista, no desaparece.

## D-007 — anemoi-datasets 0.5.44 fijado ⇒ zarr v2 (2.18.x)
- Fecha / Fase: 25/09/2026 · F0
- Estado: Aceptada
- Contexto: CLAUDE.md pide comprobar compatibilidad zarr v2/v3 antes de fijar versión. La última versión de anemoi-datasets (0.5.44, en conda-forge y PyPI) declara `zarr<=2.18.7` y `numcodecs<0.16`.
- Decisión: fijar `anemoi-datasets=0.5.44` y `zarr=2.18` en `environment.yml`; el Zarr propio (F2) también se escribe en formato v2 para que ambos sean comparables y abribles con el mismo entorno. El test de humo falla si zarr deja de ser 2.x.
- Alternativas descartadas: zarr 3 + versión antigua/no fijada de anemoi (no resuelve); dos entornos separados (duplica mantenimiento y CI).
- Consecuencias: no se usan features de zarr v3 (sharding). Revisar si anemoi-datasets publica soporte v3 antes de F5.

## D-008 — `tp` se descarga horaria; el resto de single levels también, pressure levels a 6 h
- Fecha / Fase: 25/09/2026 · F0 (validar en F2)
- Estado: Aceptada (F2)
- Contexto: `tp` en ERA5 es acumulada por hora; para obtener la acumulación 6 h hay que **sumar** las 6 horas, no submuestrear.
- Decisión: una petición horaria por mes para single levels (todas las variables, para no duplicar peticiones); pressure levels solo a 00/06/12/18. Las instantáneas de superficie se submuestrean a 6 h en F2.
- Alternativas descartadas: pedir solo 00/06/12/18 para todo (tp sería incorrecta); petición separada horaria solo para tp (el doble de peticiones en cola por un ahorro de volumen pequeño en este dominio).
- Consecuencias: raw single levels ×6 de volumen (sigue muy por debajo de 1 GB/año para esta caja). La convención de ventana de 6 h se define en F2.

## D-009 — Ingesta: manifest con sha256, escritura `.part` + rename, 4 peticiones concurrentes
- Fecha / Fase: 25/09/2026 · F1
- Estado: Aceptada
- Contexto: 72 peticiones (36 meses × 2 tipos) + 2 NetCDF; la 1ª petición tardó ~10 min entre cola y proceso → en serie serían ~12 h. Relanzar no debe duplicar ni dejar ficheros a medias.
- Decisión: `data/raw/manifest.json` con clave = nombre lógico (`{single|pressure}_AAAA-MM.{grib|nc}`) y `path`, `size`, `sha256`, `downloaded_at`. Skip solo si el fichero existe y tamaño + sha256 coinciden; si no, se vuelve a descargar. Descarga a `<nombre>.part` y `rename` atómico; manifest también se reescribe vía tmp + rename bajo lock. Reintentos con backoff exponencial (`backoff_s * 2**n`). `ThreadPoolExecutor` con `workers` en config (4).
- Alternativas descartadas: skip por mera existencia del fichero (no detecta descargas truncadas/corruptas); una petición por año (más riesgo de rechazo por límite de tamaño del CDS y reintentos más caros); Slurm/colas propias (fuera de F1, ver D-006).
- Consecuencias: ficheros fuera del manifest se re-descargan (el `single_2020-01.grib` de F0 se registró a mano tras verificar 744 mensajes/variable). Si el CDS devuelve zip en NetCDF (stepTypes mixtos) se guarda como `.nc.zip` y se resuelve en F2.

## D-010 — Normalización: nombres cfgrib, unidades nativas ERA5 con metadatos CF, `tp` 6 h en (T−6h, T]
- Fecha / Fase: 25/09/2026 · F2
- Estado: Aceptada
- Contexto: hay que fijar un esquema único para GRIB (cfgrib) y NetCDF (CDS) y una convención de ventana para `tp` antes de comparar con anemoi en F5.
- Decisión:
  - Nombres de variable de cfgrib (`t2m, u10, v10, msl, sp, tp, t, z`), que coinciden con los del NetCDF del CDS. Dims `time, level, latitude, longitude`; lat y niveles ascendentes, lon en −180..180, recorte explícito a `cfg["area"]`.
  - Unidades nativas ERA5 (K, Pa, m s-1, m, m2 s-2), reescritas en sintaxis CF + `standard_name` CF; `GRIB_*` de rejilla eliminados tras el recorte (quedaban obsoletos).
  - `tp`: serie horaria en `valid_time` (cfgrib la entrega como `(time, step)` de pasadas 06/18) → `resample("6h", closed="right", label="right").sum(min_count=6)`. El valor en T es la acumulación (T−6h, T], convención ECMWF/anemoi. Ventana incompleta → NaN (el 2020-01-01 00 UTC lo será siempre: necesita diciembre 2019). Se concatena todo el periodo antes de agregar para que las ventanas de 00 UTC del día 1 usen las horas del mes anterior.
  - Instantáneas: selección de 00/06/12/18.
- Alternativas descartadas: nombres cortos ECMWF (`2t`, `10u`: empiezan por dígito, incómodos en Python y distintos del NetCDF); convertir `tp` a mm (añade un factor 1000 a cada comparación con anemoi); ventana (T, T+6h] o centrada (CDO etiqueta en el punto medio, 03:30); submuestrear `tp` (incorrecto para acumulados).
- Consecuencias: validado contra CDO `timselsum,6,1`: diferencia 0 en ene-2020 (`reports/cdo_vs_xarray.md`). Test sintético con ventana cruzando cambio de mes y conservación de la suma.

## D-011 — Zarr: reescritura completa atómica (tmp + rename) en vez de append/region
- Fecha / Fase: 25/09/2026 · F2
- Estado: Aceptada (revisada en F6: se mantiene → D-015)
- Contexto: CLAUDE.md sugería escritura por región/append controlado. El dataset completo es < 1 GB y `tp` necesita las horas del mes anterior, así que procesar mes a mes obliga a solapar ficheros.
- Decisión: `transform` abre todos los GRIB de forma perezosa, construye el dataset completo y lo escribe en `<zarr>.tmp` que luego reemplaza al destino (zarr v2, metadatos consolidados, chunks de `configs/`).
- Alternativas descartadas: `append_dim="time"` (relanzar un mes duplica pasos; requiere lógica de dedupe); `region=` por mes (requiere pre-crear el store y gestionar el solape de `tp`: complejidad sin beneficio a este volumen).
- Consecuencias: relanzar reconstruye todo (segundos-minutos para 3 años). Si en F6 se paraleliza por mes con Slurm, pasar a `region=` con store precreado.

## D-012 — QC: 5 checks críticos, umbrales en config, unidades desde `transform.CF`
- Fecha / Fase: 27/09/2026 · F3
- Estado: Aceptada
- Contexto: el QC tiene que fallar (exit ≠ 0) ante datos corruptos sin dar falsos positivos con el NaN esperado de `tp` en el primer paso (D-010), y los umbrales no pueden estar en el código (regla 5 de CLAUDE.md).
- Decisión:
  - Checks: timesteps esperados (desde `period` + `frequency`) frente a presentes, extra y duplicados; coordenadas estrictamente crecientes; unidades y variables presentes; % NaN; rangos físicos. **Todos críticos**: con que falle uno, `passed=False` y exit 1. Los estadísticos (media, std, min, max; `t`/`z` por nivel) son informativos.
  - `configs/iberia.yaml → qc`: `max_nan_pct` (0), `leading_nan_steps` (`tp: 1`) y `ranges` por variable en unidades nativas. Los rangos de `t`/`z` son uno por variable, no uno por nivel.
  - Unidades esperadas = `transform.CF`, que es la fuente de verdad del esquema, sin copiarlas en la config.
  - El NaN se exime por **posición** (primeros N pasos de la variable), no con un % global: un NaN en cualquier otro sitio falla aunque el % sea minúsculo (1 paso = 0,023 % del periodo).
  - Informe `reports/qc_<fecha de ejecución>.{json,md}`.
- Alternativas descartadas: niveles warning/critical (ningún check actual justifica solo avisar); `max_nan_pct` > 0 para absorber el NaN de `tp` (ocultaría huecos reales); unidades duplicadas en config (dos fuentes de verdad); rangos por nivel (más config sin un caso que lo pida; un swap de niveles lo detectarían los estadísticos por nivel).
- Consecuencias: el QC carga el Zarr entero (0,8 GB de pico, 6,5 s). Si crece el dominio o el periodo, reducir por chunks.

## D-013 — CI: 4 jobs, entorno micromamba cacheado, cobertura sobre la suite completa
- Fecha / Fase: 27/09/2026 · F4
- Estado: Aceptada
- Contexto: la CI debe usar el mismo `environment.yml` que local y Docker (D-003), no tocar el CDS (D-004) y verificar la cobertura ≥ 80 % en `transform`/`qc`.
- Decisión:
  - `lint`: `ruff-action` con la versión fijada en `.pre-commit-config.yaml` (0.13.0), sin crear el entorno conda (segundos en vez de minutos).
  - `test`: `setup-micromamba` con `cache-environment` y shell de login (`bash -el`) para tener `cdo`/`ncks` en PATH. Ejecuta **toda** la suite, e2e incluido, con `--cov-fail-under=80` sobre `transform` y `qc`.
  - `e2e`: solo `pytest -m e2e` (ingesta con cliente falso que copia los fixtures → CLI `transform` → CLI `qc`). Duplica ~2 s del job `test`, pero deja el pipeline visible como paso propio.
  - `docker`: `docker build` + `pytest` dentro de la imagen, sin push. Base `mambaorg/micromamba:2.3.2` fijada.
- Alternativas descartadas: cobertura solo en unit tests (`qc()` y `to_markdown` solo se ejercitan en el e2e: 79,6 %); ruff del entorno conda en `lint` (versión no fijada, distinta de la de pre-commit); push de la imagen a un registry (nadie la consume); caché de capas Docker en GHA (optimización sin necesidad demostrada).
- Consecuencias: el job `docker` resuelve el entorno desde cero en cada ejecución (~2,5 min en local). La imagen pesa 1,9 GB. Las versiones no fijadas de `environment.yml` pueden cambiar entre ejecuciones de CI: si rompe algo, fijar o generar un lock.

## D-014 — Receta anemoi: fuente `grib` + `accumulate` con plugin `grib-hourly-accum`, inicio 06 UTC
- Fecha / Fase: 27/09/2026 · F5
- Estado: Aceptada
- Contexto: la receta tiene que leer los mismos GRIB raw que el Zarr propio (D-005) y agregar `tp` horaria a 6 h. En anemoi-datasets 0.5.44, `accumulate` calcula bien los intervalos (covering `{mars: {class: ea}}`: pasadas 06/18, pasos horarios), pero `GribSource` no implementa `execute_intervals`. La llamada acaba en `execute_valid_dates` solo con los T objetivo, así que llega 1 de las 6 horas y falla con `Accumulator not complete`.
- Decisión:
  - `src/era5_pipeline/anemoi_sources.py`: subclase de `GribSource` que pide los `valid_time` de todos los intervalos (`{i.max for i in intervals}`). Se registra como `grib-hourly-accum` en el entry point `anemoi.datasets.create.sources` de `pyproject.toml`. Nada más cambia: el emparejado de campos con intervalos y la suma los sigue haciendo `accumulate`.
  - Rutas con patrón `data/raw/single_{date:strftime(%Y-%m)}.grib`: cada grupo mensual abre solo los meses que necesita, incluido el anterior para la ventana de 00 UTC del día 1.
  - `dates.start: 2020-01-01T06`: la ventana de 00 UTC necesita dic-2019. Anemoi no admite huecos en `tp` (el Zarr propio lo deja como NaN, D-010).
  - Metadatos: `licence: CC-BY-4.0` y atribución a C3S/ERA5 (Hersbach et al., 2020).
- Alternativas descartadas: fuente `grib-index` (tendría que construir un índice SQLite, depende de `cachetools`, que no está en el entorno, y filtra por `step` igual a la longitud del intervalo, que no encaja con los pasos 5-6, 6-7… de ERA5); preagregar `tp` a 6 h con CDO y leerla con `grib` (evita `accumulate`, que es justo la parte de anemoi que interesa demostrar); fuente `xarray-zarr` sobre el Zarr propio (anemoi pasaría a ser una copia del pipeline propio y la comparación cruzada de D-005 perdería el sentido); descargar dic-2019 para empezar a 00 UTC (una petición al CDS solo para 1 paso de 4384).
- Consecuencias: el dataset anemoi tiene 4383 pasos y el propio 4384. `accumulate` reescribe sus sumas en un GRIB temporal a 16 bits, así que `tp` difiere del Zarr propio en menos de rango/2¹⁶ en el 1 % de los puntos (máx. 9,5e-7 m); las demás variables son idénticas (`reports/anemoi_vs_zarr.md`). El plugin depende de una API interna de anemoi (`GribSource`, `Intervals`): si se sube la versión fijada (D-007), el test `test_recipe_builds_on_fixtures` lo detecta.

## D-015 — Slurm: job array por mes solo en ingest; transform y QC como jobs únicos encadenados
- Fecha / Fase: 27/09/2026 · F6
- Estado: Aceptada
- Contexto: F6 simula un HPC con `slurm-docker-cluster` (1 login + 2 nodos de cómputo que en realidad comparten las 4 CPU y los 12 GB del portátil). Había que decidir qué se reparte por mes, cómo llegan el código y el entorno a los nodos, y qué pasa con el manifest si varios procesos escriben a la vez.
- Decisión:
  - `slurm/submit.sh` encadena `ingest_array.sbatch` (`--array=0-(N-1)%4`) → `transform.sbatch` (`afterok`) → `qc.sbatch` (`afterok`). N sale de `cli months`, y cada tarea traduce `SLURM_ARRAY_TASK_ID` a su mes con el mismo subcomando: el periodo sigue viviendo solo en `configs/`. `%4` es el mismo límite de peticiones simultáneas al CDS que `workers` (D-009).
  - `ingest --month YYYY-MM` filtra los trabajos de un mes (incluido el NetCDF si toca). `Manifest.record` relee `manifest.json` bajo `fcntl.flock` y fusiona antes de escribir: el `threading.Lock` anterior solo protegía entre hilos de un mismo proceso, y dos tareas del array perdían las entradas de la otra.
  - Transform sigue siendo un único job con reescritura completa (D-011 se mantiene): la ventana de `tp` de 00 UTC necesita el mes anterior, el paso dura minutos y los nodos simulados comparten las mismas CPU, así que partirlo por mes con `region=` añade complejidad sin ganar nada medible.
  - Disposición de HPC con rutas fijas dentro del clúster (`slurm/compose.override.yml`): el repo en `/gpfs/projects/era5-anemoi-iberia` (bind mount; es la única ruta que depende del host), el entorno en `/gpfs/apps/envs/era5` (volumen compartido; `slurm/cluster_setup.sh` lo construye con micromamba desde `environment.yml`) y un modulefile Lmod `era5`. Los `.sbatch` solo hacen `module load era5`. Las rutas del manifest son relativas al repo, así que valen igual en el host y en el clúster. Los jobs corren con el UID del host para no dejar ficheros de root en `data/`.
  - Memoria: `cluster_setup.sh` activa `JobAcctGatherType=jobacct_gather/linux`, que viene sin definir en la imagen, y cada job pide `--mem`. Sin `--mem`, con `CR_CORE_MEMORY` y `DefMemPerNode=UNLIMITED`, cada tarea de ingest reservaba el nodo entero (11963M) y solo corrían 2 de las 4 permitidas.
- Alternativas descartadas: array también en transform con `region=` sobre un store precreado (solape de `tp` y precreación del store, sin ganancia en un solo host); montar el entorno del host en su misma ruta absoluta (primera versión de F6: funcionaba, pero ataba los scripts a rutas y glibc del portátil); construir el entorno dentro de la imagen del clúster (otra build de ~2 GB que duplica el `Dockerfile` del proyecto; en un HPC el software vive en el sistema de ficheros compartido, no en la imagen del nodo); Apptainer en los nodos (la imagen lo trae, pero habría que convertir la imagen Docker y montar igualmente los datos: más pasos para el mismo resultado); un manifest por mes (cambia el formato que ya usan transform, los tests y la receta).
- Consecuencias: pasar los scripts a un HPC real exige cambiar solo `module load era5` (y la ruta del proyecto desde la que se lanza `submit.sh`). El entorno del clúster (2,2 GB) se construye una vez y sobrevive a `compose down`, porque está en un volumen; `compose down -v` lo borra. `slurm-docker-cluster` necesita BuildKit (`COPY --chmod`): sin el plugin buildx, `docker compose build` falla.
