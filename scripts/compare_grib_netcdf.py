"""F2: mismo mes en GRIB y NetCDF (CDS) -> ¿mismos valores y metadatos?

Uso: python scripts/compare_grib_netcdf.py single 2020-01 > reports/grib_vs_netcdf_single.md
Acepta `.nc` o `.nc.zip` (el CDS empaqueta varios .nc si hay stepTypes mixtos; ver D-009).
"""

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import xarray as xr

from era5_pipeline.transform import normalize, open_pressure, open_single

AREA = [45, -10, 35, 5]
RAW = Path("data/raw")


def open_nc(path: Path, tmp: Path) -> tuple[xr.Dataset, list[Path]]:
    files = [path]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        files = sorted(tmp.glob("*.nc"))
    return xr.merge([xr.open_dataset(f) for f in files], compat="override"), files


def main(kind: str, month: str) -> None:
    grib = RAW / f"{kind}_{month}.grib"
    nc = next(RAW.glob(f"{kind}_{month}.nc*"))
    g_raw = (open_single if kind == "single" else open_pressure)(grib)
    with tempfile.TemporaryDirectory() as d:
        n_raw, nc_files = open_nc(nc, Path(d))
        cdl = [subprocess.run(["ncdump", "-h", str(f)], capture_output=True, text=True).stdout
               for f in nc_files]  # fmt: skip
        g, n = normalize(g_raw, AREA).load(), normalize(n_raw, AREA).load()

    print(f"# GRIB vs NetCDF — {kind} {month}\n")
    print(f"- Ficheros: `{grib.name}` ({grib.stat().st_size / 1e6:.1f} MB) vs `{nc.name}` "
          f"({nc.stat().st_size / 1e6:.1f} MB, {len(nc_files)} fichero(s) .nc)")  # fmt: skip
    print(f"- Dims crudas GRIB: `{dict(g_raw.sizes)}` · NetCDF: `{dict(n_raw.sizes)}`")
    print(f"- Solo GRIB: {sorted(set(g) - set(n))} · solo NetCDF: {sorted(set(n) - set(g))}")
    common_t = np.intersect1d(g.time.values, n.time.values)
    nt_g, nt_n = g.sizes["time"], n.sizes["time"]
    print(f"- Pasos de tiempo: GRIB {nt_g} · NetCDF {nt_n} · comunes {len(common_t)}\n")

    print("| Var | dtype GRIB/NC | Máx abs | units GRIB | units NC | Atributos solo en NC |")
    print("|---|---|---|---|---|---|")
    for v in sorted(set(g) & set(n)):
        a, b = g[v].sel(time=common_t), n[v].sel(time=common_t)
        diff = float(np.nanmax(np.abs(a.values - b.values)))
        only_nc = sorted(set(b.attrs) - set(a.attrs))
        print(f"| {v} | {a.dtype}/{b.dtype} | {diff:.3g} | {a.attrs.get('units')} | "
              f"{b.attrs.get('units')} | {', '.join(only_nc) or '—'} |")  # fmt: skip

    print("\n## Cabecera NetCDF (`ncdump -h`)\n")
    for text in cdl:
        print(f"```\n{text.strip()}\n```\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
