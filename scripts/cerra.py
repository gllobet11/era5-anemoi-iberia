"""F7: un mes de CERRA (Lambert conformal, ~5,5 km) regrideado con CDO a la rejilla ERA5 del repo.

1. download: una petición al CDS, dominio CERRA completo (no admite `area`), manifest + sha256.
2. regrid:   `cdo remapcon` a la rejilla 0,25° de `configs/` -> Zarr (conservativo: agrega, D-016).
3. compare:  2t CERRA vs ERA5 en los mismos instantes -> reports/cerra_vs_era5.md + mapa PNG.

Uso: python scripts/cerra.py {download,regrid,compare,all} [--config configs/iberia.yaml]
"""

import argparse
import calendar
import logging
import subprocess
import tempfile
from pathlib import Path

from era5_pipeline.config import load_config
from era5_pipeline.ingest import Manifest

log = logging.getLogger("cerra")
REMAP = "remapcon"  # D-016: remapbil da RMSE 1,54 K frente a 1,39 K


def request(c: dict) -> dict:
    y, m = map(int, c["month"].split("-"))
    return {
        "variable": list(c["variables"].values()),
        "level_type": "surface_or_atmosphere",
        "data_type": ["reanalysis"],
        "product_type": "analysis",
        "year": [str(y)],
        "month": [f"{m:02d}"],
        "day": [f"{d:02d}" for d in range(1, calendar.monthrange(y, m)[1] + 1)],
        "time": c["hours"],
        "data_format": "grib",
    }


def raw_path(c: dict) -> Path:
    return Path(c["raw"]) / f"cerra_{c['month']}.grib"


def download(cfg: dict) -> Path:
    c = cfg["cerra"]
    out = raw_path(c)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(out.parent / "manifest.json")
    if manifest.is_valid(out.name):
        log.info("%s ya descargado", out)
        return out
    import cdsapi

    tmp = out.with_name(out.name + ".part")
    cdsapi.Client().retrieve(c["dataset"], request(c), str(tmp))
    tmp.replace(out)
    manifest.record(out.name, out)
    return out


def era5_grid(cfg: dict) -> str:
    """Descripción CDO de la rejilla ERA5 del proyecto (centros de celda, lat ascendente)."""
    n, w, s, e = cfg["area"]
    dlat, dlon = cfg["grid"]
    return (
        "gridtype = lonlat\n"
        f"xsize = {round((e - w) / dlon) + 1}\nxfirst = {w}\nxinc = {dlon}\n"
        f"ysize = {round((n - s) / dlat) + 1}\nyfirst = {s}\nyinc = {dlat}\n"
    )


def regrid(cfg: dict) -> Path:
    import xarray as xr

    from era5_pipeline.transform import CF, write_zarr

    c = cfg["cerra"]
    src, out = raw_path(c), Path(c["zarr"])
    with tempfile.TemporaryDirectory() as d:
        grid, nc = Path(d) / "grid.txt", Path(d) / "cerra.nc"
        grid.write_text(era5_grid(cfg))
        subprocess.run(["cdo", "-s", "-f", "nc4", f"{REMAP},{grid}", str(src), str(nc)], check=True)
        ds = xr.open_dataset(nc).load()
    ds = ds.rename({"2t": "t2m", "lat": "latitude", "lon": "longitude"}).sortby("latitude")
    ds = ds[["t2m", "msl"]].squeeze("height", drop=True)
    for v in ds.data_vars:
        std, units = CF[v]
        ds[v].attrs = {"standard_name": std, "units": units}
    ds.attrs = {
        "title": f"CERRA {c['month']} regridded to the ERA5 {cfg['name']} grid",
        "source": f"CERRA reanalysis (Copernicus C3S), CDS; cdo {REMAP} from Lambert conformal",
        "Conventions": "CF-1.7",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    write_zarr(ds.chunk({"time": -1}), out)
    log.info("escrito %s: %s", out, dict(ds.sizes))
    return out


GRIDDES_KEYS = ("gridtype", "gridsize", "xsize", "ysize", "xinc", "yinc", "grid_mapping_name",
                "standard_parallel", "longitude_of_central_meridian",
                "latitude_of_projection_origin", "earth_radius")  # fmt: skip


def compare(cfg: dict) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr

    c = cfg["cerra"]
    ce = xr.open_zarr(c["zarr"]).load()
    er = xr.open_zarr(cfg["paths"]["zarr"])[["t2m", "msl"]].sel(time=ce.time).load()
    ce, er = xr.align(ce, er, join="exact")  # misma rejilla o error, nunca intersección
    griddes = subprocess.run(
        ["cdo", "-s", "griddes", str(raw_path(c))], check=True, capture_output=True, text=True
    ).stdout
    grid_lines = [ln.strip() for ln in griddes.splitlines() if ln.strip().startswith(GRIDDES_KEYS)]

    d = ce - er
    rows = []
    for v, unit in (("t2m", "K"), ("msl", "Pa")):
        x = d[v]
        corr = np.corrcoef(ce[v].mean("time").values.ravel(), er[v].mean("time").values.ravel())
        rows.append(
            f"| {v} | {unit} | {float(x.mean()):+.2f} | {float(np.sqrt((x**2).mean())):.2f} "
            f"| {float(abs(x).max()):.2f} | {corr[0, 1]:.3f} |"
        )
    by_hour = d.t2m.groupby("time.hour").mean(...)
    hours = " · ".join(
        f"{h:02d} UTC {float(b):+.2f} K"
        for h, b in zip(by_hour.hour.values, by_hour.values, strict=True)
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8), constrained_layout=True)
    lo, hi = float(er.t2m.mean("time").min()), float(er.t2m.mean("time").max())
    for ax, (title, da) in zip(
        axes[:2], (("ERA5", er.t2m), ("CERRA → 0,25°", ce.t2m)), strict=True
    ):
        da.mean("time").plot(ax=ax, vmin=lo, vmax=hi, cmap="RdYlBu_r", cbar_kwargs={"label": "K"})
        ax.set_title(f"2t media {c['month']} — {title}")
    lim = float(abs(d.t2m.mean("time")).quantile(0.99))
    d.t2m.mean("time").plot(
        ax=axes[2], vmin=-lim, vmax=lim, cmap="RdBu_r", cbar_kwargs={"label": "K"}
    )
    axes[2].set_title("CERRA − ERA5 (media temporal)")
    png = Path(cfg["qc"]["reports"]) / "cerra_vs_era5_2t.png"
    fig.savefig(png, dpi=110)

    md = Path(cfg["qc"]["reports"]) / "cerra_vs_era5.md"
    md.write_text(
        f"# CERRA vs ERA5 — {c['month']}, dominio {cfg['name']}\n\n"
        f"Generado por `scripts/cerra.py compare`. CERRA regrideado con `cdo {REMAP}` a la "
        f"rejilla ERA5 0,25° del proyecto; {ce.sizes['time']} instantes (00/06/12/18 UTC).\n\n"
        "## Rejilla CERRA original (`cdo griddes`)\n\n```\n" + "\n".join(grid_lines) + "\n```\n\n"
        "## CERRA − ERA5\n\n"
        "| variable | unidades | bias medio | RMSE | máx. abs | corr. espacial (media temporal) |\n"
        "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        f"Bias de 2t por hora: {hours}\n\n![2t](cerra_vs_era5_2t.png)\n"
    )
    return md


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["download", "regrid", "compare", "all"])
    p.add_argument("--config", default="configs/iberia.yaml")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(args.config)
    for step in (download, regrid, compare):
        if args.step in (step.__name__, "all"):
            print(step(cfg))


if __name__ == "__main__":
    main()
