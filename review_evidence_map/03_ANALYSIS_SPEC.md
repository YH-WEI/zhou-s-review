# Permitted calculations and output specification

## 1. Analysis principle

All calculations are **descriptive summaries of the frozen evidence corpus**. They answer where evidence exists, what setting it has, what it reports and whether values are comparable. They do not estimate a universal treatment effect or prove that coordination is beneficial.

Default counting unit is unique `study_id`. Every headline count must also expose the corresponding unique paper and scenario counts so repeated publications/scenarios cannot silently inflate the evidence base.

## 2. Mandatory corpus-flow calculations

Calculate and save counts for:

1. records returned by each source/query family;
2. records after DOI/title deduplication;
3. title/abstract exclusions by reason;
4. full-text sought, obtained and unavailable;
5. full-text exclusions by reason;
6. included prior reviews;
7. included primary papers, unique studies and scenarios;
8. multi-asset papers/studies/scenarios;
9. records requiring manual verification.

Output: `results/tables/corpus_flow.csv` plus a readable section in `results/analysis_summary.md`.

## 3. Mandatory within-corpus evidence map

Compute cross-tabulations, always labelled “within the included corpus”, for:

- asset class and asset combination;
- number of participating focal asset classes (`S1`, `S2`, `S3+`);
- grid service;
- evidence setting `E0`–`E5`;
- claim-ladder level `L1`–`L5`;
- publication/source type;
- year and region/jurisdiction;
- coordination topology (centralized, hierarchical, distributed, hybrid/local fallback);
- primary-service safeguard reporting;
- matched coordination counterfactual availability;
- preprint/grey-literature status.

Do not transform these counts into a composite maturity score. Evidence density is not performance, quality, feasibility or market readiness.

Required outputs:

- `results/tables/corpus_counts.csv`;
- `results/tables/evidence_by_asset_service.csv`;
- `results/tables/evidence_maturity_counts.csv`;
- `results/tables/evidence_by_year_region.csv`.

## 4. Asset–mechanism–service mapping

Build a source-backed mapping at the `study_id` level. Each cell must distinguish:

- `D` — demonstrated in lab/HIL, controlled field pilot or sustained operation (`E3`–`E5`);
- `M` — modelled/simulated/replayed (`E1`–`E2`);
- `I` — inferred or proposed but not directly evaluated (`E0` or explicit inference);
- blank — no eligible evidence identified under this search/scope.

Display `n` and the highest observed setting separately; never imply that the highest setting represents all evidence. `I` must have a visually different encoding from `D`/`M`. A blank means “not identified in this corpus”, not “impossible”.

This mapping supplies the data-backed draft of Review **Fig. 4**. Required files:

- `results/tables/fig4_mechanism_service_matrix.csv`;
- `results/figures/fig4_mechanism_service_matrix.png` (300 dpi or more);
- `results/figures/fig4_mechanism_service_matrix.svg`;
- `results/audit/fig4_source_ledger.csv` listing every populated cell and source row.

## 5. Timescale mapping

Keep these raw variables separate and normalize to seconds only when the source supports conversion:

- activation/command latency;
- time to full physical response;
- sustainable delivery duration;
- scheduling/forecast horizon;
- communication latency;
- controller runtime;
- sampling and market intervals.

Do not infer physical response time from controller time step, communication latency, sampling rate or market interval.

For visualization only, response-time bins may be:

- `<1 s`;
- `1–<60 s`;
- `1–<15 min`;
- `15–<60 min`;
- `1–<4 h`;
- `>=4 h`;
- `not reported`.

Keep raw values and original language in the evidence table. Duration must use a separate field and separate bins. Output:

- `results/tables/asset_service_timescale_map.csv`;
- an internal QA plot only if enough explicit measurements exist.

## 6. Reporting-completeness calculations

For each asset/service/evidence-setting stratum, count the share of included studies that explicitly report:

- baseline/counterfactual;
- asset size and electrical/geographic boundary;
- activation and full-response time;
- sustainable duration/duty cycle;
- rebound/recovery;
- uncertainty or forecast error;
- failure/opt-out/communication-loss scenario;
- primary-service metric and result;
- digital energy/computation/communication overhead;
- battery degradation where relevant;
- grid location/network constraint;
- economic boundary and jurisdiction where economic results are claimed;
- carbon-factor type, resolution and boundary where carbon results are claimed.

The denominator must be stated for every percentage. Missing/unknown is not zero. Output:

- `results/tables/reporting_completeness.csv`;
- optional internal figure `results/figures/reporting_completeness.png`;
- manuscript use only after final review.

## 7. Comparability gate for numeric outcomes

Two values may enter one descriptive group only if all seven attributes match:

1. metric definition;
2. numerator and denominator;
3. baseline/counterfactual;
4. system boundary;
5. temporal horizon;
6. grid service and operating context;
7. validation setting.

Create a deterministic `comparability_group_id` only after these fields are verified. The audit table must state why every candidate was accepted or rejected.

- Fewer than five independent comparable `study_id` values: list individual values and contextual range; do not report a central estimate.
- Five or more genuinely comparable studies: report `n`, median, Q1, Q3, minimum and maximum. Do not default to the mean.
- Never pool peak reduction, shifted energy, total energy saving, renewable utilization, cost, carbon, reliability or comfort.
- Never pool percentages with different denominators.
- No inferential tests, confidence intervals, meta-regression or causal language unless a separate formal meta-analysis protocol and variance data are later approved.

Output:

- `results/tables/comparability_audit.csv`;
- `results/tables/comparable_numeric_summaries.csv` (possibly header-only if nothing passes);
- a statement in `analysis_summary.md` that clearly says when no aggregate is justified.

### Carbon-specific gate

Retain average versus marginal emission factors, operational versus lifecycle boundary, temporal/spatial resolution, location- versus market-based accounting and included embodied components. Do not combine across mismatched choices.

### Economic-specific gate

Retain tariff/market design, currency, currency year, jurisdiction, modeled/measured status, degradation, integration cost, opportunity cost and settlement assumptions. Do not combine across mismatched contexts.

## 8. Table contracts

### Table 1 — cross-asset capability comparison

Generate `results/tables/table1_asset_comparison_draft.csv` with source-backed entries for:

- flexibility mechanism;
- direction (increase/decrease/shift/export);
- reported response and duration evidence;
- spatial availability;
- observability/control needs;
- primary-service guardrails;
- suitable service conditions;
- evidence limits.

Ranges must link to source rows. Do not fill gaps with assumed engineering values.

### Table 2 — representative multi-asset evidence

Generate `results/tables/table2_multi_asset_evidence_draft.csv`, grouped by grid service. Include study/region, true participating asset classes, scale, coordination and communication, evidence setting, data/duration, baseline, metrics, primary-service safeguards, result and limitation.

Selection must be rule based and documented. Prefer complete coverage of all eligible multi-asset studies when feasible. If space requires a representative subset, select transparently by service coverage, distinct study/project, evidence setting and information completeness—not by positive outcome.

### Supplementary tables

- `supp_table_s1_prior_reviews.csv` — coverage matrix of existing reviews.
- `supp_table_s2_included_studies.csv` — all frozen included primary evidence with provenance.

## 9. Optional supplementary evidence distribution

Only when the search is reproducible and the corpus is adequately populated, render Supplementary Fig. S1 showing region, asset combination and evidence-setting distribution. Use counts, not implied performance scores. Save source data and both PNG/SVG.

## 10. Sensitivity calculations

Recalculate headline counts:

1. including versus excluding preprints;
2. including versus excluding grey/commercial literature;
3. at paper versus unique-study level;
4. including versus excluding records awaiting full manual verification.

Save `results/tables/sensitivity_counts.csv`. Differences must be described as corpus sensitivity, not causal robustness.

## 11. No manually inserted plotted values

Every table and figure must be generated from `data/frozen/` by code. Each displayed cell/point must resolve through a ledger to `paper_id`, `study_id`, optional `scenario_id` and page/table/figure location. Plotting scripts must not contain hard-coded evidence counts or performance numbers.

