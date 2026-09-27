"""Descarga ERA5 del CDS: una petición por (mes, tipo), idempotente vía manifest + sha256."""

import calendar
import fcntl
import hashlib
import json
import logging
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)
KINDS = {"single": "single_levels", "pressure": "pressure_levels"}
EXT = {"grib": "grib", "netcdf": "nc"}


def months(cfg: dict) -> list[tuple[int, int]]:
    start, end = (datetime.fromisoformat(cfg["period"][k]) for k in ("start", "end"))
    y, m, out = start.year, start.month, []
    while (y, m) <= (end.year, end.month):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def build_request(cfg: dict, kind: str, year: int, month: int, fmt: str = "grib") -> dict:
    sec = cfg[KINDS[kind]]
    hours = [f"{h:02d}:00" for h in range(24)] if sec["hours"] == "all" else sec["hours"]
    req = {
        "product_type": ["reanalysis"],
        "variable": list(sec["variables"].values()),
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": [f"{d:02d}" for d in range(1, calendar.monthrange(year, month)[1] + 1)],
        "time": hours,
        "area": cfg["area"],
        "grid": cfg["grid"],
        "data_format": fmt,
        "download_format": "unarchived",
    }
    if kind == "pressure":
        req["pressure_level"] = [str(lev) for lev in sec["levels"]]
    return req


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Manifest:
    """manifest.json: {nombre_lógico: {path, size, sha256, downloaded_at}}. Escritura atómica.

    Varios procesos (tareas de un job array de Slurm) pueden escribir a la vez: `record`
    relee el fichero bajo flock y fusiona, para no perder entradas de otros procesos.
    """

    def __init__(self, path: Path):
        self.path = path
        self.entries = json.loads(path.read_text()) if path.exists() else {}
        self._lock = threading.Lock()

    def is_valid(self, name: str) -> bool:
        e = self.entries.get(name)
        if not e:
            return False
        p = Path(e["path"])
        return p.exists() and p.stat().st_size == e["size"] and sha256(p) == e["sha256"]

    def record(self, name: str, path: Path) -> None:
        entry = {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": sha256(path),
            "downloaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        lock = self.path.with_suffix(".json.lock")
        with self._lock, open(lock, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            if self.path.exists():
                self.entries.update(json.loads(self.path.read_text()))
            self.entries[name] = entry
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.entries, indent=2, sort_keys=True))
            tmp.replace(self.path)


def fetch(client, cfg: dict, manifest: Manifest, kind: str, year: int, month: int, fmt: str):
    """Descarga un (tipo, mes, formato). Devuelve 'skipped' o 'downloaded'."""
    raw = Path(cfg["paths"]["raw"])
    name = f"{kind}_{year}-{month:02d}.{EXT[fmt]}"
    if manifest.is_valid(name):
        return "skipped"

    tmp = raw / (name + ".part")
    req = build_request(cfg, kind, year, month, fmt)
    ing = cfg["ingest"]
    for attempt in range(ing["retries"] + 1):
        try:
            client.retrieve(cfg[KINDS[kind]]["dataset"], req, str(tmp))
            break
        except Exception as e:
            tmp.unlink(missing_ok=True)
            if attempt == ing["retries"]:
                raise
            wait = ing["backoff_s"] * 2**attempt
            log.warning("%s: intento %d falló (%s); reintento en %ss", name, attempt + 1, e, wait)
            time.sleep(wait)

    # ponytail: el CDS puede devolver zip en NetCDF con stepTypes mixtos pese a "unarchived";
    # se guarda tal cual y F2 lo abre.
    final = raw / (name + ".zip" if zipfile.is_zipfile(tmp) else name)
    tmp.replace(final)
    manifest.record(name, final)
    log.info("%s descargado (%d bytes)", final.name, final.stat().st_size)
    return "downloaded"


def ingest(cfg: dict, client=None, month: str | None = None) -> dict[str, int]:
    """Descarga todo el periodo, o solo `month` ("YYYY-MM"; una tarea del job array, F6)."""
    if client is None:
        import cdsapi

        client = cdsapi.Client()
    raw = Path(cfg["paths"]["raw"])
    raw.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(raw / "manifest.json")

    ny, nm = map(int, cfg["ingest"]["netcdf_month"].split("-"))
    jobs = [(k, y, m, "grib") for y, m in months(cfg) for k in KINDS]
    jobs += [(k, ny, nm, "netcdf") for k in KINDS]
    if month:
        y, m = map(int, month.split("-"))
        jobs = [j for j in jobs if j[1:3] == (y, m)]
        if not jobs:
            raise ValueError(f"{month} fuera del periodo de la config")

    with ThreadPoolExecutor(cfg["ingest"]["workers"]) as ex:
        results = list(ex.map(lambda j: fetch(client, cfg, manifest, *j), jobs))
    summary = {r: results.count(r) for r in ("downloaded", "skipped")}
    log.info("ingest: %s", summary)
    return summary
