from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common import REVIEW_ROOT, ensure_directories
from src.discover import run_discovery
from src.inventory import build_source_inventory
from src.freeze_curated import freeze_curated_evidence
from src.normalise import extract_repository_metadata, run_normalise


STAGES = ("inventory", "discover", "validate", "analyse", "render", "all")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the frozen Review evidence map and descriptive outputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="config/search_plan.yml", help="Search-plan YAML relative to this directory")
    parser.add_argument("--stage", choices=STAGES, default="all", help="Pipeline stage to execute")
    parser.add_argument("--offline", action="store_true", help="Forbid network discovery and rebuild from frozen inputs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = (REVIEW_ROOT / args.config).resolve()
    if not config_path.exists():
        raise SystemExit(f"Config does not exist: {config_path}")
    ensure_directories()
    if args.stage in {"inventory", "all"}:
        rows = build_source_inventory()
        print(f"inventory: {len(rows)} source Word/PDF files")
    if args.stage in {"discover", "all"}:
        if args.offline:
            print("discover: skipped in offline mode; frozen discovery inputs retained")
        else:
            logs, candidates = run_discovery(config_path)
            print(f"discover: {len(logs)} retrieval-log rows; {len(candidates)} candidate records")
            screening, duplicates = run_normalise()
            extractions = extract_repository_metadata()
            curated = freeze_curated_evidence(REVIEW_ROOT / "data" / "interim" / "curated_coding.yml")
            print(
                f"screen: {len(screening)} dispositions; {len(duplicates)} duplicate records; "
                f"{len(extractions)} repository extraction diagnostics"
            )
            print("curated evidence: " + ", ".join(f"{name}={count}" for name, count in curated.items()))
    if args.stage not in {"inventory", "discover", "all"}:
        raise SystemExit(f"Stage {args.stage!r} will be enabled by the implementation commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
