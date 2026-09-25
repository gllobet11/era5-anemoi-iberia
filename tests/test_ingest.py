import json
from pathlib import Path

import pytest

from era5_pipeline.config import load_config
from era5_pipeline.ingest import build_request, ingest, months

ROOT = Path(__file__).parents[1]


class FakeClient:
    """Sustituye a cdsapi.Client: escribe bytes en el target. Nunca toca el CDS."""

    def __init__(self, fail_first=0):
        self.calls = []
        self.fail_first = fail_first

    def retrieve(self, dataset, request, target):
        self.calls.append((dataset, request))
        if self.fail_first:
            self.fail_first -= 1
            Path(target).write_bytes(b"parcial")
            raise ConnectionError("CDS caído")
        Path(target).write_bytes(f"{dataset}{request['year']}{request['month']}".encode())


@pytest.fixture
def cfg(tmp_path):
    c = load_config(ROOT / "configs/iberia.yaml")
    c["period"] = {"start": "2020-01-01", "end": "2020-02-29"}
    c["paths"]["raw"] = str(tmp_path / "raw")
    c["ingest"].update(backoff_s=0, workers=2)
    return c


def test_months_crosses_year():
    cfg = {"period": {"start": "2020-11-01", "end": "2021-02-28"}}
    assert months(cfg) == [(2020, 11), (2020, 12), (2021, 1), (2021, 2)]


def test_build_request():
    cfg = load_config(ROOT / "configs/iberia.yaml")
    s = build_request(cfg, "single", 2020, 2)
    assert len(s["day"]) == 29 and len(s["time"]) == 24  # bisiesto; horario por tp (D-008)
    assert "pressure_level" not in s and s["download_format"] == "unarchived"
    p = build_request(cfg, "pressure", 2021, 2, "netcdf")
    assert len(p["day"]) == 28 and p["pressure_level"] == ["500", "850"]
    assert p["time"] == ["00:00", "06:00", "12:00", "18:00"] and p["data_format"] == "netcdf"


def test_ingest_idempotent(cfg):
    client = FakeClient()
    assert ingest(cfg, client) == {"downloaded": 6, "skipped": 0}  # 2 meses×2 tipos + 2 NetCDF
    manifest = json.loads((Path(cfg["paths"]["raw"]) / "manifest.json").read_text())
    assert set(manifest) == {
        "single_2020-01.grib", "pressure_2020-01.grib", "single_2020-02.grib",
        "pressure_2020-02.grib", "single_2020-01.nc", "pressure_2020-01.nc",
    }  # fmt: skip
    assert all(len(e["sha256"]) == 64 and e["size"] > 0 for e in manifest.values())

    client2 = FakeClient()
    assert ingest(cfg, client2) == {"downloaded": 0, "skipped": 6}
    assert client2.calls == []


def test_corrupted_file_is_redownloaded(cfg):
    ingest(cfg, FakeClient())
    (Path(cfg["paths"]["raw"]) / "single_2020-02.grib").write_bytes(b"corrupto")
    client = FakeClient()
    assert ingest(cfg, client) == {"downloaded": 1, "skipped": 5}


def test_retry_then_success_leaves_no_part(cfg):
    cfg["period"]["end"] = "2020-01-31"
    cfg["ingest"]["workers"] = 1
    client = FakeClient(fail_first=2)
    assert ingest(cfg, client)["downloaded"] == 4
    assert not list(Path(cfg["paths"]["raw"]).glob("*.part"))


def test_retries_exhausted_raises(cfg):
    cfg["ingest"]["workers"] = 1
    with pytest.raises(ConnectionError):
        ingest(cfg, FakeClient(fail_first=99))
    assert not list(Path(cfg["paths"]["raw"]).glob("*.part"))
