from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .common import (
    FROZEN_DIR,
    REPO_ROOT,
    REVIEW_ROOT,
    normalize_doi,
    normalize_title,
    pipe_join,
    read_csv,
    template_fields,
    write_csv,
)


DEDUP_FIELDS = [
    "deduplication_id",
    "duplicate_record_id",
    "canonical_record_id",
    "match_method",
    "match_key",
    "action",
    "manual_verification_status",
    "notes",
]

MANUAL_REVIEW_FIELDS = [
    "search_record_id",
    "title",
    "publication_year",
    "doi_normalized",
    "stable_url",
    "oa_url",
    "query_ids",
    "manual_review_reason",
]

REPOSITORY_EXTRACTION_FIELDS = [
    "source_file_id",
    "repository_path",
    "extraction_method",
    "extraction_status",
    "characters_extracted",
    "detected_dois",
    "notes",
]


REPOSITORY_METADATA = {
    "案例论文/s41560-025-01927-1(1).pdf": {
        "title": "AI data centres as grid-interactive assets",
        "year": "2026",
        "doi": "10.1038/s41560-025-01927-1",
        "paper_id": "P0001",
        "decision": "include",
    },
    "周跃宽本人论文/2024 An electricity-driven mobility circular economy with lifecycle carbon footprints for climate-adaptive carbon neutrality transformation.pdf": {
        "title": "An electricity-driven mobility circular economy with lifecycle carbon footprints for climate-adaptive carbon neutrality transformation",
        "year": "2024",
        "doi": "10.1038/s41467-024-49868-9",
        "paper_id": "P0002",
        "decision": "include",
    },
    "周跃宽本人论文/2025 An Integrative lifecycle design approach based on carbon intensity for renewable-battery-consumer energy systems.pdf": {
        "title": "An Integrative lifecycle design approach based on carbon intensity for renewable-battery-consumer energy systems",
        "year": "2025",
        "doi": "10.1038/s44172-024-00339-5",
        "decision": "X02_internal_efficiency_only",
    },
    "周跃宽本人论文/2025 City information models for optimal EV charging and energy-resilient renaissance.pdf": {
        "title": "City information models for optimal EV charging and energy-resilient renaissance",
        "year": "2025",
        "doi": "10.1016/j.ynexs.2025.100056",
        "decision": "X03_no_grid_signal_or_service",
    },
    "周跃宽本人论文/2025 Lifecycle carbon intensity with embodied emissions of battery and hydrogen-driven integrative low-carbon systems.pdf": {
        "title": "Lifecycle carbon intensity with embodied emissions of battery and hydrogen-driven integrative low-carbon systems",
        "year": "2025",
        "doi": "10.1038/s44172-025-00411-8",
        "decision": "X03_no_grid_signal_or_service",
    },
    "周跃宽本人论文/2026 Integrating renewable energy with electricvehicle charging infrastructure in China A strategyfor enhanced accessibility and carbon abatement.pdf": {
        "title": "Integrating renewable energy with electric vehicle charging infrastructure in China: A strategy for enhanced accessibility and carbon abatement",
        "year": "2026",
        "doi": "10.1016/j.ynexs.2025.100113",
        "decision": "X03_no_grid_signal_or_service",
    },
    "周跃宽本人论文/March 18, 2025 Energy-resilient climate adaptation using a tailored life-cycle integrative design approach for national carbon abatement.pdf": {
        "title": "Energy-resilient climate adaptation using a tailored life-cycle integrative design approach for national carbon abatement",
        "year": "2024",
        "doi": "10.1016/j.xcrp.2024.102306",
        "decision": "X02_internal_efficiency_only",
    },
}


ASSET_PATTERN = re.compile(
    r"data cent(?:er|re)|cloud computing|high.performance computing|\bhpc\b|"
    r"base station|radio access network|telecom tower|cellular network|\b5g\b|\b6g\b|imt.2030|"
    r"electric vehicle|vehicle.to.grid|vehicle.to.building|vehicle.to.home|\bv2g\b|\bv2b\b|\bv2h\b|ev charging|"
    r"smart building|active building|grid.interactive building|building energy|\bhvac\b",
    re.IGNORECASE,
)

SERVICE_PATTERN = re.compile(
    r"grid|demand response|peak|load shift|flexib|frequency|reserve|renewable|curtail|voltage|congestion|"
    r"microgrid|virtual power plant|\bvpp\b|resilien|emergency|energy management|energy sharing|carbon.aware",
    re.IGNORECASE,
)

DIGITAL_ONLY_PATTERN = re.compile(
    r"traffic prediction|wireless communication|spectrum|channel estimation|data transmission|semantic communication|"
    r"edge offloading|network slicing|computer vision",
    re.IGNORECASE,
)


def _enrich_repository_candidate(row: dict[str, str]) -> dict[str, str]:
    enriched = dict(row)
    meta = REPOSITORY_METADATA.get(row.get("repository_path", ""))
    if meta:
        enriched["title"] = str(meta["title"])
        enriched["publication_year"] = str(meta["year"])
        enriched["doi_raw"] = str(meta["doi"])
        enriched["doi_normalized"] = str(meta["doi"])
        enriched["stable_url"] = f"https://doi.org/{meta['doi']}"
    return enriched


def _canonical_order(row: dict[str, str]) -> tuple[int, str]:
    priority = {"repository": 0, "openalex": 1, "crossref": 2}.get(row["source_database"], 3)
    return priority, row["search_record_id"]


def _deduplicate(rows: list[dict[str, str]]) -> tuple[dict[str, str], list[dict[str, str]]]:
    canonical_for: dict[str, str] = {}
    canonical_by_doi: dict[str, str] = {}
    canonical_by_title_year: dict[str, str] = {}
    dedup_rows: list[dict[str, str]] = []
    ordered = sorted(rows, key=_canonical_order)
    for row in ordered:
        record_id = row["search_record_id"]
        doi = normalize_doi(row.get("doi_normalized") or row.get("doi_raw"))
        title_year = f"{normalize_title(row.get('title'))}|{row.get('publication_year', '')}"
        canonical = ""
        method = ""
        key = ""
        if doi and doi in canonical_by_doi:
            canonical = canonical_by_doi[doi]
            method = "normalized_doi"
            key = doi
        elif not doi and title_year.strip("|") and title_year in canonical_by_title_year:
            canonical = canonical_by_title_year[title_year]
            method = "exact_normalized_title_plus_year"
            key = title_year
        if canonical:
            canonical_for[record_id] = canonical
            dedup_rows.append(
                {
                    "deduplication_id": f"D{len(dedup_rows) + 1:06d}",
                    "duplicate_record_id": record_id,
                    "canonical_record_id": canonical,
                    "match_method": method,
                    "match_key": key,
                    "action": "retain_as_linked_duplicate_exclude_from_screening_count",
                    "manual_verification_status": "rule_verified",
                    "notes": "No fuzzy-only auto-merge was performed.",
                }
            )
        else:
            canonical_for[record_id] = record_id
            if doi:
                canonical_by_doi[doi] = record_id
            if title_year.strip("|"):
                canonical_by_title_year.setdefault(title_year, record_id)
    return canonical_for, dedup_rows


def _local_disposition(row: dict[str, str]) -> tuple[str, str, str]:
    path = row["repository_path"]
    meta = REPOSITORY_METADATA.get(path)
    if meta:
        decision = str(meta["decision"])
        if decision == "include":
            return "include", "", "Full text reviewed against the fixed scope and codebook."
        notes = {
            "X02_internal_efficiency_only": "System design/internal performance without a qualifying external grid-service response.",
            "X03_no_grid_signal_or_service": "Planning or lifecycle context without an eligible active grid-service decision under this protocol.",
        }
        return "exclude", decision, notes[decision]
    if path.startswith("nature energy综述例子集合/"):
        return "exclude", "X13_unrelated_review_or_style_exemplar", "Repository file is a narrative/style exemplar outside the topical evidence corpus."
    if path.endswith(".docx"):
        return "exclude", "X11_non_original_or_unverifiable_claim", "Idea/translation reading aid is not an original performance source."
    return "exclude", "X14_other", "Repository candidate did not match a documented inclusion route."


def run_normalise() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    raw_rows = read_csv(FROZEN_DIR / "candidate_records.csv")
    rows = [_enrich_repository_candidate(row) for row in raw_rows]
    canonical_for, dedup_rows = _deduplicate(rows)
    query_ids_by_canonical: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        query_ids_by_canonical[canonical_for[row["search_record_id"]]].add(row["query_id"])
    timestamp = max(
        (row["searched_at_utc"] for row in read_csv(FROZEN_DIR / "search_log.csv") if row["searched_at_utc"]),
        default="2026-08-31T00:00:00Z",
    )

    screening_rows: list[dict[str, str]] = []
    manual_rows: list[dict[str, str]] = []
    for row in rows:
        record_id = row["search_record_id"]
        canonical = canonical_for[record_id]
        is_duplicate = canonical != record_id
        doi = normalize_doi(row.get("doi_normalized") or row.get("doi_raw"))
        paper_id = ""
        title_abstract_decision = "exclude"
        fulltext_decision = "exclude"
        exclusion_code = ""
        exclusion_note = ""
        confidence = "high"
        access = "repository_fulltext_available" if row["source_database"] == "repository" else (
            "oa_location_identified_not_retrieved" if row.get("oa_url") else "fulltext_not_obtained"
        )

        if is_duplicate:
            exclusion_code = "X07_duplicate_version"
            exclusion_note = f"Duplicate search record linked to canonical {canonical}."
        elif row["source_database"] == "repository":
            decision, exclusion_code, exclusion_note = _local_disposition(row)
            title_abstract_decision = decision
            fulltext_decision = decision
            meta = REPOSITORY_METADATA.get(row["repository_path"], {})
            paper_id = str(meta.get("paper_id", "")) if decision == "include" else ""
        else:
            text = f"{row.get('title', '')} {row.get('abstract', '')}"
            if not ASSET_PATTERN.search(text):
                exclusion_code = "X01_not_focal_asset"
                exclusion_note = "No focal asset was identifiable in title/available abstract metadata."
            elif DIGITAL_ONLY_PATTERN.search(text) and not SERVICE_PATTERN.search(text):
                exclusion_code = "X04_digital_only_no_energy_decision"
                exclusion_note = "Digital/communications topic without an identifiable energy decision or grid service."
            elif not SERVICE_PATTERN.search(text):
                exclusion_code = "X03_no_grid_signal_or_service"
                exclusion_note = "No qualifying grid signal, service or operational objective was identifiable in metadata."
            else:
                title_abstract_decision = "include"
                exclusion_code = "X10_fulltext_unavailable_for_required_verification"
                exclusion_note = "Potentially eligible metadata record; full text was not verified in this bounded run."
                confidence = "low"
                manual_rows.append(
                    {
                        "search_record_id": record_id,
                        "title": row["title"],
                        "publication_year": row["publication_year"],
                        "doi_normalized": doi,
                        "stable_url": row["stable_url"],
                        "oa_url": row["oa_url"],
                        "query_ids": pipe_join(query_ids_by_canonical[canonical]),
                        "manual_review_reason": "Full-text eligibility, project duplication, multi-asset role and source locators require human verification.",
                    }
                )

        screening_rows.append(
            {
                "schema_version": "1.0",
                "codebook_version": "1.0",
                "search_record_id": record_id,
                "paper_id_candidate": paper_id,
                "source_database": row["source_database"],
                "source_record_id": row["source_record_id"],
                "query_ids": pipe_join(query_ids_by_canonical[canonical]),
                "title": row["title"],
                "publication_year": row["publication_year"],
                "doi_raw": row["doi_raw"],
                "doi_normalized": doi,
                "stable_url": row["stable_url"],
                "document_type": row["document_type"],
                "corpus_layer": "repository_seed" if row["source_database"] == "repository" else "discovery_metadata",
                "fulltext_access_status": access,
                "title_abstract_decision": title_abstract_decision,
                "fulltext_decision": fulltext_decision,
                "exclusion_code": exclusion_code,
                "exclusion_note": exclusion_note,
                "screen_confidence": confidence,
                "screened_by": "codex_fulltext_review" if row["source_database"] == "repository" else "codex_metadata_rules_v1",
                "screened_at_utc": timestamp,
            }
        )

    write_csv(FROZEN_DIR / "deduplication_log.csv", DEDUP_FIELDS, dedup_rows)
    write_csv(FROZEN_DIR / "screening_log.csv", template_fields("screening"), screening_rows)
    write_csv(FROZEN_DIR / "needs_manual_review.csv", MANUAL_REVIEW_FIELDS, manual_rows)
    return screening_rows, dedup_rows


def extract_repository_metadata() -> list[dict[str, str]]:
    inventory = read_csv(REVIEW_ROOT / "data" / "source_inventory.csv")
    rows: list[dict[str, str]] = []
    doi_pattern = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", re.IGNORECASE)
    for source in inventory:
        path = REPO_ROOT / source["repository_path"]
        text = ""
        method = ""
        status = "success"
        notes = "Only DOI strings and extraction diagnostics are retained; source text is not committed."
        try:
            if path.suffix.lower() == ".pdf":
                reader = PdfReader(path)
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
                method = "pypdf_page_text"
            else:
                document = Document(path)
                text = "\n".join(paragraph.text for paragraph in document.paragraphs)
                method = "python_docx_paragraph_text"
        except Exception as exc:  # extraction failures must be logged, never guessed
            status = "failed"
            notes = f"{type(exc).__name__}: {exc}"
        dois = pipe_join(normalize_doi(match.group(0)) for match in doi_pattern.finditer(text))
        rows.append(
            {
                "source_file_id": source["source_file_id"],
                "repository_path": source["repository_path"],
                "extraction_method": method,
                "extraction_status": status,
                "characters_extracted": str(len(text)),
                "detected_dois": dois,
                "notes": notes,
            }
        )
    write_csv(FROZEN_DIR / "repository_extraction_log.csv", REPOSITORY_EXTRACTION_FIELDS, rows)
    return rows
