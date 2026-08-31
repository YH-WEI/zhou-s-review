from __future__ import annotations

from pathlib import Path

from .common import REPO_ROOT, REVIEW_ROOT, sha256_file, write_csv


INVENTORY_FIELDS = [
    "source_file_id",
    "repository_path",
    "extension",
    "byte_size",
    "sha256",
    "role",
    "extraction_status",
    "notes",
]


def _role(path: Path) -> tuple[str, str]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    name = path.name
    if rel == "周跃宽的idea.docx":
        return "idea_seed", "Formal idea source; statements still require original-source verification."
    if name in {"AI数据中心作为电网互动型资产_逐段翻译与深度解读.docx", "Data_centers_6G_中文逐句翻译与通俗解读.docx"}:
        return "reading_aid", "Secondary reading aid; never cited instead of the original source."
    if rel.startswith("案例论文/") and path.suffix.lower() == ".pdf":
        return "seed_primary_candidate", "Repository seed; subject to the same screening and coding rules."
    if rel.startswith("周跃宽本人论文/"):
        return "candidate_study", "Author-corpus candidate; repository presence does not imply inclusion."
    if rel.startswith("nature energy综述例子集合/"):
        return "review_style_exemplar", "Narrative/style exemplar; excluded from topical evidence unless independently eligible."
    return "repository_source", "Pre-existing repository Word/PDF source."


def source_paths() -> list[Path]:
    paths: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".docx"}:
            continue
        if ".git" in path.parts or REVIEW_ROOT in path.parents:
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(REPO_ROOT).as_posix().casefold())


def build_source_inventory(output_path: Path | None = None) -> list[dict[str, object]]:
    output_path = output_path or REVIEW_ROOT / "data" / "source_inventory.csv"
    rows: list[dict[str, object]] = []
    for index, path in enumerate(source_paths(), start=1):
        role, notes = _role(path)
        rows.append(
            {
                "source_file_id": f"SRC{index:04d}",
                "repository_path": path.relative_to(REPO_ROOT).as_posix(),
                "extension": path.suffix.lower(),
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
                "role": role,
                "extraction_status": "available_local",
                "notes": notes,
            }
        )
    write_csv(output_path, INVENTORY_FIELDS, rows)
    return rows


def verify_source_inventory(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for row in rows:
        path = REPO_ROOT / row["repository_path"]
        if not path.exists():
            failures.append({"repository_path": row["repository_path"], "error": "missing"})
            continue
        actual = sha256_file(path)
        if actual != row["sha256"]:
            failures.append(
                {
                    "repository_path": row["repository_path"],
                    "error": "sha256_mismatch",
                    "expected": row["sha256"],
                    "actual": actual,
                }
            )
    return failures
