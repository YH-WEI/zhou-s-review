from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import numpy as np

from .common import (
    FROZEN_DIR,
    RESULTS_DIR,
    REVIEW_ROOT,
    load_yaml,
    pipe_join,
    read_csv,
    template_fields,
    write_csv,
    write_json,
)
from .discover import SEARCH_RUN_ID


EVIDENCE_RANK = {f"E{index}": index for index in range(6)}


def _highest(values: set[str]) -> str:
    return max(values, key=lambda value: EVIDENCE_RANK.get(value, -1)) if values else ""


def _ids(rows: list[dict[str, str]], field: str) -> int:
    return len({row[field] for row in rows if row.get(field)})


def _append_count(rows: list[dict[str, object]], dimension: str, value: str, scenarios: list[dict[str, str]], notes: str = "") -> None:
    rows.append(
        {
            "dimension": dimension,
            "value": value,
            "study_count": _ids(scenarios, "study_id"),
            "paper_count": _ids(scenarios, "paper_id"),
            "scenario_count": _ids(scenarios, "scenario_id"),
            "notes": notes or "Within the included corpus; counts are not performance or maturity scores.",
        }
    )


def _markdown_preview(rows: list[dict[str, object]], fields: list[str], limit: int = 10) -> list[str]:
    display = rows[:limit]
    if not display:
        return ["_Header-only: no eligible rows in this bounded corpus._"]
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    for row in display:
        lines.append("| " + " | ".join(str(row.get(field, "") or "—").replace("|", "/") for field in fields) + " |")
    if len(rows) > limit:
        lines.append(f"\n_Preview shows {limit} of {len(rows)} rows._")
    return lines


def run_analysis() -> dict[str, int]:
    rules = load_yaml(REVIEW_ROOT / "config" / "schema_rules.yml")
    config = load_yaml(REVIEW_ROOT / "config" / "search_plan.yml")
    tables_dir = RESULTS_DIR / "tables"
    audit_dir = RESULTS_DIR / "audit"
    tables_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    candidates = read_csv(FROZEN_DIR / "candidate_records.csv")
    screening = read_csv(FROZEN_DIR / "screening_log.csv")
    dedup = read_csv(FROZEN_DIR / "deduplication_log.csv")
    papers = read_csv(FROZEN_DIR / "papers.csv")
    studies = read_csv(FROZEN_DIR / "studies.csv")
    scenarios = read_csv(FROZEN_DIR / "scenarios.csv")
    case_assets = read_csv(FROZEN_DIR / "case_assets.csv")
    metrics = read_csv(FROZEN_DIR / "quantitative_values.csv")
    safeguards = read_csv(FROZEN_DIR / "safeguards.csv")
    reviews = read_csv(FROZEN_DIR / "reviews.csv")
    claims = read_csv(FROZEN_DIR / "claim_evidence_ledger.csv")
    manual = read_csv(FROZEN_DIR / "needs_manual_review.csv")
    paper_by_id = {row["paper_id"]: row for row in papers}
    study_by_id = {row["study_id"]: row for row in studies}
    scenario_by_id = {row["scenario_id"]: row for row in scenarios}
    active_assets: dict[str, set[str]] = defaultdict(set)
    asset_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in case_assets:
        asset_rows[row["scenario_id"]].append(row)
        if row["asset_role"] == "active_energy_asset" and row["active_flexibility_asset"] == "yes":
            active_assets[row["scenario_id"]].add(row["asset_class"])

    # Corpus flow
    duplicate_ids = {row["duplicate_record_id"] for row in dedup}
    canonical_screen = [row for row in screening if row["search_record_id"] not in duplicate_ids]
    flow: list[dict[str, object]] = []

    def flow_row(stage: str, reason: str, record_count: int = 0, paper_count: int = 0, study_count: int = 0, scenario_count: int = 0, notes: str = "") -> None:
        flow.append(
            {
                "stage": stage,
                "reason": reason,
                "record_count": record_count,
                "paper_count": paper_count,
                "study_count": study_count,
                "scenario_count": scenario_count,
                "notes": notes,
            }
        )

    flow_row("identified", "all_sources", len(candidates), notes="Repository records plus bounded Crossref/OpenAlex results.")
    source_query_counts = Counter((row["source_database"], row["query_family"]) for row in candidates)
    for (source, family), count in sorted(source_query_counts.items()):
        flow_row("identified_by_source_query_family", f"{source}:{family}", count)
    flow_row("deduplicated", "after_normalized_doi_and_exact_title_year", len(candidates) - len(dedup), notes="No fuzzy-only merge was performed.")
    title_exclusion_counts = Counter(
        row["exclusion_code"]
        for row in canonical_screen
        if row["title_abstract_decision"] == "exclude" and row["exclusion_code"] != "X07_duplicate_version"
    )
    for reason, count in sorted(title_exclusion_counts.items()):
        flow_row("title_abstract_excluded", reason, count)
    sought = [row for row in canonical_screen if row["title_abstract_decision"] == "include"]
    obtained = [row for row in sought if row["fulltext_decision"] == "include"]
    unavailable = [row for row in sought if row["exclusion_code"] == "X10_fulltext_unavailable_for_required_verification"]
    flow_row("fulltext", "sought", len(sought))
    flow_row("fulltext", "obtained_and_verified", len(obtained))
    flow_row("fulltext", "unavailable_or_not_verified", len(unavailable))
    fulltext_exclusions = Counter(row["exclusion_code"] for row in sought if row["fulltext_decision"] == "exclude")
    for reason, count in sorted(fulltext_exclusions.items()):
        flow_row("fulltext_excluded", reason, count)
    flow_row("included", "prior_reviews", paper_count=len(reviews), notes="Prior-review table is header-only in this bounded run.")
    flow_row("included", "primary_evidence", paper_count=len(papers), study_count=len(studies), scenario_count=len(scenarios))
    multi_scenarios = [row for row in scenarios if row["multi_asset"] == "yes"]
    flow_row("included", "multi_asset_evidence", paper_count=_ids(multi_scenarios, "paper_id"), study_count=_ids(multi_scenarios, "study_id"), scenario_count=len(multi_scenarios))
    flow_row("manual_verification", "required", len(manual), notes="Not included in evidence calculations.")
    write_csv(
        tables_dir / "corpus_flow.csv",
        ["stage", "reason", "record_count", "paper_count", "study_count", "scenario_count", "notes"],
        flow,
    )

    # Within-corpus evidence map
    count_rows: list[dict[str, object]] = []
    for asset in rules["focal_assets"]:
        subset = [scenario for scenario in scenarios if asset in active_assets[scenario["scenario_id"]]]
        _append_count(count_rows, "asset_class", asset, subset)
    combinations: dict[str, list[dict[str, str]]] = defaultdict(list)
    size_classes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for scenario in scenarios:
        combination = "+".join(sorted(active_assets[scenario["scenario_id"]]))
        combinations[combination].append(scenario)
        size = len(active_assets[scenario["scenario_id"]])
        size_classes["S1" if size == 1 else ("S2" if size == 2 else "S3+")].append(scenario)
    for value, subset in sorted(combinations.items()):
        _append_count(count_rows, "asset_combination", value, subset)
    for value in ("S1", "S2", "S3+"):
        _append_count(count_rows, "participating_focal_asset_classes", value, size_classes.get(value, []))
    for dimension, field, allowed in (
        ("grid_service", "service_family", rules["service_families"]),
        ("evidence_setting", "evidence_setting", [f"E{i}" for i in range(6)]),
        ("claim_level", "highest_claim_level", rules["claim_levels"]),
        ("coordination_topology", "control_architecture", rules["control_architectures"]),
        ("matched_coordination_counterfactual", "matched_coordination_counterfactual", ["yes", "no", "unknown"]),
    ):
        for value in allowed:
            _append_count(count_rows, dimension, value, [row for row in scenarios if row[field] == value])
    for publication_type in rules["publication_types"]:
        subset = [scenario for scenario in scenarios if paper_by_id[scenario["paper_id"]]["publication_type"] == publication_type]
        _append_count(count_rows, "publication_type", publication_type, subset)
    for year in sorted({paper["publication_year"] for paper in papers}):
        _append_count(count_rows, "publication_year", year, [scenario for scenario in scenarios if paper_by_id[scenario["paper_id"]]["publication_year"] == year])
    for region in sorted({paper["region_or_jurisdiction"] for paper in papers}):
        _append_count(count_rows, "region_or_jurisdiction", region, [scenario for scenario in scenarios if paper_by_id[scenario["paper_id"]]["region_or_jurisdiction"] == region])
    explicit_treatments = {"hard_constraint", "soft_penalty", "ex_post_check", "scenario_assumption"}
    for label in ("explicit_or_modelled", "only_unreported_not_considered_or_not_applicable"):
        subset = []
        for scenario in scenarios:
            has_explicit = any(row["scenario_id"] == scenario["scenario_id"] and row["treatment_status"] in explicit_treatments for row in safeguards)
            if (label == "explicit_or_modelled") == has_explicit:
                subset.append(scenario)
        _append_count(count_rows, "primary_service_safeguard_reporting", label, subset)
    for label in ("peer_reviewed", "preprint", "grey_or_commercial"):
        subset = []
        for scenario in scenarios:
            pub = paper_by_id[scenario["paper_id"]]["publication_type"]
            match = pub == "preprint" if label == "preprint" else (
                pub in {"institutional_project_report", "commercial_self_report", "official_agency_or_market"} if label == "grey_or_commercial" else pub.startswith("peer_reviewed")
            )
            if match:
                subset.append(scenario)
        _append_count(count_rows, "preprint_grey_status", label, subset)
    write_csv(tables_dir / "corpus_counts.csv", ["dimension", "value", "study_count", "paper_count", "scenario_count", "notes"], count_rows)

    asset_service_rows = []
    for asset in rules["focal_assets"]:
        for service in rules["service_families"]:
            subset = [
                scenario
                for scenario in scenarios
                if asset in active_assets[scenario["scenario_id"]] and scenario["service_family"] == service
            ]
            settings = {row["evidence_setting"] for row in subset}
            asset_service_rows.append(
                {
                    "asset_class": asset,
                    "service_family": service,
                    "study_count": _ids(subset, "study_id"),
                    "paper_count": _ids(subset, "paper_id"),
                    "scenario_count": len(subset),
                    "highest_evidence_setting": _highest(settings),
                    "interpretation": "Evidence identified within included corpus" if subset else "No eligible evidence identified in this corpus; not technical impossibility",
                }
            )
    write_csv(
        tables_dir / "evidence_by_asset_service.csv",
        ["asset_class", "service_family", "study_count", "paper_count", "scenario_count", "highest_evidence_setting", "interpretation"],
        asset_service_rows,
    )

    maturity_rows = []
    for setting in [f"E{i}" for i in range(6)]:
        subset = [row for row in scenarios if row["evidence_setting"] == setting]
        maturity_rows.append(
            {
                "evidence_setting": setting,
                "study_count": _ids(subset, "study_id"),
                "paper_count": _ids(subset, "paper_id"),
                "scenario_count": len(subset),
                "notes": "Setting descriptor only; not a quality or maturity score.",
            }
        )
    write_csv(tables_dir / "evidence_maturity_counts.csv", ["evidence_setting", "study_count", "paper_count", "scenario_count", "notes"], maturity_rows)

    year_region: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for scenario in scenarios:
        paper = paper_by_id[scenario["paper_id"]]
        year_region[(paper["publication_year"], paper["region_or_jurisdiction"])].append(scenario)
    year_region_rows = [
        {
            "publication_year": year,
            "region_or_jurisdiction": region,
            "study_count": _ids(subset, "study_id"),
            "paper_count": _ids(subset, "paper_id"),
            "scenario_count": len(subset),
            "notes": "Within the included corpus.",
        }
        for (year, region), subset in sorted(year_region.items())
    ]
    write_csv(tables_dir / "evidence_by_year_region.csv", ["publication_year", "region_or_jurisdiction", "study_count", "paper_count", "scenario_count", "notes"], year_region_rows)

    # Fig. 4 source data and ledger
    mechanism_keys = []
    for row in case_assets:
        if row["asset_role"] == "active_energy_asset" and row["active_flexibility_asset"] == "yes":
            key = (row["asset_class"], row["flexibility_resource"])
            if key not in mechanism_keys:
                mechanism_keys.append(key)
    mechanism_keys.sort()
    mechanism_ids = {key: f"MECH{index:03d}" for index, key in enumerate(mechanism_keys, 1)}
    fig4_rows = []
    fig4_ledger = []
    for asset, mechanism in mechanism_keys:
        for service in rules["service_families"]:
            subset = []
            for scenario in scenarios:
                if scenario["service_family"] != service:
                    continue
                if any(
                    item["scenario_id"] == scenario["scenario_id"]
                    and item["asset_class"] == asset
                    and item["flexibility_resource"] == mechanism
                    and item["asset_role"] == "active_energy_asset"
                    for item in case_assets
                ):
                    subset.append(scenario)
            settings = {row["evidence_setting"] for row in subset}
            highest = _highest(settings)
            code = "D" if highest in {"E3", "E4", "E5"} else ("M" if highest in {"E1", "E2"} else ("I" if highest == "E0" else ""))
            fig4_rows.append(
                {
                    "mechanism_id": mechanism_ids[(asset, mechanism)],
                    "asset_class": asset,
                    "flexibility_mechanism": mechanism,
                    "service_family": service,
                    "evidence_code": code,
                    "study_count": _ids(subset, "study_id"),
                    "highest_evidence_setting": highest,
                    "cell_label": f"{code} n={_ids(subset, 'study_id')}" if subset else "",
                    "interpretation": "Blank means not identified in this corpus, not impossible." if not subset else "Highest setting and unique-study count shown separately.",
                }
            )
            for scenario in subset:
                source_asset = next(
                    item
                    for item in case_assets
                    if item["scenario_id"] == scenario["scenario_id"]
                    and item["asset_class"] == asset
                    and item["flexibility_resource"] == mechanism
                    and item["asset_role"] == "active_energy_asset"
                )
                fig4_ledger.append(
                    {
                        "mechanism_id": mechanism_ids[(asset, mechanism)],
                        "service_family": service,
                        "evidence_code": code,
                        "paper_id": scenario["paper_id"],
                        "study_id": scenario["study_id"],
                        "scenario_id": scenario["scenario_id"],
                        "source_locator": source_asset["source_locator"],
                        "evidence_note": source_asset["evidence_note"],
                        "verification_status": source_asset["verification_status"],
                    }
                )
    write_csv(
        tables_dir / "fig4_mechanism_service_matrix.csv",
        ["mechanism_id", "asset_class", "flexibility_mechanism", "service_family", "evidence_code", "study_count", "highest_evidence_setting", "cell_label", "interpretation"],
        fig4_rows,
    )
    write_csv(
        audit_dir / "fig4_source_ledger.csv",
        ["mechanism_id", "service_family", "evidence_code", "paper_id", "study_id", "scenario_id", "source_locator", "evidence_note", "verification_status"],
        fig4_ledger,
    )

    # Timescale map
    metrics_by_scenario: dict[str, list[dict[str, str]]] = defaultdict(list)
    for metric in metrics:
        metrics_by_scenario[metric["scenario_id"]].append(metric)
    timescale_rows = []
    time_fields = {
        "activation_latency_s": ("activation_latency_raw", "activation_latency_s"),
        "full_response_time_s": ("full_response_time_raw", "full_response_time_s"),
        "sustain_duration_s": ("sustain_duration_raw", "sustain_duration_s"),
        "planning_horizon_s": ("planning_horizon_raw", "planning_horizon_s"),
        "communication_latency_s": ("communication_latency_raw", "communication_latency_s"),
        "controller_runtime_s": ("controller_runtime_raw", "controller_runtime_s"),
    }
    for scenario in scenarios:
        for asset in sorted(active_assets[scenario["scenario_id"]]):
            out: dict[str, object] = {
                "scenario_id": scenario["scenario_id"],
                "study_id": scenario["study_id"],
                "paper_id": scenario["paper_id"],
                "asset_class": asset,
                "service_family": scenario["service_family"],
                "reporting_note": "Distinct time concepts; blanks mean not reported, never zero.",
                "source_locator": scenario["source_page"],
            }
            for metric_code, (raw_field, normalized_field) in time_fields.items():
                match = next((metric for metric in metrics_by_scenario[scenario["scenario_id"]] if metric["metric_code"] == metric_code), None)
                out[raw_field] = f"{match['point_value']} {match['unit_raw']}" if match else ""
                out[normalized_field] = match["normalized_point_value"] if match else ""
                if match:
                    out["source_locator"] = pipe_join([str(out["source_locator"]), match["source_locator"]])
            timescale_rows.append(out)
    timescale_fields = [
        "scenario_id", "study_id", "paper_id", "asset_class", "service_family",
        "activation_latency_raw", "activation_latency_s", "full_response_time_raw", "full_response_time_s",
        "sustain_duration_raw", "sustain_duration_s", "planning_horizon_raw", "planning_horizon_s",
        "communication_latency_raw", "communication_latency_s", "controller_runtime_raw", "controller_runtime_s",
        "reporting_note", "source_locator",
    ]
    write_csv(tables_dir / "asset_service_timescale_map.csv", timescale_fields, timescale_rows)

    # Reporting completeness by asset/service/evidence stratum
    safeguard_by_scenario: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in safeguards:
        safeguard_by_scenario[row["scenario_id"]].append(row)
    completeness_rows = []
    items = [
        "baseline_counterfactual", "asset_size_and_boundary", "activation_and_full_response_time",
        "sustainable_duration_or_duty_cycle", "rebound_or_recovery", "uncertainty_or_forecast_error",
        "failure_optout_or_communication_loss", "primary_service_metric_and_result", "digital_overhead",
        "battery_degradation_where_relevant", "grid_location_or_network_constraint",
        "economic_boundary_where_claimed", "carbon_factor_where_claimed",
    ]
    strata: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for scenario in scenarios:
        for asset in active_assets[scenario["scenario_id"]]:
            strata[(asset, scenario["service_family"], scenario["evidence_setting"])].append(scenario)
    for (asset, service, setting), subset in sorted(strata.items()):
        for item in items:
            applicable: list[dict[str, str]] = []
            reported: list[dict[str, str]] = []
            for scenario in subset:
                scenario_metrics = metrics_by_scenario[scenario["scenario_id"]]
                active_rows = [row for row in asset_rows[scenario["scenario_id"]] if row["asset_class"] == asset and row["asset_role"] == "active_energy_asset"]
                value = False
                is_applicable = True
                if item == "baseline_counterfactual":
                    value = bool(scenario["baseline_description"])
                elif item == "asset_size_and_boundary":
                    value = bool(scenario["system_boundary"]) and all(row["nominal_capacity_status"] == "source_reported" for row in active_rows)
                elif item == "activation_and_full_response_time":
                    value = any(row["metric_code"] in {"activation_latency_s", "full_response_time_s"} for row in scenario_metrics)
                elif item == "sustainable_duration_or_duty_cycle":
                    value = any(row["metric_code"] == "sustain_duration_s" for row in scenario_metrics)
                elif item == "rebound_or_recovery":
                    value = any("rebound" in row["metric_code"] or "recovery" in row["metric_code"] for row in scenario_metrics)
                elif item == "uncertainty_or_forecast_error":
                    value = scenario["uncertainty_considered"] == "yes"
                elif item == "failure_optout_or_communication_loss":
                    value = scenario["failure_scenario_considered"] == "yes"
                elif item == "primary_service_metric_and_result":
                    rows_for_asset = [row for row in safeguard_by_scenario[scenario["scenario_id"]] if row["asset_class"] == asset]
                    value = any(row["result_status"] == "source_reported" and row["constraint_type"] not in {"battery_degradation"} for row in rows_for_asset)
                elif item == "digital_overhead":
                    value = scenario["digital_overhead_considered"] == "yes"
                elif item == "battery_degradation_where_relevant":
                    is_applicable = asset == "EV" or any("battery" in row["flexibility_resource"].lower() for row in active_rows)
                    value = any(row["constraint_type"] == "battery_degradation" and row["treatment_status"] not in {"not_reported", "not_considered", "not_applicable", "unclear"} for row in safeguard_by_scenario[scenario["scenario_id"]])
                elif item == "grid_location_or_network_constraint":
                    value = scenario["network_constraint_considered"] == "yes"
                elif item == "economic_boundary_where_claimed":
                    is_applicable = any(row["currency"] or "cost" in row["metric_code"] or "economic" in row["metric_code"] for row in scenario_metrics)
                    value = is_applicable and all(row["jurisdiction"] for row in scenario_metrics if row["currency"] or "cost" in row["metric_code"] or "economic" in row["metric_code"])
                elif item == "carbon_factor_where_claimed":
                    is_applicable = any(row["carbon_factor_type"] or "carbon" in row["metric_code"] for row in scenario_metrics)
                    value = is_applicable and all(row["carbon_factor_type"] and row["system_boundary"] for row in scenario_metrics if row["carbon_factor_type"] or "carbon" in row["metric_code"])
                if is_applicable:
                    applicable.append(scenario)
                    if value:
                        reported.append(scenario)
            denominator = _ids(applicable, "study_id")
            numerator = _ids(reported, "study_id")
            completeness_rows.append(
                {
                    "asset_class": asset,
                    "service_family": service,
                    "evidence_setting": setting,
                    "reporting_item": item,
                    "reported_study_count": numerator,
                    "applicable_study_denominator": denominator,
                    "reported_share_percent": round(100 * numerator / denominator, 1) if denominator else "",
                    "applicability_status": "applicable" if denominator else "not_applicable_in_stratum",
                    "notes": "Missing/unknown is not zero; denominator is unique applicable study_id.",
                }
            )
    write_csv(
        tables_dir / "reporting_completeness.csv",
        ["asset_class", "service_family", "evidence_setting", "reporting_item", "reported_study_count", "applicable_study_denominator", "reported_share_percent", "applicability_status", "notes"],
        completeness_rows,
    )

    # Seven-part comparability gate
    comparability_rows = []
    eligible_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for metric in metrics:
        scenario = scenario_by_id[metric["scenario_id"]]
        group_id = ""
        if metric["eligible_for_synthesis"] == "yes":
            group_id = "CG_" + hashlib.sha256(metric["comparability_signature"].encode("utf-8")).hexdigest()[:10]
            eligible_groups[group_id].append(metric)
    group_n = {group: len({row["study_id"] for row in rows}) for group, rows in eligible_groups.items()}
    for metric in metrics:
        scenario = scenario_by_id[metric["scenario_id"]]
        group_id = "CG_" + hashlib.sha256(metric["comparability_signature"].encode("utf-8")).hexdigest()[:10] if metric["eligible_for_synthesis"] == "yes" else ""
        if metric["eligible_for_synthesis"] == "yes":
            decision = "accepted_context_only_below_five_studies" if group_n[group_id] < config["comparability"]["minimum_independent_studies_for_central_summary"] else "accepted_for_descriptive_central_summary"
            reason = "All seven attributes are populated, but fewer than five independent studies prohibit a central estimate." if group_n[group_id] < 5 else "Seven-part gate and minimum independent-study count passed."
        else:
            decision = "rejected"
            reason = metric["noncomparability_reason"]
        comparability_rows.append(
            {
                "metric_record_id": metric["metric_record_id"],
                "paper_id": metric["paper_id"],
                "study_id": metric["study_id"],
                "scenario_id": metric["scenario_id"],
                "metric_code": metric["metric_code"],
                "metric_definition": metric["metric_definition"],
                "denominator_code": metric["denominator_code"],
                "baseline_type": metric["baseline_type"],
                "system_boundary": metric["system_boundary"],
                "temporal_horizon": metric["temporal_horizon"],
                "service_family": scenario["service_family"],
                "validation_setting": scenario["evidence_setting"],
                "normalized_unit": metric["normalized_unit"],
                "comparability_group_id": group_id,
                "gate_decision": decision,
                "independent_study_count": group_n.get(group_id, 0),
                "reason": reason,
                "source_locator": metric["source_locator"],
            }
        )
    write_csv(
        tables_dir / "comparability_audit.csv",
        ["metric_record_id", "paper_id", "study_id", "scenario_id", "metric_code", "metric_definition", "denominator_code", "baseline_type", "system_boundary", "temporal_horizon", "service_family", "validation_setting", "normalized_unit", "comparability_group_id", "gate_decision", "independent_study_count", "reason", "source_locator"],
        comparability_rows,
    )
    numeric_summary_rows = []
    for group_id, group_metrics in sorted(eligible_groups.items()):
        values = [float(row["normalized_point_value"]) for row in group_metrics if row["normalized_point_value"]]
        unique_studies = {row["study_id"] for row in group_metrics}
        n = len(unique_studies)
        enough = n >= int(config["comparability"]["minimum_independent_studies_for_central_summary"])
        numeric_summary_rows.append(
            {
                "comparability_group_id": group_id,
                "metric_code": group_metrics[0]["metric_code"],
                "normalized_unit": group_metrics[0]["normalized_unit"],
                "independent_study_n": n,
                "summary_status": "descriptive_central_summary" if enough else "individual_values_and_contextual_range_only",
                "individual_values": pipe_join(str(value) for value in values),
                "minimum": min(values) if values else "",
                "maximum": max(values) if values else "",
                "median": median(values) if enough and values else "",
                "q1": float(np.quantile(values, 0.25)) if enough and values else "",
                "q3": float(np.quantile(values, 0.75)) if enough and values else "",
                "notes": "No central estimate: fewer than five independent comparable studies." if not enough else "Median and quartiles only; no inferential statistics.",
            }
        )
    write_csv(
        tables_dir / "comparable_numeric_summaries.csv",
        ["comparability_group_id", "metric_code", "normalized_unit", "independent_study_n", "summary_status", "individual_values", "minimum", "maximum", "median", "q1", "q3", "notes"],
        numeric_summary_rows,
    )

    # Draft tables
    table1_rows = []
    for asset_row in case_assets:
        if asset_row["asset_role"] != "active_energy_asset":
            continue
        scenario = scenario_by_id[asset_row["scenario_id"]]
        scenario_metrics = metrics_by_scenario[scenario["scenario_id"]]
        time_bits = [
            f"{metric['metric_name_raw']}: {metric['point_value']} {metric['unit_raw']}"
            for metric in scenario_metrics
            if metric["metric_code"] in {"activation_latency_s", "full_response_time_s", "sustain_duration_s", "ramp_transition_duration_s"}
        ]
        if not any(metric["metric_code"] in {"activation_latency_s", "full_response_time_s"} for metric in scenario_metrics):
            time_bits.append("activation/full physical response time not reported")
        safeguard_bits = [
            f"{row['constraint_type']}={row['treatment_status']}"
            for row in safeguard_by_scenario[scenario["scenario_id"]]
            if row["asset_class"] == asset_row["asset_class"]
        ]
        table1_rows.append(
            {
                "asset_class": asset_row["asset_class"],
                "flexibility_mechanism": asset_row["flexibility_resource"],
                "direction": asset_row["flexibility_direction"],
                "reported_response_and_duration_evidence": "; ".join(time_bits),
                "spatial_availability": scenario["geographic_scale"],
                "observability_and_control_needs": f"{asset_row['decision_variable']}; metering: {asset_row['energy_metering_point']}; topology: {scenario['control_architecture']}",
                "primary_service_guardrails": "; ".join(safeguard_bits),
                "suitable_service_conditions": scenario["service_family"],
                "evidence_setting": scenario["evidence_setting"],
                "evidence_limits": scenario["notes"],
                "paper_id": scenario["paper_id"],
                "study_id": scenario["study_id"],
                "scenario_id": scenario["scenario_id"],
                "source_locator": asset_row["source_locator"],
            }
        )
    write_csv(
        tables_dir / "table1_asset_comparison_draft.csv",
        ["asset_class", "flexibility_mechanism", "direction", "reported_response_and_duration_evidence", "spatial_availability", "observability_and_control_needs", "primary_service_guardrails", "suitable_service_conditions", "evidence_setting", "evidence_limits", "paper_id", "study_id", "scenario_id", "source_locator"],
        table1_rows,
    )

    table2_rows = []
    for scenario in multi_scenarios:
        paper = paper_by_id[scenario["paper_id"]]
        active = "+".join(sorted(active_assets[scenario["scenario_id"]]))
        scenario_metrics = metrics_by_scenario[scenario["scenario_id"]]
        table2_rows.append(
            {
                "service_family": scenario["service_family"],
                "study_and_region": f"{paper['first_author']} et al. ({paper['publication_year']}); {paper['region_or_jurisdiction']}",
                "asset_combination": active,
                "scale": f"{scenario['electrical_scale']}|{scenario['geographic_scale']}",
                "coordination_and_communication": f"{scenario['control_architecture']}; {scenario['communication_generation_status']}",
                "evidence_setting": scenario["evidence_setting"],
                "data_and_duration": scenario["data_source_type"],
                "baseline": scenario["baseline_description"],
                "metrics": pipe_join(metric["metric_code"] for metric in scenario_metrics),
                "primary_service_safeguards": "; ".join(f"{row['asset_class']}:{row['constraint_type']}={row['treatment_status']}" for row in safeguard_by_scenario[scenario["scenario_id"]]),
                "result": "; ".join(f"{metric['metric_name_raw']}={metric['point_value']} {metric['unit_raw']}" for metric in scenario_metrics),
                "limitation": scenario["notes"],
                "paper_id": scenario["paper_id"],
                "study_id": scenario["study_id"],
                "scenario_id": scenario["scenario_id"],
                "source_locator": pipe_join(metric["source_locator"] for metric in scenario_metrics) or scenario["source_page"],
                "selection_rule": "Complete coverage of every eligible multi-asset study in the frozen corpus.",
            }
        )
    write_csv(
        tables_dir / "table2_multi_asset_evidence_draft.csv",
        ["service_family", "study_and_region", "asset_combination", "scale", "coordination_and_communication", "evidence_setting", "data_and_duration", "baseline", "metrics", "primary_service_safeguards", "result", "limitation", "paper_id", "study_id", "scenario_id", "source_locator", "selection_rule"],
        table2_rows,
    )
    write_csv(tables_dir / "supp_table_s1_prior_reviews.csv", template_fields("reviews"), reviews)

    supp_s2_rows = []
    for scenario in scenarios:
        paper = paper_by_id[scenario["paper_id"]]
        study = study_by_id[scenario["study_id"]]
        supp_s2_rows.append(
            {
                "paper_id": paper["paper_id"],
                "study_id": study["study_id"],
                "scenario_id": scenario["scenario_id"],
                "title": paper["title"],
                "publication_year": paper["publication_year"],
                "doi_normalized": paper["doi_normalized"],
                "publication_type": paper["publication_type"],
                "region_or_jurisdiction": paper["region_or_jurisdiction"],
                "asset_combination": "+".join(sorted(active_assets[scenario["scenario_id"]])),
                "service_family": scenario["service_family"],
                "evidence_setting": scenario["evidence_setting"],
                "highest_claim_level": scenario["highest_claim_level"],
                "multi_asset": scenario["multi_asset"],
                "source_locator": scenario["source_page"],
                "verification_status": scenario["verification_status"],
            }
        )
    write_csv(
        tables_dir / "supp_table_s2_included_studies.csv",
        ["paper_id", "study_id", "scenario_id", "title", "publication_year", "doi_normalized", "publication_type", "region_or_jurisdiction", "asset_combination", "service_family", "evidence_setting", "highest_claim_level", "multi_asset", "source_locator", "verification_status"],
        supp_s2_rows,
    )

    # Sensitivity counts
    def sensitivity_row(variant: str, subset: list[dict[str, str]], notes: str) -> dict[str, object]:
        multi = [row for row in subset if row["multi_asset"] == "yes"]
        return {
            "variant": variant,
            "paper_count": _ids(subset, "paper_id"),
            "study_count": _ids(subset, "study_id"),
            "scenario_count": len(subset),
            "multi_asset_paper_count": _ids(multi, "paper_id"),
            "multi_asset_study_count": _ids(multi, "study_id"),
            "multi_asset_scenario_count": len(multi),
            "manual_verification_queue_count": len(manual),
            "notes": notes,
        }
    sensitivity_rows = [
        sensitivity_row("all_verified_included", scenarios, "Headline unit is unique study_id; paper and scenario counts shown alongside."),
        sensitivity_row("exclude_preprints", [row for row in scenarios if paper_by_id[row["paper_id"]]["publication_type"] != "preprint"], "No included preprint in this corpus."),
        sensitivity_row("exclude_grey_and_commercial", [row for row in scenarios if paper_by_id[row["paper_id"]]["publication_type"] not in {"institutional_project_report", "commercial_self_report", "official_agency_or_market"}], "No included grey/commercial source in this corpus."),
        sensitivity_row("paper_level_counting", scenarios, "Paper count shown explicitly; repeated projects would still be controlled through study_id."),
        sensitivity_row("unique_study_level_counting", scenarios, "Primary headline counting unit."),
        sensitivity_row("exclude_awaiting_manual_verification", scenarios, "Awaiting records are already excluded from calculations; queue size disclosed."),
    ]
    write_csv(
        tables_dir / "sensitivity_counts.csv",
        ["variant", "paper_count", "study_count", "scenario_count", "multi_asset_paper_count", "multi_asset_study_count", "multi_asset_scenario_count", "manual_verification_queue_count", "notes"],
        sensitivity_rows,
    )

    # Verification package
    audit_scenario_fields = [
        "scenario_id", "study_id", "paper_id", "asset_combination", "service_family", "evidence_setting",
        "highest_claim_level", "source_locator", "verification_status", "reason_for_mandatory_review",
    ]
    multi_audit = [
        {
            "scenario_id": row["scenario_id"], "study_id": row["study_id"], "paper_id": row["paper_id"],
            "asset_combination": "+".join(sorted(active_assets[row["scenario_id"]])), "service_family": row["service_family"],
            "evidence_setting": row["evidence_setting"], "highest_claim_level": row["highest_claim_level"],
            "source_locator": row["source_page"], "verification_status": row["verification_status"],
            "reason_for_mandatory_review": "multi_asset",
        }
        for row in scenarios if row["multi_asset"] == "yes"
    ]
    field_audit = [
        {
            "scenario_id": row["scenario_id"], "study_id": row["study_id"], "paper_id": row["paper_id"],
            "asset_combination": "+".join(sorted(active_assets[row["scenario_id"]])), "service_family": row["service_family"],
            "evidence_setting": row["evidence_setting"], "highest_claim_level": row["highest_claim_level"],
            "source_locator": row["source_page"], "verification_status": row["verification_status"],
            "reason_for_mandatory_review": "E4_or_E5",
        }
        for row in scenarios if row["evidence_setting"] in {"E4", "E5"}
    ]
    sixg_audit = [
        {
            "scenario_id": row["scenario_id"], "study_id": row["study_id"], "paper_id": row["paper_id"],
            "asset_combination": "+".join(sorted(active_assets[row["scenario_id"]])), "service_family": row["service_family"],
            "evidence_setting": row["evidence_setting"], "highest_claim_level": row["highest_claim_level"],
            "source_locator": row["source_page"], "verification_status": row["verification_status"],
            "reason_for_mandatory_review": "6g_status",
        }
        for row in scenarios if row["communication_generation_status"] in {"future_imt2030_6g", "b5g_research", "5g_advanced"}
    ]
    write_csv(audit_dir / "all_multiasset_records.csv", audit_scenario_fields, multi_audit)
    write_csv(audit_dir / "all_E4_E5_records.csv", audit_scenario_fields, field_audit)
    write_csv(audit_dir / "all_6g_status_records.csv", audit_scenario_fields, sixg_audit)
    write_csv(
        audit_dir / "all_aggregated_values.csv",
        ["comparability_group_id", "metric_record_id", "study_id", "scenario_id", "normalized_point_value", "normalized_unit", "source_locator", "notes"],
        [],
    )
    write_csv(audit_dir / "strong_claim_sources.csv", template_fields("claim_evidence_ledger"), claims)
    mandatory_scenarios = {row["scenario_id"] for row in multi_audit + field_audit + sixg_audit}
    mandatory_scenarios.update(row["scenario_id"] for row in claims if row["scenario_id"])
    remaining = [row for row in scenarios if row["scenario_id"] not in mandatory_scenarios]
    sample_size = int(np.ceil(len(remaining) * 0.2)) if remaining else 0
    sample = sorted(remaining, key=lambda row: hashlib.sha256(f"{config['counting']['verification_sample_seed']}:{row['scenario_id']}".encode()).hexdigest())[:sample_size]
    sample_rows = [
        {
            "scenario_id": row["scenario_id"],
            "study_id": row["study_id"],
            "paper_id": row["paper_id"],
            "asset_combination": "+".join(sorted(active_assets[row["scenario_id"]])),
            "evidence_setting": row["evidence_setting"],
            "sample_seed": config["counting"]["verification_sample_seed"],
            "source_locator": row["source_page"],
            "notes": "Fixed-seed stratified remainder sample.",
        }
        for row in sample
    ]
    write_csv(
        audit_dir / "stratified_review_sample.csv",
        ["scenario_id", "study_id", "paper_id", "asset_combination", "evidence_setting", "sample_seed", "source_locator", "notes"],
        sample_rows,
    )

    # Reports and run manifest
    included_papers = len(papers)
    included_studies = len(studies)
    included_scenarios = len(scenarios)
    multi_studies = _ids(multi_scenarios, "study_id")
    central_groups = [row for row in numeric_summary_rows if row["summary_status"] == "descriptive_central_summary"]
    summary_lines = [
        "# Evidence-map analysis summary",
        "",
        "## Answer first",
        "",
        f"This bounded, reproducible run included **{included_papers} papers, {included_studies} unique studies and {included_scenarios} scenarios** after screening. "
        f"It identified **{multi_studies} unique multi-asset study** within the included corpus. The result is descriptive evidence mapping, not a systematic review or meta-analysis.",
        "",
        f"No comparability group reached the required five independent studies; **{len(central_groups)} central numeric summaries were produced**. Individual verified values remain contextual.",
        "",
        "## Corpus flow preview",
        "",
        *_markdown_preview(flow, ["stage", "reason", "record_count", "paper_count", "study_count", "scenario_count"], 14),
        "",
        "## Within-corpus evidence",
        "",
        "- The DC record is an `E4` controlled field pilot for peak-demand response; it is not sustained market operation.",
        "- The EV-BLDG record is an `E1` synthetic/modelled renewable-integration scenario; it is not field delivery.",
        "- No included active-energy BS or operational 6G scenario was identified. This is only a statement about the included corpus.",
        "- Primary-service reporting is incomplete: the field trial reports workload SLA outcomes, while the modelled EV-building scenario lacks several mobility/building guardrail outcomes.",
        "",
        "## Fig. 4 matrix preview",
        "",
        *_markdown_preview([row for row in fig4_rows if row["evidence_code"]], ["asset_class", "flexibility_mechanism", "service_family", "evidence_code", "study_count", "highest_evidence_setting"], 10),
        "",
        "`D` means E3-E5 demonstrated evidence, `M` means E1-E2 modelled/replayed evidence, and blank means not identified under this protocol—not impossible.",
        "",
        "## Multi-asset Table 2 preview",
        "",
        *_markdown_preview(table2_rows, ["service_family", "study_and_region", "asset_combination", "evidence_setting", "result", "limitation"], 10),
        "",
        "## Comparability conclusion",
        "",
        "Insufficient comparability for a central numeric synthesis. Peak-power reduction, duration, SLA outcomes and lifecycle-carbon values differ in metric definition, denominator, boundary, horizon, service and/or validation setting. The two gate-complete singleton values are listed individually; neither is averaged.",
        "",
        "## Sensitivity",
        "",
        "Excluding preprints or grey/commercial sources does not change the verified included counts because both included papers are peer reviewed. Paper- and study-level counts are identical in this small frozen corpus. The 277-item manual queue remains outside calculations.",
        "",
        "## Output traceability",
        "",
        "All displayed table cells and Fig. 4 cells are generated from `data/frozen/`; source IDs and page/figure locators are in the corresponding audit ledgers.",
    ]
    (RESULTS_DIR / "analysis_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    limitation_lines = [
        "# Limitations",
        "",
        "- The search ran every configured Crossref and OpenAlex query family but retained only the first 10 relevance-ranked records per request; all 190 network queries are explicitly marked truncated.",
        f"- {len(manual)} potentially relevant metadata records lacked full-text verification in this run and remain outside the evidence tables.",
        "- No prior review passed full-text verification, so Supplementary Table S1 is header-only and the Review's literature-gap claim remains unsubstantiated by this run.",
        "- The two included studies cannot represent the whole literature; every distribution applies only to the included corpus.",
        "- The field evidence covers one data-centre GPU cluster over bounded events, not whole-facility or sustained market delivery.",
        "- The EV-building evidence is synthetic/modelled and lacks several mobility, comfort, network and digital-overhead checks.",
        "- No active base-station or operational 6G evidence was included; this must not be phrased as global absence or technical impossibility.",
        "- No numeric central estimate is justified under the seven-part comparability gate.",
    ]
    (RESULTS_DIR / "limitations.md").write_text("\n".join(limitation_lines) + "\n", encoding="utf-8")

    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REVIEW_ROOT, text=True).strip()
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REVIEW_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = "unavailable"
        branch = "unavailable"
    package_versions = {}
    for package in ("requests", "yaml", "pandas", "numpy", "matplotlib", "pypdf", "docx", "pytest"):
        try:
            module = __import__(package)
            package_versions[package] = getattr(module, "__version__", "installed-version-not-exposed")
        except ImportError:
            package_versions[package] = "not_installed"
    manifest = {
        "schema_version": "1.0",
        "run_id": SEARCH_RUN_ID,
        "review_mode": config["review_mode"],
        "corpus_claim_mode": config["corpus_claim_mode"],
        "search_date_bounds": config["date_bounds"],
        "branch_at_analysis": branch,
        "commit_at_analysis": git_sha,
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": package_versions,
        "counts": {
            "candidate_records": len(candidates),
            "deduplicated_records": len(candidates) - len(dedup),
            "manual_verification_queue": len(manual),
            "included_papers": included_papers,
            "included_studies": included_studies,
            "included_scenarios": included_scenarios,
            "multi_asset_studies": multi_studies,
            "central_numeric_summaries": len(central_groups),
        },
        "commands": [
            "python run_pipeline.py --config config/search_plan.yml --stage inventory",
            "python run_pipeline.py --config config/search_plan.yml --stage discover",
            "python run_pipeline.py --config config/search_plan.yml --stage validate",
            "python run_pipeline.py --config config/search_plan.yml --stage analyse",
            "python run_pipeline.py --config config/search_plan.yml --stage render",
            "pytest -q",
            "python run_pipeline.py --config config/search_plan.yml --stage all --offline",
        ],
        "status": "PARTIAL",
        "status_reason": "Bounded/truncated discovery and unresolved full-text manual-verification queue materially limit coverage.",
    }
    write_json(RESULTS_DIR / "run_manifest.json", manifest)

    return {
        "candidate_records": len(candidates),
        "included_papers": included_papers,
        "included_studies": included_studies,
        "included_scenarios": included_scenarios,
        "multi_asset_studies": multi_studies,
        "central_numeric_summaries": len(central_groups),
    }
