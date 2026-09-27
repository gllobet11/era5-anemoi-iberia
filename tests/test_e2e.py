"""Pipeline completo sobre fixtures: ingest (cliente falso) -> transform -> qc. Sin CDS."""

import json
import shutil
from pathlib import Path

import pytest
import xarray as xr

from era5_pipeline import cli
from era5_pipeline.config import load_config
from era5_pipeline.ingest import ingest

ROOT = Path(__file__).parents[1]
FIX = ROOT / "tests/fixtures"


class FixtureClient:
    """Sustituye a cdsapi.Client: 'descarga' el GRIB de fixture que corresponde al dataset."""

    def retrieve(self, dataset, request, target):
        if request["data_format"] == "netcdf":  # sin fixture NetCDF; transform solo lee GRIB
            Path(target).write_bytes(b"netcdf")
            return
        kind = "single" if "single" in dataset else "pressure"
        shutil.copy(FIX / f"{kind}_2020-01.grib", target)


@pytest.mark.e2e
def test_pipeline_on_fixtures(tmp_path):
    cfg = load_config(ROOT / "configs/iberia.yaml")
    cfg["period"] = {"start": "2020-01-01", "end": "2020-01-01"}
    cfg["paths"] |= {"raw": str(tmp_path / "raw"), "zarr": str(tmp_path / "zarr/fix.zarr")}
    cfg["qc"]["reports"] = str(tmp_path / "reports")
    cfg_path = tmp_path / "cfg.json"  # JSON es YAML válido
    cfg_path.write_text(json.dumps(cfg))

    assert ingest(cfg, FixtureClient()) == {"downloaded": 4, "skipped": 0}
    assert ingest(cfg, FixtureClient()) == {"downloaded": 0, "skipped": 4}

    assert cli.main(["transform", "--config", str(cfg_path)]) is None
    ds = xr.open_zarr(cfg["paths"]["zarr"])
    assert dict(ds.sizes) == {"time": 3, "latitude": 41, "longitude": 61, "level": 2}

    # el fixture cubre 00-12 UTC del 01-01: el QC debe fallar solo por el paso de 18 UTC
    zarr = cfg["paths"]["zarr"]
    assert cli.main(["qc", "--zarr", zarr, "--config", str(cfg_path)]) == 1
    (report,) = (tmp_path / "reports").glob("qc_*.json")
    r = json.loads(report.read_text())
    assert {k for k, c in r["checks"].items() if not c["passed"]} == {"time"}
    assert r["checks"]["time"]["missing"] == ["2020-01-01 18:00:00"]
    assert report.with_suffix(".md").read_text().startswith("# QC")
