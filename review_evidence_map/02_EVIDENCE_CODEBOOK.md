# Evidence codebook and relational data contract

## 1. Unit of analysis

Do not place the whole evidence base in one flat spreadsheet. Use separate entities:

| Entity | One row means | Main purpose |
|---|---|---|
| `screening` | one database/search record | retrieval, deduplication and inclusion/exclusion audit |
| `papers` | one publication/report/version | bibliographic provenance and paper counts |
| `studies` | one underlying study, dataset, experiment, project or deployment | independent evidence counts and duplicate control |
| `scenarios` | one fixed asset combination, service objective, system boundary, controller and baseline evaluated within a study | evidence setting, claim level and service mapping |
| `case_assets` | one focal asset class/role in one scenario | active energy roles versus compute/communication enablers |
| `quantitative_values` | one reported or transparently derived metric from one scenario | response/duration/outcome and comparability analysis |
| `safeguards` | one scenario × active asset × primary-service constraint type assessment | primary-service protection coverage |
| `reviews` | one included prior review | Supplementary Table S1 and gap substantiation |
| `resources` | one unique dataset, codebase, standard, official rule or other external resource | explicit answer to where inputs/definitions came from |
| `resource_links` | one use of a resource by a paper, study, scenario or metric | separate resource identity from its analytical role |
| `claim_evidence_ledger` | one proposed manuscript/output claim linked to evidence | end-to-end traceability |

`paper_id`, `study_id` and `scenario_id` are not interchangeable. Several paper versions may share one `work_family_id`; several papers may describe the same study/project; several scenarios may be reported within one study.

Headline evidence counts default to unique `study_id`, with paper and scenario counts shown alongside. Numeric aggregation uses independent studies/project families, never outcome-row count.

## 2. Global encoding rules

- UTF-8 CSV, comma delimiter, one header row, Unix newlines.
- IDs are stable ASCII strings such as `P0001`, `ST0001`, `SC0001`, `M0001`.
- Dates use ISO 8601; timestamps use UTC with `Z`.
- Decimal separator is `.`; no thousands separators.
- Multi-value fields use `|`, sorted and deduplicated. Commas are not a list separator.
- DOI is lowercase without `https://doi.org/`, `http://dx.doi.org/` or `doi:`.
- Preserve raw terms/values/units and store normalized versions in separate fields.
- `0` is a real observed value and can never represent missingness.
- Final frozen files may not contain `pending`.
- Every `other` enum requires a non-empty companion `*_other_text`.
- Every quantitative/strong qualitative record needs a source locator and short evidence note.

### Missingness/status vocabulary

Use a companion status for every nullable evidence value:

- `source_reported`;
- `reviewer_derived`;
- `figure_digitized` (normally excluded unless explicitly approved and uncertainty recorded);
- `not_reported` — the source is silent;
- `not_applicable` — logically irrelevant;
- `unclear` — mentioned but not reliably classifiable;
- `fulltext_unavailable` — source could not be checked.

“Explicitly not considered” is a substantive `no/not_considered`, not `not_reported`. Unknown booleans use `unknown`, not `false`.

## 3. Controlled vocabularies

### Focal asset class

`DC`, `BS`, `EV`, `BLDG`.

Multiple EVs or multiple buildings remain one focal asset class. Renewable generation, stationary storage, grid, aggregator and market are contextual resources unless they belong to a focal asset and must not increment focal asset count by themselves.

### Asset role

- `active_energy_asset` — its power/energy/thermal flexibility is a decision variable or controlled response;
- `compute_enabler` — performs forecasting/optimization/coordination but its own energy is not dispatched;
- `communication_enabler` — carries information but its own load/storage is not dispatched;
- `passive_context` — present but not actively controlled for the service;
- `aggregator_or_market_interface` — actor/interface, not a focal energy asset.

One asset may have several roles, but `active_asset_class_count` counts distinct focal classes with `active_energy_asset` only.

### Grid-service family

- `frequency_response_regulation`;
- `demand_response_peak_management`;
- `renewable_energy_integration`;
- `local_energy_sharing_distribution_support`;
- `resilience_emergency_operation`;
- `other`.

Also store `service_type` separately:

- `market_product` — named procured product;
- `technical_grid_service` — frequency, voltage, congestion, reserve, etc.;
- `operational_objective` — peak reduction, curtailment reduction, energy matching, etc.;
- `resilience_function` — backup, islanding, critical-load restoration.

Do not place “renewable utilization increased” and a formal frequency-regulation product at the same semantic level.

### Coordination architecture

- `centralized` — one decision maker receives relevant global inputs and dispatches assets;
- `hierarchical` — supervisory and local layers with explicit decomposition;
- `distributed` — peer/local agents coordinate without one global dispatch authority;
- `market_or_aggregator` — bids/prices/clearing or aggregator dispatch is the principal coupling mechanism;
- `hybrid` — material combination of the above plus defined local fallback;
- `local_only` — one local controller, no cross-site hierarchy;
- `unclear`.

### Coordination test

True multi-asset coordination requires all three:

1. at least two distinct focal asset classes are active decision variables/responders;
2. they share a grid-service objective or a physically/economically coupled constraint;
3. joint control, optimization, dispatch, negotiation or market clearing couples their decisions.

`multi_asset` and `active_asset_class_count` must be script-derived from `case_assets` plus these flags.

### Validation environment and derived evidence setting

Record the environment first; derive the Review code by rule:

| Validation environment | Derived code |
|---|---|
| `concept_only` | `E0` |
| `synthetic_simulation` | `E1` |
| `measured_data_replay_or_calibrated_model` | `E2` |
| `laboratory` or `hardware_in_the_loop` | `E3` |
| `controlled_field_pilot` | `E4` |
| `sustained_operational_delivery` or `real_market_operation` | `E5` |

Measured inputs do not turn an offline simulation into field validation. `E0`–`E5` is a setting descriptor, not a quality score.

### Highest supported claim level

- `L1_nominal_resource`;
- `L2_available_flexibility`;
- `L3_delivered_service`;
- `L4_net_system_outcome`;
- `L5_deployable_value`.

This is independent of evidence setting. A simulation may report a system outcome (`L4/E1`) without proving deployment.

### Publication/source layer

`peer_reviewed_primary`, `peer_reviewed_review`, `conference`, `preprint`, `official_standard`, `official_agency_or_market`, `institutional_project_report`, `commercial_self_report`, `other`.

### Communication generation/status

`legacy_4g_or_earlier`, `current_5g`, `5g_advanced`, `b5g_research`, `future_imt2030_6g`, `mixed`, `not_applicable`, `unclear`.

Only current operational systems can be coded deployed. A 6G vision, candidate technology, lab testbed or roadmap remains `future_imt2030_6g`.

### Screening exclusion codes

- `X01_not_focal_asset`;
- `X02_internal_efficiency_only`;
- `X03_no_grid_signal_or_service`;
- `X04_digital_only_no_energy_decision`;
- `X05_assets_copresent_not_coordinated`;
- `X06_no_extractable_boundary_or_method`;
- `X07_duplicate_version`;
- `X08_duplicate_project_no_new_evidence`;
- `X09_retracted_or_superseded`;
- `X10_fulltext_unavailable_for_required_verification`;
- `X11_non_original_or_unverifiable_claim`;
- `X12_outside_date_or_language_rule`;
- `X13_unrelated_review_or_style_exemplar`;
- `X14_other`.

## 4. Table contracts

### `screening.csv`

Required fields are defined by `templates/screening_template.csv`.

- `search_record_id` is unique before deduplication.
- One primary exclusion code is required for every excluded record.
- `screen_confidence=low` requires manual review.
- `fulltext_unavailable` is different from “source did not report a field”.

### `papers.csv`

- `paper_id` is one publication/report version.
- `work_family_id` links preprint, conference, journal version and correction.
- Only one `included_main_version=yes` per work family may enter the main paper-level count.
- `study_id` links the paper to the main underlying study; many-to-many cases must be handled through scenarios rather than copying paper rows.
- Reviews and official context remain separate `corpus_layer` values.

### `studies.csv`

- `study_id` represents an underlying research/experimental/deployment evidence base.
- `project_family_id` links several closely related studies/campaigns where independence is uncertain.
- `independence_status` is `independent`, `shared_dataset`, `shared_project`, `extension`, or `unclear`.
- Headline counts must disclose the study/project-family sensitivity.

### `scenarios.csv`

A scenario fixes asset combination, service, system boundary, control arrangement, data/validation setting and baseline. Do not split a scenario merely because several metrics are reported.

Key fields:

- three coordination-test flags;
- service family/type/raw name;
- system/electrical/geographic scale;
- validation environment and derived `E` code;
- highest supported `L` code;
- comparison design and matched coordination counterfactual;
- raw technology generation/status;
- provenance and verification.

### `case_assets.csv`

One row is scenario × focal asset class × role. Every active focal asset requires at least one row with `asset_role=active_energy_asset` and a stated flexibility resource. DC/BS enabler-only rows do not count toward multi-asset status.

### `quantitative_values.csv`

One row is one metric/result. Time variables use distinct `metric_code` values:

- `activation_latency_s`;
- `full_response_time_s`;
- `sustain_duration_s`;
- `control_interval_s`;
- `planning_horizon_s`;
- `communication_latency_s`;
- `controller_runtime_s`;
- `sampling_interval_s`;
- `market_interval_s`.

Other metrics must preserve an explicit definition. A generic `percent_improvement` code is forbidden.

Every comparative metric needs a baseline class/description, denominator, system boundary, time aggregation and effect direction. `comparability_signature` is script-derived from:

> service subtype + metric definition + normalized unit/denominator + horizon + system boundary + baseline class + validation setting.

`eligible_for_synthesis=yes` is allowed only when all required fields are source-verified and the seven-part gate passes.

### `safeguards.csv`

One row is scenario × active asset × constraint type. Treatment vocabulary:

- `hard_constraint`;
- `soft_penalty`;
- `ex_post_check`;
- `scenario_assumption`;
- `discussion_only`;
- `not_considered`;
- `not_reported`;
- `not_applicable`;
- `unclear`.

Constraint types include DC SLA/deadline/availability/thermal safety; BS coverage/throughput/latency/reliability/backup reserve; EV departure SOC/mobility/opt-out/degradation; building comfort/IAQ/safety/critical load. Every active asset needs coverage rows sufficient to distinguish unreported, not considered and not applicable.

### `reviews.csv`

Use only for prior-review coverage and source discovery. Performance numbers normally trace to primary studies or authoritative documents, not this table.

### `resources.csv` and `resource_links.csv`

Store a resource once, then link it to the paper/scenario/metric that uses it. Resource types include `public_dataset`, `proprietary_dataset`, `paper_supplement`, `code_repository`, `tariff_or_market_rule`, `weather_data`, `grid_data`, `carbon_factor`, `standard`, `synthetic_data_definition`, and `other`.

Record provider, stable URL/DOI, version/commit, license, access status/date, measured/simulated/synthetic nature, resolution and checksum when a local lawful copy exists. `resource_links.usage_role` is one or more of `evidence_source`, `metric_recalculation`, `normalization`, `validation`, `service_definition`, or `context_only`.

API keys, contact emails, cookies and institutional credentials are never resources and must not appear in frozen files or request URLs.

### `claim_evidence_ledger.csv`

Every prominent output/claim maps to source rows. `basis` is one of `reported`, `reviewer_derived`, `figure_digitized`, `reviewer_inferred`. Derived claims name the script and input record IDs. Search snippets cannot populate the ledger.

Any verbatim locator excerpt is for internal verification only and is capped at 25 English words per source; prefer a faithful paraphrase.

## 5. Numeric and time validation

- `lower_value <= point_value <= upper_value` whenever all exist.
- Time and capacity values are non-negative.
- Unit conversion must be reversible and logged by `transform_rule_id`.
- A qualitative phrase such as “seconds-level” may populate raw text and a qualitative bin, but not an invented number.
- A range crossing bins is marked `spans_bins`; never force its midpoint into one bin.
- “Day-ahead” is a planning horizon, not response time.
- “Up to” is an upper bound, not a central estimate.
- A value digitized from a figure requires method/error metadata and is excluded from aggregation unless explicitly approved.

## 6. Primary validation invariants

The pipeline must fail validation when:

- an ID is duplicated or a foreign key is missing;
- one work family has multiple main versions;
- a scenario-level field conflicts across linked rows;
- an active asset referenced by safeguards is absent from `case_assets`;
- `multi_asset=yes` but fewer than two distinct active focal classes exist;
- coordination is true without all three coordination-test conditions;
- an enabler-only DC/BS is counted as an active energy asset;
- a comparative metric has no baseline/denominator/system boundary;
- an unknown/unreported value is encoded as zero or false;
- `eligible_for_synthesis=yes` but the comparability signature is missing or mismatched;
- a quantitative value has no original source locator;
- a 6G proposal/testbed is labelled operational deployment;
- a plot/table source row cannot resolve to paper, study and scenario provenance.
