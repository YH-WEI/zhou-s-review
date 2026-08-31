from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

import yaml


REVIEW_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = REVIEW_ROOT.parent
TEMPLATES_DIR = REVIEW_ROOT / "templates"
DATA_DIR = REVIEW_ROOT / "data"
FROZEN_DIR = DATA_DIR / "frozen"
RESULTS_DIR = REVIEW_ROOT / "results"


def ensure_directories() -> None:
    for path in (
        DATA_DIR / "raw_metadata",
        DATA_DIR / "interim",
        DATA_DIR / "manual_imports",
        FROZEN_DIR,
        RESULTS_DIR / "tables",
        RESULTS_DIR / "figures",
        RESULTS_DIR / "audit",
    ):
        path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def template_fields(name: str) -> list[str]:
    path = TEMPLATES_DIR / f"{name}_template.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fields})


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return value


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip(" .")


def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def pipe_join(values: Iterable[str]) -> str:
    return "|".join(sorted({value for value in values if value}))
