from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from era5_pipeline.config import load_config
from era5_pipeline.transform import build, normalize, open_single, tp_to_6h, write_zarr

ROOT = Path(__file__).parents[1]
FIX = ROOT / "tests/fixtures"
AREA = [45, -10, 35, 5]


def hourly(start, n):
    t = pd.date_range(start, periods=n, freq="h")
    return xr.DataArray(np.arange(1.0, n + 1), coords={"time": t}, dims="time")


def test_tp_6h_window_is_right_closed():
    # 19:00 del 31-01 a 12:00 del 01-02: la ventana de 00 UTC cruza el cambio de mes
    tp = hourly("2020-01-31T19:00", 18)
    out = tp_to_6h(tp)
    assert list(out.time.dt.strftime("%m-%d %H").values) == ["02-01 00", "02-01 06", "02-01 12"]
    np.testing.assert_allclose(
        out.values, [1 + 2 + 3 + 4 + 5 + 6, 7 + 8 + 9 + 10 + 11 + 12, 13 + 14 + 15 + 16 + 17 + 18]
    )
    assert out.sum() == tp.sum()  # la suma 6 h conserva la suma horaria


def test_tp_6h_incomplete_window_is_nan():
    out = tp_to_6h(hourly("2020-01-01T02:00", 5))  # 02..06: faltan las 01
    assert out.isnull().all()


def test_normalize_netcdf_style():
    ds = xr.Dataset(
        {"t": (("valid_time", "pressure_level", "latitude", "longitude"), np.zeros((1, 2, 3, 3)))},
        coords={
            "valid_time": pd.to_datetime(["2020-01-01"]),
            "pressure_level": [850.0, 500.0],
            "latitude": [45.0, 40.0, 35.0],
            "longitude": [350.0, 355.0, 0.0],
            "expver": ("valid_time", ["0001"]),
        },
    )
    out = normalize(ds, AREA)
    assert set(out.dims) == {"time", "level", "latitude", "longitude"}
    assert "expver" not in out.coords
    assert list(out.level) == [500, 850] and list(out.latitude) == [35, 40, 45]
    assert list(out.longitude) == [-10, -5, 0]


@pytest.fixture(scope="module")
def ds():
    cfg = load_config(ROOT / "configs/iberia.yaml")
    return build([FIX / "single_2020-01.grib"], [FIX / "pressure_2020-01.grib"], cfg).load()


def test_build_structure(ds):
    assert dict(ds.sizes) == {"time": 3, "latitude": 41, "longitude": 61, "level": 2}
    assert ds.latitude.to_index().is_monotonic_increasing
    assert (
        float(ds.longitude.min()) == -10 and float(ds.longitude.max()) == 5
    )  # pressure W-11 recortado
    assert list(ds.time.dt.hour.values) == [0, 6, 12]
    assert set(ds.data_vars) == {"t2m", "u10", "v10", "msl", "sp", "tp", "t", "z"}
    assert ds.t.dims == ("time", "level", "latitude", "longitude")
    assert ds.tp.dims == ("time", "latitude", "longitude")
    assert ds.u10.attrs["units"] == "m s-1" and ds.tp.attrs["standard_name"]


def test_build_values_match_raw(ds):
    raw = normalize(open_single(FIX / "single_2020-01.grib"), AREA).load()
    assert ds.tp.isel(time=0).isnull().all()  # 00 UTC sin horas previas en el fixture
    hours = raw.tp.sel(time=slice("2020-01-01T01", "2020-01-01T06")).sum("time")
    np.testing.assert_allclose(ds.tp.sel(time="2020-01-01T06"), hours, rtol=1e-6)
    xr.testing.assert_equal(ds.t2m.sel(time="2020-01-01T12"), raw.t2m.sel(time="2020-01-01T12"))


def test_write_zarr_idempotent(ds, tmp_path):
    out = tmp_path / "x.zarr"
    write_zarr(ds.chunk({"time": 2}), out)
    write_zarr(ds.chunk({"time": 2}), out)
    z = xr.open_zarr(out)
    assert not (tmp_path / "x.zarr.tmp").exists()
    xr.testing.assert_identical(z.load(), ds)


def test_no_stale_grib_grid_attrs(ds):
    assert ds.longitude.attrs["units"] == "degrees_east"
    for v in ds.data_vars.values():
        assert not any(k in v.attrs for k in ("GRIB_Nx", "GRIB_numberOfPoints"))
        assert "GRIB_paramId" in v.attrs


def test_open_single_tp_is_time_first():
    raw = open_single(FIX / "single_2020-01.grib")
    assert raw.tp.dims == ("time", "latitude", "longitude") and raw.tp.sizes["time"] == 14
    assert raw.tp.indexes["time"].is_unique
