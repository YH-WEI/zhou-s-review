# Codex execution, validation and handoff

## 1. Git and preservation rules

1. Start from current `main` and create `codex/review-evidence-map-results` (use a timestamped suffix if it already exists).
2. Do not modify, move, rename or recompress any pre-existing Word/PDF source.
3. Keep temporary full text, API keys, credentials, virtual environments and caches out of Git.
4. Commit only lawful metadata, structured evidence, short supporting excerpts, code, tests, tables, figures and audit files.
5. Do not merge the final pull request.

Before analysis, generate `data/source_inventory.csv` for every pre-existing file with path, extension, byte size, SHA-256, role, extraction status and notes. Verify the source hashes again before handoff.

## 2. Implementation phases

### Phase 0 — freeze the protocol

- Read all required files listed in `README.md`.
- Copy the fixed enums and definitions into machine-readable validation rules without changing their meaning.
- Record any unavoidable ambiguity in `results/audit/decision_log.md`; do not silently invent a rule.
- Create a run identifier and freeze the search end date at `2026-08-31`.

### Phase 1 — scaffold and environment

- Implement the `src/`, `tests/`, `data/` and `results/` tree.
- Use Python 3.11 or later.
- Complete `requirements.txt` and create a pinned `requirements.lock` (or an equivalently reproducible lock file).
- Provide `run_pipeline.py` and an optional Makefile wrapper.
- Add clear `--help`, stage selection and a no-network rebuild mode that regenerates analyses from frozen CSV inputs.

### Phase 2 — inventory and discovery

- Inventory and hash 100% of repository source files.
- Extract bibliographic seeds/references from repository documents where technically possible; log failures rather than guessing.
- Execute source-specific versions of every enabled query family in `config/search_plan.yml`.
- Save raw metadata responses, request logs and hashes.
- Ingest any manual RIS/BibTeX/CSV exports found under `data/manual_imports/` and record their provenance.
- Query DOI/OA/version metadata without bypassing paywalls or access controls.

### Phase 3 — normalize and screen

- Normalize DOIs, titles, dates, source types and stable URLs.
- Deduplicate conservatively and preserve a merge log.
- Populate one screening disposition for every candidate with a controlled exclusion code.
- Separate prior reviews from primary evidence.
- Freeze the included-paper table only after DOI/version/retraction checks.
- Identify repeated papers from the same project/dataset/deployment using `study_id`; retain paper links but do not count them as independent studies.

Automated/LLM screening may prefill decisions, but every low-confidence, multi-asset, field/operational, 6G-related or quantitatively aggregated record must be queued for explicit source verification.

### Phase 4 — extract and code evidence

- Populate the codebook at paper, study and scenario levels.
- Separate active energy assets from computing/communication enablers.
- Apply the true multi-asset rule.
- Record evidence setting `E0`–`E5`, claim level `L1`–`L5` and publication status separately.
- Preserve original terminology, raw values and units before normalization.
- Give every coded claim/value a page/section/table/figure locator and concise evidence note.
- Keep activation latency, full-response time, duration, scheduling horizon, communication latency and controller runtime separate.
- Leave missing numeric cells blank and set the required companion status (`not_reported`, `not_applicable`, `unclear` or `fulltext_unavailable`); use explicit tri-state values for categorical fields. Never infer values from generic adjectives or low-resolution plots.

### Phase 5 — validate before calculating

Run schema and logic checks. At minimum:

- IDs are unique and references resolve;
- enums are valid;
- DOI duplicates are reconciled;
- `asset_count` equals active focal-asset flags;
- `multi_asset=true` requires at least two active focal classes and joint coordination;
- data-centre/BS enabler-only roles do not increment active asset count;
- field and operational classifications meet their definitions;
- 6G proposals/testbeds are not coded as deployed 6G;
- every numeric record has unit, definition, source locator and missingness state;
- normalized-unit conversion is reversible and logged;
- joins do not unintentionally multiply rows;
- every plotted/table value traces to frozen input rows.

Write machine-readable validation results and a readable QA report. Do not continue to final rendering with material validation errors.

### Phase 6 — calculate and render

Implement every mandatory item in `03_ANALYSIS_SPEC.md` and no prohibited analysis. Generate source-data CSVs before figures. Figures must be editable SVG plus at least 300 dpi PNG, accessible in colour and greyscale, and free of 3D effects or misleading performance gradients.

No aggregate may be rendered unless the seven-part comparability gate passes. A header-only comparable-summary file plus a clear “insufficient comparability” report is a valid result.

### Phase 7 — sensitivity and source verification package

Generate:

- all multi-asset records;
- all `E4`/`E5` records;
- all 6G-status records;
- all values used in any aggregate;
- all sources supporting strong Fig. 4 cells or draft synthesis claims;
- a fixed-seed stratified sample of at least 20% of the remaining records, covering all assets and evidence settings.

Recalculate headline counts with/without preprints, grey/commercial literature, low-confidence records and at paper versus unique-study level.

### Phase 8 — clean rebuild

- From committed frozen inputs, delete only reproducible derived outputs in a safe task-specific path.
- Run the full pipeline in no-network mode.
- Run all tests.
- Compare regenerated file hashes or document nondeterministic metadata fields explicitly.
- Confirm original source hashes are unchanged.

### Phase 9 — handoff and PR

Create `results/REVIEW_HANDOFF.md`, commit all required files, push the branch and open a PR to `main` without merging.

## 3. Required command contract

Document commands equivalent to:

```bash
python -m venv .venv-review
. .venv-review/bin/activate
python -m pip install -r requirements.txt

python run_pipeline.py --config config/search_plan.yml --stage inventory
python run_pipeline.py --config config/search_plan.yml --stage discover
python run_pipeline.py --config config/search_plan.yml --stage validate
python run_pipeline.py --config config/search_plan.yml --stage analyse
python run_pipeline.py --config config/search_plan.yml --stage render
pytest -q
python run_pipeline.py --config config/search_plan.yml --stage all --offline
```

If a Makefile is supplied, `make all`, `make test` and `make offline-rebuild` should wrap the same operations. Commands must run from `review_evidence_map/` and must never delete outside that directory.

## 4. Required output paths

### Frozen data and provenance

```text
data/source_inventory.csv
data/frozen/search_log.csv
data/frozen/candidate_records.csv
data/frozen/deduplication_log.csv
data/frozen/screening_log.csv
data/frozen/papers.csv
data/frozen/studies.csv
data/frozen/scenarios.csv
data/frozen/case_assets.csv
data/frozen/safeguards.csv
data/frozen/reviews.csv
data/frozen/quantitative_values.csv
data/frozen/resources.csv
data/frozen/resource_links.csv
data/frozen/claim_evidence_ledger.csv
```

### Tables

```text
results/tables/corpus_flow.csv
results/tables/corpus_counts.csv
results/tables/evidence_by_asset_service.csv
results/tables/evidence_maturity_counts.csv
results/tables/evidence_by_year_region.csv
results/tables/fig4_mechanism_service_matrix.csv
results/tables/asset_service_timescale_map.csv
results/tables/reporting_completeness.csv
results/tables/comparability_audit.csv
results/tables/comparable_numeric_summaries.csv
results/tables/table1_asset_comparison_draft.csv
results/tables/table2_multi_asset_evidence_draft.csv
results/tables/supp_table_s1_prior_reviews.csv
results/tables/supp_table_s2_included_studies.csv
results/tables/sensitivity_counts.csv
```

### Figures and ledgers

```text
results/figures/fig4_mechanism_service_matrix.svg
results/figures/fig4_mechanism_service_matrix.png
results/audit/fig4_source_ledger.csv
results/audit/all_multiasset_records.csv
results/audit/all_E4_E5_records.csv
results/audit/all_6g_status_records.csv
results/audit/all_aggregated_values.csv
results/audit/strong_claim_sources.csv
results/audit/stratified_review_sample.csv
```

Supplementary figures are conditional on sufficient data but their source tables must exist when generated.

### Reports

```text
results/analysis_summary.md
results/qa_report.md
results/limitations.md
results/run_manifest.json
results/audit/decision_log.md
results/REVIEW_HANDOFF.md
```

Every table should have a Markdown preview or be summarized in `analysis_summary.md`. Every figure needs a source-data CSV and caption note stating the count unit and what colour/labels encode.

## 5. Status definitions

- `DONE` — all required sources/protocol phases completed; every frozen row and output passes validation; the offline rebuild and tests pass; no material unresolved source or coding issue remains.
- `PARTIAL` — the completed subset is valid and reproducible, but missing databases/full texts/manual verification materially limit coverage or a conditional result.
- `BLOCKED` — a missing permission, required source or material scope decision prevents a credible frozen corpus or analysis.

Never downgrade requirements or fabricate data to report `DONE`.

## 6. DONE acceptance checklist

Codex may report `DONE` only if all items pass:

- [ ] Existing source Word/PDF files are unchanged and 100% inventoried.
- [ ] Search sources, exact queries, UTC dates, result counts, caps and raw-response hashes are recorded.
- [ ] Every candidate has a screening disposition and every exclusion has a controlled reason.
- [ ] Every included paper has stable provenance and at least one evidence locator.
- [ ] Paper, study/project and scenario units are separated.
- [ ] Every multi-asset classification satisfies the fixed definition.
- [ ] Active energy roles and digital enabler roles are separated.
- [ ] `E0`–`E5`, `L1`–`L5` and publication status remain separate fields.
- [ ] All response/duration/latency concepts remain distinct.
- [ ] Every percentage states its denominator.
- [ ] Every numeric conversion and comparability decision is auditable.
- [ ] No heterogeneous metrics were pooled and no unsupported central estimate was produced.
- [ ] All summary totals reconcile to frozen rows at study and paper levels.
- [ ] All figures/tables regenerate from frozen data with no hard-coded evidence values.
- [ ] Required sensitivity calculations and source-verification packages exist.
- [ ] Tests and clean offline rebuild pass.
- [ ] The PR contains no original joint simulation, optimization, AI controller or unsupported meta-analysis.
- [ ] `REVIEW_HANDOFF.md` and the PR body state status, commit SHA, commands, corpus flow, supported/conditional/prohibited claims, source gaps and comparability outcome.

## 7. Independent review gate for ChatGPT

The result is not manuscript-ready until the later independent review completes:

1. scope audit;
2. corpus/query balance audit;
3. multi-asset definition audit;
4. duplicate project/dataset audit;
5. provenance and source-location audit;
6. clean recalculation audit;
7. seven-part comparability audit;
8. visual semantics audit;
9. wording/6G-status audit;
10. sensitivity and limitations audit.

The later reviewer will manually verify 100% of multi-asset, field/operational, 6G-deployment, aggregated-value and strong-claim records, plus a stratified 20% sample of the remainder. Any fabricated/misattributed source, or a material error rate above 5% in the sample, fails the result and triggers a full re-audit.
