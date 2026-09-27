import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from era5_pipeline import cli
from era5_pipeline.config import load_config
from era5_pipeline.qc import (
    check_monotonic,
    check_nan,
    check_ranges,
    check_time,
    check_units,
    run_qc,
    stats,
)
from era5_pipeline.transform import CF, build, write_zarr

ROOT = Path(__file__).parents[1]
FIX = ROOT / "tests/fixtures"
BASE = load_config(ROOT / "configs/iberia.yaml")
CFG = BASE | {"period": {"start": "2020-01-01", "end": "2020-01-01"}}  # 4 pasos de 6 h
# valor plausible (dentro de rango) por variable
VALUE = {"t2m": 285, "u10": 3, "v10": -2, "msl": 101300, "sp": 95000, "tp": 0.001, "t": 260}


def good_ds() -> xr.Dataset:
    time = pd.date_range("2020-01-01", periods=4, freq="6h")
    lat, lon, level = [35.0, 40.0, 45.0], [-10.0, -5.0, 0.0, 5.0], [500.0, 850.0]
    ds = xr.Dataset(coords={"time": time, "latitude": lat, "longitude": lon, "level": level})
    shape2d = (4, 3, 4)
    for v, x in VALUE.items():
        if v != "t":
            ds[v] = (("time", "latitude", "longitude"), np.full(shape2d, x, "float32"))
    ds["t"] = (("time", "level", "latitude", "longitude"), np.full((4, 2, 3, 4), 260, "float32"))
    z = np.broadcast_to(np.array([55000, 15000], "float32")[None, :, None, None], (4, 2, 3, 4))
    ds["z"] = (("time", "level", "latitude", "longitude"), z.copy())
    ds["tp"][0] = np.nan  # ventana incompleta del 1er paso: esperada (D-010)
    for v, (std, units) in CF.items():
        ds[v].attrs.update(standard_name=std, units=units)
    return ds


def test_good_dataset_passes():
    r = run_qc(good_ds(), CFG)
    assert r["passed"], {k: c for k, c in r["checks"].items() if not c["passed"]}


def test_time_detects_missing_extra_and_duplicate():
    ds = good_ds()
    assert check_time(ds, CFG)["passed"]
    assert check_time(ds.drop_isel(time=2), CFG)["missing"] == ["2020-01-01 12:00:00"]
    late = ds.isel(time=[-1]).assign_coords(time=[pd.Timestamp("2020-01-02")])
    extra = xr.concat([ds, late], "time")
    assert check_time(extra, CFG)["extra"] == ["2020-01-02 00:00:00"]
    dup = xr.concat([ds, ds.isel(time=[0])], "time")
    r = check_time(dup, CFG)
    assert not r["passed"] and r["duplicated"] == ["2020-01-01 00:00:00"]


def test_monotonic_detects_descending_latitude():
    ds = good_ds()
    assert check_monotonic(ds, CFG)["passed"]
    r = check_monotonic(ds.isel(latitude=slice(None, None, -1)), CFG)
    assert r["not_strictly_increasing"] == ["latitude"]


def test_units_detects_wrong_and_missing():
    ds = good_ds()
    ds["msl"].attrs["units"] = "hPa"
    r = check_units(ds.drop_vars("z"), CFG)
    assert r["missing_vars"] == ["z"]
    assert r["wrong_units"] == {"msl": {"expected": "Pa", "found": "hPa"}}


def test_nan_leading_steps_exempt_only_for_configured_var():
    ds = good_ds()
    assert check_nan(ds, CFG)["passed"]  # NaN de tp en el 1er paso: exento
    ds["t2m"][0, 0, 0] = np.nan  # mismo paso, variable sin exención
    r = check_nan(ds, CFG)
    assert list(r["over_threshold"]) == ["t2m"] and r["nan_pct"]["tp"] == 0


def test_ranges_detects_out_of_range():
    ds = good_ds()
    ds["tp"][1, 0, 0] = -0.01
    ds["t"][2, 1, 1, 1] = 400
    r = check_ranges(ds, CFG)
    assert not r["passed"]
    assert {v for v, x in r["vars"].items() if x["n_out"]} == {"tp", "t"}
    assert r["vars"]["t"]["max"] == 400


def test_stats_per_level():
    s = stats(good_ds())
    assert s["z_500"]["mean"] == 55000 and s["z_850"]["mean"] == 15000
    assert s["t2m"] == {"units": "K", "mean": 285, "std": 0, "min": 285, "max": 285}
    assert np.isfinite(s["tp"]["mean"])  # NaN ignorados


def test_injected_faults_are_all_detected():
    ds = good_ds()
    ds["u10"][1, 1, 1] = np.nan
    ds["msl"].attrs["units"] = "hPa"
    ds = ds.drop_isel(time=2)
    r = run_qc(ds, CFG)
    assert not r["passed"]
    failed = {k for k, c in r["checks"].items() if not c["passed"]}
    assert failed == {"time", "nan", "units"}
    assert r["checks"]["time"]["missing"] == ["2020-01-01 12:00:00"]


@pytest.fixture(scope="module")
def fixture_zarr(tmp_path_factory):
    ds = build([FIX / "single_2020-01.grib"], [FIX / "pressure_2020-01.grib"], BASE)
    path = tmp_path_factory.mktemp("z") / "fix.zarr"
    write_zarr(ds, path)
    return path


def test_e2e_cli_on_fixture(fixture_zarr, tmp_path):
    # el fixture GRIB cubre 00-12 UTC del 01-01: solo falta el paso de 18 UTC
    cfg = CFG | {"qc": BASE["qc"] | {"reports": str(tmp_path)}}
    cfg_path = tmp_path / "cfg.json"  # JSON es YAML válido
    cfg_path.write_text(json.dumps(cfg))
    assert cli.main(["qc", "--zarr", str(fixture_zarr), "--config", str(cfg_path)]) == 1

    (report_json,) = tmp_path.glob("qc_*.json")
    r = json.loads(report_json.read_text())
    failed = {k for k, c in r["checks"].items() if not c["passed"]}
    assert failed == {"time"} and r["checks"]["time"]["missing"] == ["2020-01-01 18:00:00"]
    assert (tmp_path / report_json.name.replace(".json", ".md")).read_text().startswith("# QC")
