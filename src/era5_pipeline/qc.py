"""QC del Zarr normalizado -> reports/qc_<fecha>.{json,md}.

Todos los checks son críticos: si alguno falla, `passed` es False y la CLI sale con código 1.
Umbrales y rangos en `cfg["qc"]`; unidades esperadas = las que escribe transform (CF).
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import xarray as xr

from era5_pipeline.transform import CF

MAX_LISTED = 20  # timesteps listados en el informe; el resto solo se cuenta


def expected_times(cfg: dict) -> pd.DatetimeIndex:
    p = cfg["period"]
    end = pd.Timestamp(p["end"]) + pd.Timedelta("1D")  # period.end es un día completo
    return pd.date_range(p["start"], end, freq=cfg["frequency"], inclusive="left")


def check_time(ds: xr.Dataset, cfg: dict) -> dict:
    t = pd.DatetimeIndex(ds.time.values)
    exp = expected_times(cfg)
    missing, extra, dup = exp.difference(t), t.difference(exp), t[t.duplicated()]
    fmt = lambda idx: [str(x) for x in idx[:MAX_LISTED]]  # noqa: E731
    return {
        "passed": len(missing) == len(extra) == len(dup) == 0,
        "expected": len(exp),
        "present": len(t),
        "missing": fmt(missing),
        "n_missing": len(missing),
        "extra": fmt(extra),
        "duplicated": fmt(dup),
    }


def check_monotonic(ds: xr.Dataset, cfg: dict) -> dict:
    idx = {c: ds.indexes[c] for c in ("time", "level", "latitude", "longitude") if c in ds.indexes}
    bad = [c for c, i in idx.items() if not (i.is_monotonic_increasing and i.is_unique)]
    return {"passed": not bad, "not_strictly_increasing": bad}


def check_units(ds: xr.Dataset, cfg: dict) -> dict:
    missing = [v for v in CF if v not in ds]
    wrong = {
        v: {"expected": u, "found": ds[v].attrs.get("units")}
        for v, (_, u) in CF.items()
        if v in ds and ds[v].attrs.get("units") != u
    }
    return {"passed": not missing and not wrong, "missing_vars": missing, "wrong_units": wrong}


def check_nan(ds: xr.Dataset, cfg: dict) -> dict:
    q = cfg["qc"]
    pct = {}
    for v in ds.data_vars:
        da = ds[v].isel(time=slice(q.get("leading_nan_steps", {}).get(v, 0), None))
        pct[v] = round(100 * float(da.isnull().mean()), 4)
    bad = {v: p for v, p in pct.items() if p > q["max_nan_pct"]}
    return {"passed": not bad, "nan_pct": pct, "over_threshold": bad}


def check_ranges(ds: xr.Dataset, cfg: dict) -> dict:
    out = {}
    for v, (lo, hi) in cfg["qc"]["ranges"].items():
        if v in ds:  # variables ausentes ya fallan en check_units
            da = ds[v]
            n = int(((da < lo) | (da > hi)).sum())
            out[v] = {"range": [lo, hi], "min": float(da.min()), "max": float(da.max()), "n_out": n}
    return {"passed": all(r["n_out"] == 0 for r in out.values()), "vars": out}


CHECKS = {
    "time": check_time,
    "monotonic_coords": check_monotonic,
    "units": check_units,
    "nan": check_nan,
    "ranges": check_ranges,
}


def stats(ds: xr.Dataset) -> dict:
    """Media, std, min, max por variable; las de presión, por nivel (t_500, z_850...)."""
    out = {}
    for v in sorted(ds.data_vars):
        levels = ds.level.values if "level" in ds[v].dims else [None]
        for lev in levels:
            da = ds[v] if lev is None else ds[v].sel(level=lev)
            key = v if lev is None else f"{v}_{int(lev)}"
            out[key] = {
                "units": ds[v].attrs.get("units"),
                **{f: float(getattr(da, f)()) for f in ("mean", "std", "min", "max")},
            }
    return out


def run_qc(ds: xr.Dataset, cfg: dict) -> dict:
    checks = {name: fn(ds, cfg) for name, fn in CHECKS.items()}
    return {
        "passed": all(c["passed"] for c in checks.values()),
        "sizes": dict(ds.sizes),
        "checks": checks,
        "stats": stats(ds),
    }


def to_markdown(report: dict) -> str:
    ok = lambda b: "✅" if b else "❌"  # noqa: E731
    lines = [
        f"# QC — {report['zarr']}",
        "",
        f"Fecha: {report['date']} · Resultado: {ok(report['passed'])} · Dims: {report['sizes']}",
        "",
        "## Checks",
        "",
        "| Check | OK | Detalle |",
        "|---|---|---|",
    ]
    for name, c in report["checks"].items():
        detail = json.dumps({k: v for k, v in c.items() if k != "passed"}, ensure_ascii=False)
        lines.append(f"| {name} | {ok(c['passed'])} | `{detail}` |")
    lines += ["", "## Estadísticos", "", "| Variable | Unidades | Media | Std | Min | Max |"]
    lines.append("|---|---|---|---|---|---|")
    for k, s in report["stats"].items():
        nums = " | ".join(f"{s[f]:.6g}" for f in ("mean", "std", "min", "max"))
        lines.append(f"| {k} | {s['units']} | {nums} |")
    return "\n".join(lines) + "\n"


def qc(zarr: str | Path, cfg: dict) -> dict:
    # ponytail: carga el Zarr entero (~440 MB); si crece dominio/periodo, reducir por chunks
    ds = xr.open_zarr(zarr).load()
    report = {"zarr": str(zarr), "date": date.today().isoformat(), **run_qc(ds, cfg)}
    out = Path(cfg["qc"]["reports"])
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"qc_{report['date']}"
    stem.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    stem.with_suffix(".md").write_text(to_markdown(report))
    return report
