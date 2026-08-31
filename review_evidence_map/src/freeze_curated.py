from __future__ import annotations

from pathlib import Path

from .common import FROZEN_DIR, load_yaml, template_fields, write_csv


CURATED_TABLES = (
    "papers",
    "studies",
    "scenarios",
    "case_assets",
    "safeguards",
    "reviews",
    "quantitative_values",
    "resources",
    "resource_links",
    "claim_evidence_ledger",
)


def freeze_curated_evidence(source: Path) -> dict[str, int]:
    payload = load_yaml(source)
    tables = payload.get("tables", {})
    counts: dict[str, int] = {}
    for name in CURATED_TABLES:
        rows = tables.get(name, []) or []
        fields = template_fields(name)
        unknown = sorted({key for row in rows for key in row} - set(fields))
        if unknown:
            raise ValueError(f"Unknown {name} fields in curated source: {unknown}")
        write_csv(FROZEN_DIR / f"{name}.csv", fields, rows)
        counts[name] = len(rows)
    return counts
