"""Receta anemoi (D-014): metadatos y variables coherentes con configs/ y build sobre fixtures."""

import subprocess
from pathlib import Path

import numpy as np
import pytest
import xarray as xr
import yaml
from anemoi.datasets import open_dataset

from era5_pipeline.config import load_config
from era5_pipeline.transform import build

ROOT = Path(__file__).parents[1]
FIX = ROOT / "tests/fixtures"
RECIPE = yaml.safe_load((ROOT / "recipes/iberia.yaml").read_text())
NAMES = {"2t": "t2m", "10u": "u10", "10v": "v10"}


def test_recipe_metadata():
    for key in ("name", "description", "attribution", "licence"):
        assert RECIPE.get(key), key
    assert RECIPE["licence"] == "CC-BY-4.0"
    assert "Copernicus" in RECIPE["attribution"]
    assert RECIPE["dates"]["frequency"] == load_config(ROOT / "configs/iberia.yaml")["frequency"]


def test_recipe_matches_config():
    cfg = load_config(ROOT / "configs/iberia.yaml")
    single, pressure, accum = RECIPE["input"]["join"]
    assert set(single["grib"]["param"]) | {"tp"} == set(cfg["single_levels"]["variables"])
    assert set(pressure["grib"]["param"]) == set(cfg["pressure_levels"]["variables"])
    assert pressure["grib"]["level"] == cfg["pressure_levels"]["levels"]
    assert accum["accumulate"]["period"] == cfg["frequency"]
    assert accum["accumulate"]["source"]["grib-hourly-accum"]["param"] == ["tp"]


@pytest.mark.e2e
def test_recipe_builds_on_fixtures(tmp_path):
    """Receta con los fixtures (01-01 06 y 12 UTC): mismos valores que transform.build."""
    recipe = yaml.safe_load((ROOT / "recipes/iberia.yaml").read_text())
    recipe["dates"] |= {"start": "2020-01-01T06:00:00", "end": "2020-01-01T12:00:00"}
    # el fixture de presión es W-11 (ejercita el recorte de transform); anemoi no recorta -> CDO
    pressure = tmp_path / "pressure_2020-01.grib"
    subprocess.run(
        ["cdo", "-s", "sellonlatbox,-10,5,35,45", FIX / pressure.name, pressure], check=True
    )
    for src in recipe["input"]["join"]:
        spec = src.get("grib") or src["accumulate"]["source"]["grib-hourly-accum"]
        name = Path(spec["path"]).name.replace("{date:strftime(%Y-%m)}", "2020-01")
        spec["path"] = str(pressure if name == pressure.name else FIX / name)
    (tmp_path / "r.yaml").write_text(yaml.safe_dump(recipe))
    out = tmp_path / "fix.zarr"
    subprocess.run(["anemoi-datasets", "create", tmp_path / "r.yaml", out], check=True)

    a = open_dataset(out)
    cfg = load_config(ROOT / "configs/iberia.yaml")
    own = build([FIX / "single_2020-01.grib"], [FIX / "pressure_2020-01.grib"], cfg)
    own = own.sel(time=a.dates).load()
    lon = np.where(a.longitudes > 180, a.longitudes - 360, a.longitudes)
    pts = {"latitude": a.latitudes, "longitude": lon}
    pts = {k: xr.DataArray(v, dims="p") for k, v in pts.items()}
    for var in a.variables:
        base, _, lev = var.partition("_")
        mine = own[NAMES.get(base, base)].sel(pts)
        if lev:
            mine = mine.sel(level=int(lev))
        np.testing.assert_array_equal(a[:, a.name_to_index[var], 0, :], mine.values, err_msg=var)
