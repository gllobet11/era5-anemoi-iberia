"""F2: mismo paso con CDO y con Xarray sobre un mes, y diferencia máxima por variable.

1. remapbil a una rejilla 0,3° desde (-9.9, 35.1): pesos bilineales asimétricos (a mitad de celda
   los pesos son 0,25 y ambos coinciden al bit, lo que no discrimina)
   vs `DataArray.interp(method="linear")`.
2. tp horaria -> 6 h: `cdo timselsum,6,1` (salta 00 UTC del día 1) vs `transform.tp_to_6h`.

Uso: python scripts/compare_cdo_xarray.py data/raw/single_2020-01.grib > reports/cdo_vs_xarray.md
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr

from era5_pipeline.transform import CF, normalize, open_single, tp_to_6h

AREA = [45, -10, 35, 5]
CODES = {"var167": "t2m", "var151": "msl", "var165": "u10", "var228": "tp"}  # tabla GRIB1 ECMWF
GRID = """gridtype = lonlat
xsize = 50
ysize = 33
xfirst = -9.9
xinc = 0.3
yfirst = 35.1
yinc = 0.3
"""


def cdo(*args: str) -> None:
    subprocess.run(["cdo", "-s", "-f", "nc4", *args], check=True)


def open_cdo(path: Path) -> xr.Dataset:
    ds = xr.open_dataset(path)
    ds = ds.rename({k: v for k, v in CODES.items() if k in ds})
    return ds.rename(lat="latitude", lon="longitude").sortby("latitude").load()


def main(grib: str) -> None:
    grib = Path(grib)
    xa = normalize(open_single(grib), AREA).load()
    rows = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "grid.txt").write_text(GRID)
        cdo(f"remapbil,{d / 'grid.txt'}", "-selcode,167,151,165", str(grib), str(d / "rb.nc"))
        cb = open_cdo(d / "rb.nc")
        for v in ("t2m", "msl", "u10"):
            xi = xa[v].interp(latitude=cb.latitude, longitude=cb.longitude, method="linear")
            diff = np.abs(cb[v].values - xi.values)
            rows.append((f"remapbil {v}", CF[v][1], diff.max(), diff.mean()))

        cdo("timselsum,6,1", "-selcode,228", str(grib), str(d / "tp6.nc"))
        ct = open_cdo(d / "tp6.nc").tp
        xt = tp_to_6h(xa.tp).dropna("time", how="all")
        n = xt.sizes["time"]  # CDO emite además el grupo final incompleto; se compara lo común
        diff = np.abs(ct.values[:n] - xt.values)
        rows.append(("timselsum,6 tp", "m", diff.max(), diff.mean()))
        cdo_times = ct.time.values[:n]

    print(f"# CDO vs Xarray — {grib.name}\n")
    print("| Operación | Unidades | Máx abs | Media abs |\n|---|---|---|---|")
    for op, u, mx, mean in rows:
        print(f"| {op} | {u} | {mx:.3g} | {mean:.3g} |")
    print(f"\nEtiquetas de tiempo tp 6 h: CDO {cdo_times[0]} … vs Xarray {xt.time.values[0]} …")


if __name__ == "__main__":
    main(sys.argv[1])
