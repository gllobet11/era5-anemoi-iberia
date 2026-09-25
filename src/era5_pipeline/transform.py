"""GRIB ERA5 (raw mensual) -> Zarr normalizado a 6 h.

Convención de `tp` (D-010): ERA5 horario en `valid_time` T = acumulación en (T-1h, T].
El valor 6 h etiquetado en T es la suma de las horas T-5h..T = acumulación en (T-6h, T],
igual que ECMWF/anemoi. Ventanas incompletas (p. ej. el primer 00 UTC del periodo) -> NaN.
"""

import logging
import shutil
from pathlib import Path

import xarray as xr

log = logging.getLogger(__name__)
CFGRIB = {"indexpath": ""}  # sin .idx: evita índices obsoletos si un GRIB se re-descarga
DROP = ["number", "step", "surface", "valid_time", "expver", "meanSea"]
KEEP = {"GRIB_paramId", "GRIB_shortName", "GRIB_cfVarName", "GRIB_stepType"}
# Metadatos CF por variable (nombre cfgrib -> standard_name, units). Unidades nativas ERA5 (D-010).
CF = {
    "t2m": ("air_temperature", "K"),
    "u10": ("eastward_wind", "m s-1"),
    "v10": ("northward_wind", "m s-1"),
    "msl": ("air_pressure_at_mean_sea_level", "Pa"),
    "sp": ("surface_air_pressure", "Pa"),
    "tp": ("lwe_thickness_of_precipitation_amount", "m"),
    "t": ("air_temperature", "K"),
    "z": ("geopotential", "m2 s-2"),
}


def normalize(ds: xr.Dataset, area: list[float]) -> xr.Dataset:
    """Coordenadas comunes para GRIB (cfgrib) y NetCDF (CDS nuevo): time, level, lat ↑, lon ±180."""
    if "valid_time" in ds.dims:  # NetCDF del CDS nuevo
        ds = ds.drop_vars("time", errors="ignore").rename(valid_time="time")
    if "isobaricInhPa" in ds.dims:
        ds = ds.rename(isobaricInhPa="level")
    if "pressure_level" in ds.dims:
        ds = ds.rename(pressure_level="level")
    ds = ds.drop_vars(DROP, errors="ignore")
    lon = ((ds.longitude + 180) % 360 - 180).assign_attrs(ds.longitude.attrs)
    ds = ds.assign_coords(longitude=lon)
    ds = ds.sortby(["latitude", "longitude"] + (["level"] if "level" in ds.dims else []))
    n, w, s, e = area
    ds = ds.sel(latitude=slice(s, n), longitude=slice(w, e))
    # los GRIB_* de rejilla (Nx, numberOfPoints, lon/lat first...) quedan obsoletos tras recortar
    for v in ds.data_vars.values():
        v.attrs = {k: a for k, a in v.attrs.items() if not k.startswith("GRIB_") or k in KEEP}
    return ds


def stack_accum(da: xr.DataArray) -> xr.DataArray:
    """(time, step) de cfgrib -> serie horaria en valid_time."""
    s = da.stack(z=("time", "step"))
    vt = s.valid_time.values
    s = s.drop_vars(["z", "time", "step", "valid_time"]).assign_coords(z=vt).rename(z="time")
    return s.dropna("time", how="all").sortby("time").transpose("time", ...)


def tp_to_6h(tp: xr.DataArray) -> xr.DataArray:
    out = tp.resample(time="6h", closed="right", label="right").sum(min_count=6)
    return out.assign_attrs(tp.attrs, long_name="Total precipitation, 6 h accumulation (T-6h, T]")


def open_single(path: Path) -> xr.Dataset:
    inst = xr.open_dataset(
        path, engine="cfgrib", backend_kwargs=CFGRIB | {"filter_by_keys": {"stepType": "instant"}}
    )
    acc = xr.open_dataset(
        path, engine="cfgrib", backend_kwargs=CFGRIB | {"filter_by_keys": {"stepType": "accum"}}
    )
    return inst.drop_vars(DROP, errors="ignore").assign(tp=stack_accum(acc.tp))


def open_pressure(path: Path) -> xr.Dataset:
    return xr.open_dataset(
        path,
        engine="cfgrib",
        backend_kwargs=CFGRIB | {"filter_by_keys": {"typeOfLevel": "isobaricInhPa"}},
    )


def build(single_files, pressure_files, cfg: dict) -> xr.Dataset:
    area = cfg["area"]
    # concat antes de agregar tp: la ventana del día 1 a 00 UTC usa horas del mes anterior
    single = normalize(xr.concat([open_single(f) for f in single_files], "time"), area)
    pres = normalize(xr.concat([open_pressure(f) for f in pressure_files], "time"), area)

    tp6 = tp_to_6h(single.tp)
    inst = single.drop_vars("tp")
    inst = inst.sel(time=inst.time.dt.hour % 6 == 0)
    ds = xr.merge([inst, tp6.to_dataset(name="tp"), pres], join="inner", combine_attrs="override")
    ds.attrs = {
        "title": f"ERA5 {cfg['name']} 6-hourly",
        "source": "ERA5 reanalysis (Copernicus C3S / ECMWF), CDS",
        "Conventions": "CF-1.7",
    }
    for name, (std, units) in CF.items():
        ds[name].attrs.update(standard_name=std, units=units)
    chunks = {k: v for k, v in cfg["chunks"].items() if k in ds.dims} | {"level": -1}
    return ds.chunk(chunks)


def write_zarr(ds: xr.Dataset, path: Path) -> None:
    """Reescritura completa vía directorio temporal + rename (idempotente, D-011)."""
    for v in ds.variables.values():
        v.encoding.pop("chunks", None)  # restos de cfgrib que chocan con el chunking nuevo
    tmp = path.with_name(path.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    ds.to_zarr(tmp, mode="w", consolidated=True)
    shutil.rmtree(path, ignore_errors=True)
    tmp.rename(path)


def transform(cfg: dict) -> Path:
    raw = Path(cfg["paths"]["raw"])
    single = sorted(raw.glob("single_*.grib"))
    pres = sorted(raw.glob("pressure_*.grib"))
    if not single or not pres:
        raise FileNotFoundError(f"faltan GRIB single/pressure en {raw}")
    out = Path(cfg["paths"]["zarr"])
    out.parent.mkdir(parents=True, exist_ok=True)
    ds = build(single, pres, cfg)
    log.info("escribiendo %s: %s", out, dict(ds.sizes))
    write_zarr(ds, out)
    return out
