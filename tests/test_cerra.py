"""F7 (D-016): la rejilla destino de CDO coincide con la del Zarr ERA5 del proyecto."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import xarray as xr

from era5_pipeline.config import load_config
from era5_pipeline.transform import normalize, open_single

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cerra  # noqa: E402


def test_remap_era5_onto_own_grid_is_identity(tmp_path):
    cfg = load_config(ROOT / "configs/iberia.yaml")
    grib = ROOT / "tests/fixtures/single_2020-01.grib"
    (tmp_path / "grid.txt").write_text(cerra.era5_grid(cfg))
    out = tmp_path / "rb.nc"
    subprocess.run(
        [
            "cdo",
            "-s",
            "-f",
            "nc4",
            f"{cerra.REMAP},{tmp_path / 'grid.txt'}",
            "-selcode,167",
            grib,
            out,
        ],
        check=True,
    )
    cb = xr.open_dataset(out).load().sortby("lat")
    ref = normalize(open_single(grib), cfg["area"]).t2m
    assert cb.var167.shape == ref.shape
    np.testing.assert_array_equal(cb.lat, ref.latitude)
    np.testing.assert_array_equal(cb.lon, ref.longitude)
    np.testing.assert_allclose(cb.var167, ref, atol=1e-3)


def test_request_has_no_area():  # CERRA (Lambert) no admite recorte en el CDS
    req = cerra.request(load_config(ROOT / "configs/iberia.yaml")["cerra"])
    assert "area" not in req and "grid" not in req
    assert len(req["day"]) == 31 and req["data_format"] == "grib"
