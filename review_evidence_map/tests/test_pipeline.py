from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from src.common import FROZEN_DIR, RESULTS_DIR, REVIEW_ROOT, load_yaml, read_csv
from src.discover import generate_queries
from src.inventory import verify_source_inventory
from src.validate import validate_frozen_data


def test_all_query_family_instances_are_generated() -> None:
    config = load_yaml(REVIEW_ROOT / "config" / "search_plan.yml")
    queries = generate_queries(config)
    assert len(queries) == 95
    assert len({query.query_id for query in queries}) == 95


def test_every_candidate_has_exactly_one_screening_disposition() -> None:
    candidates = read_csv(FROZEN_DIR / "candidate_records.csv")
    screening = read_csv(FROZEN_DIR / "screening_log.csv")
    assert len(candidates) == len(screening)
    assert len({row["search_record_id"] for row in screening}) == len(screening)
    assert all(row["fulltext_decision"] in {"include", "exclude"} for row in screening)
    assert all(row["exclusion_code"] for row in screening if row["fulltext_decision"] == "exclude")


def test_source_inventory_hashes_are_unchanged() -> None:
    inventory = read_csv(REVIEW_ROOT / "data" / "source_inventory.csv")
    assert len(inventory) == 21
    assert verify_source_inventory(inventory) == []


def test_full_frozen_validation_has_no_material_failure() -> None:
    failures = [check for check in validate_frozen_data() if check.status == "FAIL"]
    assert failures == []


def test_multi_asset_is_derived_only_from_active_focal_roles() -> None:
    scenarios = {row["scenario_id"]: row for row in read_csv(FROZEN_DIR / "scenarios.csv")}
    active: dict[str, set[str]] = defaultdict(set)
    for row in read_csv(FROZEN_DIR / "case_assets.csv"):
        if row["asset_role"] == "active_energy_asset" and row["active_flexibility_asset"] == "yes":
            active[row["scenario_id"]].add(row["asset_class"])
    for scenario_id, scenario in scenarios.items():
        expected = len(active[scenario_id]) >= 2 and all(
            scenario[field] == "yes"
            for field in (
                "coordination_active_decision_variables",
                "coordination_common_service_or_constraint",
                "coordination_joint_control_dispatch_or_clearing",
            )
        )
        assert (scenario["multi_asset"] == "yes") is expected


def test_required_outputs_exist_and_fig4_cells_trace() -> None:
    required = [
        "tables/corpus_flow.csv",
        "tables/corpus_counts.csv",
        "tables/evidence_by_asset_service.csv",
        "tables/evidence_maturity_counts.csv",
        "tables/evidence_by_year_region.csv",
        "tables/fig4_mechanism_service_matrix.csv",
        "tables/asset_service_timescale_map.csv",
        "tables/reporting_completeness.csv",
        "tables/comparability_audit.csv",
        "tables/comparable_numeric_summaries.csv",
        "tables/table1_asset_comparison_draft.csv",
        "tables/table2_multi_asset_evidence_draft.csv",
        "tables/supp_table_s1_prior_reviews.csv",
        "tables/supp_table_s2_included_studies.csv",
        "tables/sensitivity_counts.csv",
        "figures/fig4_mechanism_service_matrix.png",
        "figures/fig4_mechanism_service_matrix.svg",
        "audit/fig4_source_ledger.csv",
        "audit/all_multiasset_records.csv",
        "audit/all_E4_E5_records.csv",
        "audit/all_6g_status_records.csv",
        "audit/all_aggregated_values.csv",
        "audit/strong_claim_sources.csv",
        "audit/stratified_review_sample.csv",
        "analysis_summary.md",
        "qa_report.md",
        "limitations.md",
        "run_manifest.json",
    ]
    assert [path for path in required if not (RESULTS_DIR / path).exists()] == []
    matrix = read_csv(RESULTS_DIR / "tables" / "fig4_mechanism_service_matrix.csv")
    ledger = read_csv(RESULTS_DIR / "audit" / "fig4_source_ledger.csv")
    ledger_keys = {(row["mechanism_id"], row["service_family"]) for row in ledger}
    assert all((row["mechanism_id"], row["service_family"]) in ledger_keys for row in matrix if row["evidence_code"])


def test_no_unsupported_central_numeric_summary() -> None:
    rows = read_csv(RESULTS_DIR / "tables" / "comparable_numeric_summaries.csv")
    for row in rows:
        if int(row["independent_study_n"]) < 5:
            assert row["summary_status"] == "individual_values_and_contextual_range_only"
            assert row["median"] == ""
            assert row["q1"] == ""
            assert row["q3"] == ""


def test_zero_is_not_used_as_missingness() -> None:
    metrics = read_csv(FROZEN_DIR / "quantitative_values.csv")
    zero_rows = [row for row in metrics if row["point_value"] == "0"]
    assert zero_rows
    assert all(row["value_status"] == "source_reported" for row in zero_rows)


def test_all_claim_excerpts_respect_word_limit() -> None:
    for row in read_csv(FROZEN_DIR / "claim_evidence_ledger.csv"):
        excerpt = row["paraphrase_or_short_excerpt_le_25_words"]
        assert len(excerpt.split()) <= 25
