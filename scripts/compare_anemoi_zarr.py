"""F5: dataset anemoi (receta) vs Zarr propio (transform) sobre las mismas fechas y puntos.

Para cada variable: estadísticos de ambos (`qc.stats` en el Zarr, los mismos sobre el array anemoi),
diferencia máxima punto a punto y los estadísticos que anemoi guarda en el dataset (periodo propio).

Uso: python scripts/compare_anemoi_zarr.py data/zarr/iberia-anemoi.zarr data/zarr/iberia.zarr \
       > reports/anemoi_vs_zarr.md
"""

import sys

import numpy as np
import xarray as xr
import zarr
from anemoi.datasets import open_dataset

from era5_pipeline.qc import stats

NAMES = {"2t": "t2m", "10u": "u10", "10v": "v10"}  # anemoi (ECMWF) -> cfgrib; el resto coincide


def to_grid(a, var: str, own: xr.Dataset) -> xr.DataArray:
    """Variable anemoi (fechas x puntos) como (time, latitude, longitude) en la rejilla propia."""
    lon = np.where(a.longitudes > 180, a.longitudes - 360, a.longitudes)
    x = a[:, a.name_to_index[var], 0, :]
    da = xr.DataArray(x, dims=("time", "p"), coords={"time": a.dates})
    da = da.assign_coords(latitude=("p", a.latitudes), longitude=("p", lon))
    return da.set_index(p=["latitude", "longitude"]).unstack("p").reindex_like(own)


def main(anemoi_path: str, zarr_path: str) -> None:
    a = open_dataset(anemoi_path)
    own = xr.open_zarr(zarr_path).sel(time=a.dates).load()
    mine = stats(own)
    ref = own.t2m.isel(time=0, drop=True)
    stored = a.statistics
    attrs = zarr.open(anemoi_path, mode="r").attrs
    s0, s1 = attrs["statistics_start_date"], attrs["statistics_end_date"]

    print("# Dataset anemoi vs Zarr propio\n")
    print(f"- anemoi: `{anemoi_path}` · {a.shape} (fechas × variables × ensemble × puntos)")
    print(f"- propio: `{zarr_path}` · mismas {len(a.dates)} fechas ({a.dates[0]} → {a.dates[-1]})")
    print(f"- Estadísticos guardados por anemoi: periodo {s0} → {s1}\n")
    print(
        "| anemoi | propio | unidades | media (propio) | media (anemoi) | std (propio) "
        "| std (anemoi) | max abs diff | media guardada | std guardada |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for var in a.variables:
        base, _, lev = var.partition("_")
        key = NAMES.get(var, var)
        grid = to_grid(a, var, ref)
        mine_da = own[NAMES.get(base, base)]
        if lev:
            mine_da = mine_da.sel(level=int(lev), drop=True)
        diff = float(abs(grid - mine_da).max())
        m, i = mine[key], a.name_to_index[var]
        print(
            f"| {var} | {key} | {m['units']} | {m['mean']:.6g} | {float(grid.mean()):.6g} "
            f"| {m['std']:.6g} | {float(grid.std()):.6g} | {diff:.3g} "
            f"| {stored['mean'][i]:.6g} | {stored['stdev'][i]:.6g} |"
        )


if __name__ == "__main__":
    main(*sys.argv[1:3])
