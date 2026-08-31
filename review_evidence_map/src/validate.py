from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .common import (
    FROZEN_DIR,
    RESULTS_DIR,
    REVIEW_ROOT,
    load_yaml,
    read_csv,
    sha256_file,
    template_fields,
    write_json,
)
from .inventory import verify_source_inventory


@dataclass
class Check:
    check_id: str
    severity: str
    status: str
    message: str
    affected_records: str = ""


ID_FIELDS = {
    "papers": "paper_id",
    "studies": "study_id",
    "scenarios": "scenario_id",
    "case_assets": "scenario_asset_id",
    "quantitative_values": "metric_record_id",
    "safeguards": "safeguard_id",
    "reviews": "review_id",
    "resources": "resource_id",
    "resource_links": "resource_link_id",
    "claim_evidence_ledger": "claim_id",
}

TABLES = tuple(ID_FIELDS)


def _number(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def _add(checks: list[Check], check_id: str, ok: bool, message: str, records: list[str] | None = None, severity: str = "error") -> None:
    checks.append(
        Check(
            check_id=check_id,
            severity=severity,
            status="PASS" if ok else ("WARN" if severity == "warning" else "FAIL"),
            message=message,
            affected_records="|".join(records or []),
        )
    )


def validate_frozen_data() -> list[Check]:
    rules = load_yaml(REVIEW_ROOT / "config" / "schema_rules.yml")
    tables = {name: read_csv(FROZEN_DIR / f"{name}.csv") for name in TABLES}
    checks: list[Check] = []

    for name, rows in tables.items():
        expected = template_fields(name)
        path = FROZEN_DIR / f"{name}.csv"
        actual = list(rows[0]) if rows else path.read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        _add(checks, f"schema_{name}", actual == expected, f"{name}.csv header matches its template")

    for name, key in ID_FIELDS.items():
        values = [row[key] for row in tables[name]]
        duplicates = sorted(value for value, count in Counter(values).items() if value and count > 1)
        blanks = [str(index + 2) for index, value in enumerate(values) if not value]
        _add(checks, f"unique_{name}", not duplicates and not blanks, f"{name} IDs are unique and non-empty", duplicates + blanks)

    pending = []
    for name, rows in tables.items():
        for row in rows:
            if any(str(value).strip().lower() == "pending" for value in row.values()):
                pending.append(f"{name}:{row.get(ID_FIELDS[name], '')}")
    _add(checks, "no_pending", not pending, "Frozen evidence tables contain no pending status", pending)

    papers = {row["paper_id"]: row for row in tables["papers"]}
    studies = {row["study_id"]: row for row in tables["studies"]}
    scenarios = {row["scenario_id"]: row for row in tables["scenarios"]}
    resources = {row["resource_id"]: row for row in tables["resources"]}
    metrics = {row["metric_record_id"]: row for row in tables["quantitative_values"]}

    fk_failures = []
    for row in tables["papers"]:
        if row["study_id"] not in studies:
            fk_failures.append(f"paper:{row['paper_id']}->study:{row['study_id']}")
    for row in tables["studies"]:
        if row["primary_paper_id"] not in papers:
            fk_failures.append(f"study:{row['study_id']}->paper:{row['primary_paper_id']}")
    for name in ("scenarios", "safeguards", "quantitative_values"):
        for row in tables[name]:
            if row["paper_id"] not in papers:
                fk_failures.append(f"{name}:{row[ID_FIELDS[name]]}->paper:{row['paper_id']}")
            if row["study_id"] not in studies:
                fk_failures.append(f"{name}:{row[ID_FIELDS[name]]}->study:{row['study_id']}")
            if name != "scenarios" and row["scenario_id"] not in scenarios:
                fk_failures.append(f"{name}:{row[ID_FIELDS[name]]}->scenario:{row['scenario_id']}")
    for row in tables["case_assets"]:
        if row["scenario_id"] not in scenarios:
            fk_failures.append(f"case_assets:{row['scenario_asset_id']}->scenario:{row['scenario_id']}")
    for row in tables["resource_links"]:
        if row["resource_id"] not in resources:
            fk_failures.append(f"resource_links:{row['resource_link_id']}->resource:{row['resource_id']}")
        for field, lookup in (("paper_id", papers), ("study_id", studies), ("scenario_id", scenarios), ("metric_record_id", metrics)):
            if row[field] and row[field] not in lookup:
                fk_failures.append(f"resource_links:{row['resource_link_id']}->{field}:{row[field]}")
    for row in tables["claim_evidence_ledger"]:
        for field, lookup in (("paper_id", papers), ("study_id", studies), ("scenario_id", scenarios), ("metric_record_id", metrics)):
            if row[field] and row[field] not in lookup:
                fk_failures.append(f"claims:{row['claim_id']}->{field}:{row[field]}")
    _add(checks, "foreign_keys", not fk_failures, "All evidence-table foreign keys resolve", fk_failures)

    doi_duplicates = sorted(
        doi for doi, count in Counter(row["doi_normalized"] for row in papers.values() if row["doi_normalized"]).items() if count > 1
    )
    _add(checks, "doi_unique", not doi_duplicates, "Included paper DOIs are unique", doi_duplicates)

    main_by_family: dict[str, int] = defaultdict(int)
    for row in papers.values():
        if row["included_main_version"] == "yes":
            main_by_family[row["work_family_id"]] += 1
    bad_families = sorted(family for family, count in main_by_family.items() if count != 1)
    _add(checks, "one_main_version", not bad_families, "Each included work family has exactly one main version", bad_families)

    enum_failures = []
    enum_specs = [
        ("case_assets", "asset_class", set(rules["focal_assets"])),
        ("case_assets", "asset_role", set(rules["asset_roles"])),
        ("scenarios", "service_family", set(rules["service_families"])),
        ("scenarios", "service_type", set(rules["service_types"])),
        ("scenarios", "control_architecture", set(rules["control_architectures"])),
        ("scenarios", "highest_claim_level", set(rules["claim_levels"])),
        ("scenarios", "communication_generation_status", set(rules["communication_generation_statuses"])),
        ("papers", "publication_type", set(rules["publication_types"])),
        ("safeguards", "treatment_status", set(rules["safeguard_treatments"])),
    ]
    for table, field, allowed in enum_specs:
        for row in tables[table]:
            if row[field] not in allowed:
                enum_failures.append(f"{table}:{row[ID_FIELDS[table]]}:{field}={row[field]}")
    _add(checks, "controlled_vocabularies", not enum_failures, "Controlled vocabulary values are valid", enum_failures)

    setting_map = rules["validation_environment_to_evidence_setting"]
    setting_failures = [
        row["scenario_id"]
        for row in scenarios.values()
        if setting_map.get(row["validation_environment"]) != row["evidence_setting"]
    ]
    _add(checks, "evidence_setting_derived", not setting_failures, "E0-E5 codes derive from validation environment", setting_failures)

    active_by_scenario: dict[str, set[str]] = defaultdict(set)
    all_roles_by_scenario: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tables["case_assets"]:
        all_roles_by_scenario[row["scenario_id"]].append(row)
        if row["asset_role"] == "active_energy_asset" and row["active_flexibility_asset"] == "yes":
            active_by_scenario[row["scenario_id"]].add(row["asset_class"])
    classification_failures = []
    for scenario_id, row in scenarios.items():
        count = len(active_by_scenario[scenario_id])
        flags = all(
            row[field] == "yes"
            for field in (
                "coordination_active_decision_variables",
                "coordination_common_service_or_constraint",
                "coordination_joint_control_dispatch_or_clearing",
            )
        )
        derived_multi = count >= int(rules["multi_asset_rule"]["minimum_distinct_active_focal_classes"]) and flags
        if int(row["active_asset_class_count"]) != count or (row["multi_asset"] == "yes") != derived_multi:
            classification_failures.append(scenario_id)
        for asset in all_roles_by_scenario[scenario_id]:
            if asset["asset_role"] in {"compute_enabler", "communication_enabler"} and asset["active_flexibility_asset"] == "yes":
                classification_failures.append(asset["scenario_asset_id"])
    _add(checks, "multi_asset_classification", not classification_failures, "Multi-asset status derives from distinct active focal roles and all coordination tests", classification_failures)

    safeguard_failures = []
    for row in tables["safeguards"]:
        if row["asset_class"] not in active_by_scenario[row["scenario_id"]]:
            safeguard_failures.append(row["safeguard_id"])
    for scenario_id, active_assets in active_by_scenario.items():
        covered = {row["asset_class"] for row in tables["safeguards"] if row["scenario_id"] == scenario_id}
        for asset in active_assets - covered:
            safeguard_failures.append(f"{scenario_id}:{asset}:missing")
    _add(checks, "safeguard_links", not safeguard_failures, "Safeguards reference active assets and every active asset has coverage", safeguard_failures)

    metric_failures = []
    for row in tables["quantitative_values"]:
        record = row["metric_record_id"]
        if not row["source_locator"] or not row["metric_definition"] or not row["unit_raw"] or not row["value_status"]:
            metric_failures.append(f"{record}:minimum provenance")
        point, lower, upper = (_number(row[field]) for field in ("point_value", "lower_value", "upper_value"))
        if lower is not None and point is not None and lower > point:
            metric_failures.append(f"{record}:lower>point")
        if upper is not None and point is not None and point > upper:
            metric_failures.append(f"{record}:point>upper")
        if row["metric_code"] in rules["metric_time_codes"] and point is not None and point < 0:
            metric_failures.append(f"{record}:negative time")
        if row["metric_code"] == "percent_improvement":
            metric_failures.append(f"{record}:forbidden generic percent")
        if row["baseline_required"] == "yes" and not all(
            row[field] for field in ("baseline_type", "baseline_description", "denominator_raw", "system_boundary")
        ):
            metric_failures.append(f"{record}:incomplete baseline")
        if row["eligible_for_synthesis"] == "yes" and not row["comparability_signature"]:
            metric_failures.append(f"{record}:missing comparability signature")
        normalized = _number(row["normalized_point_value"])
        if row["transform_rule_id"] == "hours_to_seconds_x3600" and point is not None:
            if normalized is None or not math.isclose(normalized, point * 3600):
                metric_failures.append(f"{record}:bad hour conversion")
        if row["transform_rule_id"] == "minutes_to_seconds_x60" and point is not None:
            if normalized is None or not math.isclose(normalized, point * 60):
                metric_failures.append(f"{record}:bad minute conversion")
    _add(checks, "quantitative_values", not metric_failures, "Quantitative values preserve provenance, baselines, units and reversible conversions", metric_failures)

    operational_6g = [
        row["scenario_id"]
        for row in scenarios.values()
        if row["communication_generation_status"] == "future_imt2030_6g"
        and (row["live_control"] == "yes" or row["market_delivery"] == "yes" or row["evidence_setting"] in {"E4", "E5"})
    ]
    _add(checks, "six_g_status", not operational_6g, "Prospective IMT-2030/6G is never classified as operational delivery", operational_6g)

    locator_failures = []
    for row in tables["claim_evidence_ledger"]:
        if not row["source_locator"] and not (row["evidence_basis"] == "reviewer_derived" and row["derived_input_ids"] and row["derived_script"]):
            locator_failures.append(row["claim_id"])
    _add(checks, "claim_traceability", not locator_failures, "Every claim has a source locator or explicit derived-input lineage", locator_failures)

    screening = read_csv(FROZEN_DIR / "screening_log.csv")
    candidates = read_csv(FROZEN_DIR / "candidate_records.csv")
    _add(checks, "screening_complete", len(screening) == len(candidates), "Every candidate record has one screening disposition")
    exclusion_failures = [row["search_record_id"] for row in screening if row["fulltext_decision"] == "exclude" and not row["exclusion_code"]]
    _add(checks, "exclusion_codes", not exclusion_failures, "Every excluded record has a controlled exclusion reason", exclusion_failures)
    low_confidence_count = sum(row["screen_confidence"] == "low" for row in screening)
    manual_count = len(read_csv(FROZEN_DIR / "needs_manual_review.csv"))
    _add(checks, "manual_review_queue", low_confidence_count == manual_count, "Every low-confidence screen is queued for manual review", severity="warning" if low_confidence_count else "error")

    search_log = read_csv(FROZEN_DIR / "search_log.csv")
    source_counts = Counter(row["source_database"] for row in search_log)
    _add(
        checks,
        "enabled_query_families",
        source_counts["crossref"] == 95 and source_counts["openalex"] == 95,
        "All 95 configured query-family instances ran for both Crossref and OpenAlex",
    )
    raw_hash_failures = []
    for row in search_log:
        raw = row["raw_response_path"]
        if raw and raw != "not_applicable":
            path = REVIEW_ROOT / raw
            if not path.exists() or sha256_file(path) != row["raw_response_sha256"]:
                raw_hash_failures.append(f"{row['source_database']}:{row['query_id']}")
    _add(checks, "raw_response_hashes", not raw_hash_failures, "Raw metadata responses match frozen SHA-256 values", raw_hash_failures)

    source_inventory = read_csv(REVIEW_ROOT / "data" / "source_inventory.csv")
    inventory_failures = verify_source_inventory(source_inventory)
    _add(checks, "source_hashes", not inventory_failures, "All inventoried source PDF/DOCX hashes are unchanged", [item["repository_path"] for item in inventory_failures])
    _add(checks, "source_inventory_coverage", len(source_inventory) == 21, "All 21 pre-existing source PDF/DOCX files are inventoried")

    _add(
        checks,
        "manual_verification_limit",
        False,
        f"{manual_count} potentially relevant metadata records remain without full-text manual verification; status cannot be DONE.",
        severity="warning",
    )
    _add(
        checks,
        "prior_review_limit",
        bool(tables["reviews"]),
        "No prior review passed full-text verification in this bounded run; Supplementary Table S1 remains header-only.",
        severity="warning",
    )
    return checks


def write_validation_reports(checks: list[Check]) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    machine = RESULTS_DIR / "audit" / "validation_results.json"
    write_json(
        machine,
        {
            "schema_version": "1.0",
            "overall_status": "FAIL" if any(check.status == "FAIL" for check in checks) else "PASS_WITH_LIMITATIONS",
            "checks": [asdict(check) for check in checks],
        },
    )
    report = RESULTS_DIR / "qa_report.md"
    failures = [check for check in checks if check.status == "FAIL"]
    warnings = [check for check in checks if check.status == "WARN"]
    lines = [
        "# QA report",
        "",
        f"**Validation result:** {'FAIL' if failures else 'PASS with disclosed limitations'}",
        "",
        f"Checks: {len(checks)} total; {len(failures)} failures; {len(warnings)} warnings.",
        "",
        "| Check | Status | Message | Affected records |",
        "|---|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| `{check.check_id}` | {check.status} | {check.message} | {check.affected_records or '—'} |")
    lines += [
        "",
        "Warnings are coverage/manual-verification limitations, not schema or logic failures. Any FAIL blocks analysis rendering.",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return machine, report


def run_validation() -> list[Check]:
    checks = validate_frozen_data()
    write_validation_reports(checks)
    failures = [check for check in checks if check.status == "FAIL"]
    if failures:
        summary = "; ".join(f"{check.check_id}: {check.affected_records or check.message}" for check in failures)
        raise ValueError(f"Material validation errors: {summary}")
    return checks
