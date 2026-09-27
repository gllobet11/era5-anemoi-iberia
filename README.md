# era5-anemoi-iberia

[![CI](https://github.com/gllobet11/era5-anemoi-iberia/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/gllobet11/era5-anemoi-iberia/actions/workflows/ci.yml)

Reproducible pipeline that downloads a regional ERA5 subset (Iberian Peninsula, 2020–2022, 6-hourly)
from the Copernicus CDS, converts GRIB to Zarr with Xarray/CDO, runs quality checks, and builds an
[anemoi-datasets](https://anemoi.readthedocs.io/projects/datasets/) dataset from the same raw GRIB.

> Work in progress. Full documentation (architecture, decisions, limitations) comes at the end of
> the project; design decisions are logged in `Decisions.md` (Spanish).

## Quick start

```bash
micromamba env create -f environment.yml && micromamba activate era5
python -m era5_pipeline.cli ingest    --config configs/iberia.yaml   # needs ~/.cdsapirc
python -m era5_pipeline.cli transform --config configs/iberia.yaml
python -m era5_pipeline.cli qc        --zarr data/zarr/iberia.zarr  # exit 1 if a check fails
anemoi-datasets create  recipes/iberia.yaml data/zarr/iberia-anemoi.zarr
anemoi-datasets inspect data/zarr/iberia-anemoi.zarr
pytest -q && ruff check .
```

Docker (same `environment.yml`): `docker build -t era5-pipeline . && docker run --rm era5-pipeline pytest -q`

## anemoi-datasets

`recipes/iberia.yaml` builds the dataset straight from the raw CDS GRIB files (`grib` source joined
with an `accumulate` block for 6 h `tp`). anemoi-datasets 0.5.44's `grib` source ignores the hourly
intervals that `accumulate` asks for, so the repo registers a 10-line subclass,
`grib-hourly-accum` (`src/era5_pipeline/anemoi_sources.py`), via an entry point. The dataset starts
at 2020-01-01 06 UTC because the 00 UTC `tp` window needs December 2019, which isn't downloaded.

Result (`reports/anemoi_inspect.txt`): 4383 × 10 × 1 × 2501, 6 h, 0 missing dates, 231 MiB, built in
7 min 40 s. Compared with the Xarray Zarr on the same dates and points (`reports/anemoi_vs_zarr.md`):

| Variable | Mean (own Zarr) | Mean (anemoi) | Std (own) | Std (anemoi) | Max abs diff |
|---|---|---|---|---|---|
| 2t (K) | 289.352 | 289.352 | 6.9759 | 6.9759 | 0 |
| 10u (m s-1) | 0.412871 | 0.412871 | 3.76856 | 3.76856 | 0 |
| 10v (m s-1) | -0.463418 | -0.463418 | 3.3119 | 3.3119 | 0 |
| msl (Pa) | 101800 | 101800 | 626.882 | 626.882 | 0 |
| sp (Pa) | 97920.2 | 97920.2 | 4484.91 | 4484.91 | 0 |
| tp (m, 6 h) | 4.37488e-04 | 4.37493e-04 | 1.5785e-03 | 1.5785e-03 | 9.5e-07 |
| t_500 (K) | 257.84 | 257.84 | 5.25238 | 5.25238 | 0 |
| t_850 (K) | 283.852 | 283.852 | 6.94203 | 6.94203 | 0 |
| z_500 (m2 s-2) | 56288.1 | 56288.1 | 1206.7 | 1206.7 | 0 |
| z_850 (m2 s-2) | 14914 | 14914 | 524.832 | 524.832 | 0 |

Every field is identical except `tp`. `accumulate` writes its sums to a temporary GRIB packed at
16 bits, so 1 % of `tp` values move by less than one quantisation step (field range / 2^16). The
statistics that `inspect` prints differ from the table because anemoi computes them on its own
period only (2020-01-01 06 → 2022-05-26 12), not on the full dataset.

`notebooks/01_open_anemoi.ipynb` opens the dataset with `anemoi.datasets.open_dataset`, subsets by
date and variable and plots `2t`.

## CI

`lint` (ruff) · `test` (pytest, coverage ≥ 80 % on `transform`/`qc`) · `e2e` (mocked ingest →
transform → QC, and the anemoi recipe, on small GRIB fixtures) · `docker` (build image, run tests inside).
CI never contacts the CDS and uses no secrets: all tests run on versioned fixtures (< 1 MB).
