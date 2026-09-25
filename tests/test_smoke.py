import shutil
import subprocess
from pathlib import Path

from era5_pipeline.config import load_config

ROOT = Path(__file__).parents[1]


def test_imports():
    import anemoi.datasets  # noqa: F401
    import cfgrib  # noqa: F401
    import xarray  # noqa: F401
    import zarr

    assert zarr.__version__.startswith("2.")  # D-007


def test_cli_tools():
    for cmd in (["cdo", "--version"], ["ncks", "--version"]):
        assert shutil.which(cmd[0]), f"{cmd[0]} no está en PATH"
        subprocess.run(cmd, check=True, capture_output=True)


def test_config():
    cfg = load_config(ROOT / "configs/iberia.yaml")
    assert cfg["area"] == [45, -10, 35, 5]
    assert set(cfg["single_levels"]["variables"]) == {"2t", "10u", "10v", "msl", "tp", "sp"}
    assert cfg["pressure_levels"]["levels"] == [500, 850]
    assert cfg["frequency"] == "6h"
