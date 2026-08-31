from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common import REVIEW_ROOT, ensure_directories
from src.inventory import build_source_inventory


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
    if args.stage not in {"inventory", "all"}:
        raise SystemExit(f"Stage {args.stage!r} will be enabled by the implementation commit")
    if args.stage == "all" and args.offline:
        print("offline scaffold run: inventory complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
