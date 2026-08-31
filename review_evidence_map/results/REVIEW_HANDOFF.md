# Review evidence map handoff

## Delivery status

- Status: **PARTIAL**.
- Branch: `codex/review-evidence-map-results`.
- Exact results-package commit: `0646c31d5e5ab81ef40ea1564abd6d976c698126`.
- Target: pull request to `main`; leave unmerged.
- Run ID: `RUN_20260831_EVIDENCE_MAP_01`.
- Claim scope: every corpus-level statement means **within the included corpus**.

`PARTIAL` is deliberate. The completed subset is internally valid and reproducible, but discovery retained only the first 10 relevance-ranked records per API request, 277 metadata candidates still require legitimate full-text verification, and no prior-review full text was included. These limitations prevent an exhaustive or manuscript-ready evidence claim.

## Environment and commands

The run used Windows 11, Python 3.13.5, and the pinned packages in `requirements.lock`. From `review_evidence_map/`:

```powershell
python -m venv .venv-review
.\.venv-review\Scripts\python.exe -m pip install -r requirements.lock
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage inventory
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage discover
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage validate
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage analyse
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage render
.\.venv-review\Scripts\python.exe -m pytest -q
.\.venv-review\Scripts\python.exe run_pipeline.py --config config/search_plan.yml --stage all --offline
```

The clean offline rebuild ran in a fresh detached Git worktree. It passed all 9 tests and reproduced 29 derived files with zero SHA-256 differences. `results/run_manifest.json` was excluded from the byte comparison only because its branch field changes in a detached worktree; the manually maintained decision log was also excluded. See the [run manifest](run_manifest.json) and [offline rebuild report](audit/offline_rebuild_report.json).

## Corpus flow

| Stage or unit | Count |
|---|---:|
| Candidate records identified | 1,921 |
| Records after exact DOI/title-year deduplication | 581 |
| Title/abstract includes sought for full-text verification | 279 |
| Full texts verified and included | 2 |
| Awaiting legitimate full-text/manual verification | 277 |
| Included papers | 2 |
| Independent studies/projects | 2 |
| Included scenarios | 2 |
| Multi-asset papers / studies / scenarios | 1 / 1 / 1 |
| Included prior reviews | 0 |
| Central numeric summaries | 0 |

Every one of the 1,921 candidates has a controlled screening disposition. Paper, study/project, and scenario units are distinct. The detailed flow is in [corpus flow](tables/corpus_flow.csv) and [corpus counts](tables/corpus_counts.csv).

## Supported claims

The following statements are supportable only with the stated boundaries:

1. Within the included corpus, one Phoenix data-centre field pilot (`P0001`/`ST0001`/`SC0001`) reached E4/L3 evidence maturity. It reports a bounded 25% power reduction for 3 hours and zero service-level-agreement violations across 33 experiments. It contains one active focal asset class (`DC`) and is not multi-asset. The reported 15-minute value is a planned ramp interval, not a measured physical response time.
2. Within the included corpus, one modelled scenario (`P0002`/`ST0002`/`SC0002`) coordinates active electric-vehicle and building roles under a renewable-integration objective. It satisfies the fixed multi-asset definition but is E1/L3 modelled evidence, not a field deployment.
3. No quantitative value passed both the seven-part comparability gate and the minimum group size of five, so no pooled estimate or central numeric summary is reported.

Source locations and short supporting excerpts are recorded in the [strong-claim ledger](audit/strong_claim_sources.csv), [E4/E5 audit](audit/all_E4_E5_records.csv), [multi-asset audit](audit/all_multiasset_records.csv), and frozen [claim-evidence ledger](../data/frozen/claim_evidence_ledger.csv).

## Conditional claims

- Figure 4 describes only the observed mechanism-service cells in the two included scenarios. Empty cells mean “not observed in this included corpus,” not impossibility or global absence.
- The Beijing life-cycle carbon values in `P0002` are source-specific contextual results with their original system boundary and comparator. They are not pooled, averaged, or generalized.
- No included scenario was classified as operational 6G. This is an included-corpus observation, not evidence that operational 6G applications do not exist.
- The single qualifying multi-asset study establishes presence in the included corpus, not prevalence, superiority, synergy, or scalability.

## Prohibited claims

Do not use this package to claim that:

- multi-asset coordination creates synergy or that adding assets improves outcomes;
- the evidence base is globally sparse, representative, exhaustive, or prevalence-estimating;
- the reported pilots are commercially scalable or deployment-ready;
- 6G is operationally demonstrated or absent from the wider literature;
- heterogeneous percentages, carbon values, durations, ramp intervals, latencies, or response times can be averaged together;
- this work is a meta-analysis, a new simulation/optimization study, or an AI-controller evaluation.

## Source gaps and inaccessible evidence

- All 95 enabled query instances were executed against both Crossref and OpenAlex: 190 API requests, plus repository seeding and manual-import logging. Each API request retained at most 10 relevance-ranked results and records its cap/truncation and raw-response SHA-256.
- The 277 records in [needs manual review](../data/frozen/needs_manual_review.csv) were excluded with `X10`; metadata or abstracts were never treated as full-text evidence.
- Optional Unpaywall retrieval was skipped because no contact-email environment value was provided. No manual database export was supplied.
- The repository's pre-existing PDF/DOCX files were inventoried and hash-checked unchanged. Only legitimately supplied primary full texts were eligible for evidence coding; review exemplars and drafting aids were not converted into primary evidence.
- No prior-review full text met the included-evidence boundary, so [Supplementary Table S1](tables/supp_table_s1_prior_reviews.csv) is header-only and review-to-review synthesis is unavailable.

## Seven-part comparability outcome

The comparability audit separately checked metric definition, numerator, denominator, unit/scale, time horizon, system boundary, and comparator/baseline.

- `M1` (25% data-centre power reduction) and `M2` (3-hour duration) passed all seven fields as source-specific singleton values, but each failed the minimum group size (`n >= 5`) for a central summary.
- `M3` was rejected because the 15-minute planned ramp interval does not establish full-response time.
- `M4` was rejected from pooling because its zero-violation result has a unique denominator of 33 experiments.
- `M5` was rejected from pooling because the life-cycle carbon result depends on a study-specific boundary and baseline.

The complete decisions are in [comparability audit](tables/comparability_audit.csv), [comparable summaries](tables/comparable_numeric_summaries.csv), and [all aggregated values](audit/all_aggregated_values.csv). The latter is header-only because no aggregate was permitted.

## Result entry points

- Narrative: [analysis summary](analysis_summary.md), [QA report](qa_report.md), and [limitations](limitations.md).
- Main tables: [Table 1](tables/table1_asset_comparison_draft.csv), [Table 2](tables/table2_multi_asset_evidence_draft.csv), [evidence by asset/service](tables/evidence_by_asset_service.csv), and [reporting completeness](tables/reporting_completeness.csv).
- Figure: [Figure 4 PNG](figures/fig4_mechanism_service_matrix.png), [SVG](figures/fig4_mechanism_service_matrix.svg), [source data](tables/fig4_mechanism_service_matrix.csv), and [caption](figures/fig4_caption.md).
- Provenance and QA: [source inventory](../data/source_inventory.csv), [search log](../data/frozen/search_log.csv), [validation results](audit/validation_results.json), and [decision log](audit/decision_log.md).
- Sensitivity and reviewer package: [sensitivity analysis](tables/sensitivity_counts.csv), [6G status audit](audit/all_6g_status_records.csv), and [stratified review sample](audit/stratified_review_sample.csv).

## Independent review gate

This package is not manuscript-ready until an independent reviewer completes the ten audits required by `04_CODEX_EXECUTION.md`: scope; corpus/query balance; multi-asset definition; duplicate project/dataset; provenance/source location; clean recalculation; seven-part comparability; visual semantics; wording/6G status; and sensitivity/limitations.

The reviewer must manually inspect 100% of multi-asset, field/operational, 6G-deployment, aggregated-value, and strong-claim records, plus the prescribed stratified 20% remainder sample. Here the remainder sample is empty because both included scenarios already fall into mandatory-review categories. Any fabricated or misattributed source, or a material sampled error rate above 5%, fails the package and triggers full re-audit.

The exact results-package commit is listed above. The PR head SHA after this handoff file is committed is the canonical final delivery SHA and must be recorded in the PR body.
