# era5-anemoi-iberia

[![CI](https://github.com/gllobet11/era5-anemoi-iberia/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/gllobet11/era5-anemoi-iberia/actions/workflows/ci.yml)

Reproducible pipeline that downloads a regional ERA5 subset (Iberian Peninsula, 2020–2022, 6-hourly)
from the Copernicus CDS, converts GRIB to Zarr with Xarray/CDO, runs quality checks, and (work in
progress) builds an [anemoi-datasets](https://anemoi.readthedocs.io/projects/datasets/) dataset.

> Work in progress. Full documentation (architecture, decisions, limitations) comes at the end of
> the project; design decisions are logged in `Decisions.md` (Spanish).

## Quick start

```bash
micromamba env create -f environment.yml && micromamba activate era5
python -m era5_pipeline.cli ingest    --config configs/iberia.yaml   # needs ~/.cdsapirc
python -m era5_pipeline.cli transform --config configs/iberia.yaml
python -m era5_pipeline.cli qc        --zarr data/zarr/iberia.zarr  # exit 1 if a check fails
pytest -q && ruff check .
```

Docker (same `environment.yml`): `docker build -t era5-pipeline . && docker run --rm era5-pipeline pytest -q`

## CI

`lint` (ruff) · `test` (pytest, coverage ≥ 80 % on `transform`/`qc`) · `e2e` (mocked ingest →
transform → QC on small GRIB fixtures) · `docker` (build image, run tests inside).
CI never contacts the CDS and uses no secrets: all tests run on versioned fixtures (< 1 MB).
