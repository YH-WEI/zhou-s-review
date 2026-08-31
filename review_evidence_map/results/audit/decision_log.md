# Decision log

## 2026-08-31 — bounded metadata discovery

All enabled Crossref and OpenAlex query families will be executed, but this run freezes only the first 10 records returned by each source/query combination. The configured upper safety bound remains 500. Every request records the provider total, sort order, cap and truncation status. This prevents an illustrative evidence-map run from being misrepresented as an exhaustive systematic review; final status must be `PARTIAL`, and all distribution language must say “within the included corpus”.

## 2026-08-31 — repository source boundary

The immutable source-hash contract covers every pre-existing `.pdf` and `.docx` outside `review_evidence_map/`. Protocol Markdown files and generated pipeline artifacts are version-controlled implementation inputs/outputs, not source documents in this inventory.

## 2026-08-31 — broad multi-asset query placeholder

`three_plus_or_broad_multi_asset` refers to `{multi_asset_terms}` but the supplied YAML does not define that placeholder. It is operationalized as `multi-asset OR cross-sector OR integrated energy management OR virtual power plant`, combined with at least one focal-asset term, one service group and the configured coordination terms. Exact rendered queries are frozen in `data/frozen/search_log.csv`.

## 2026-08-31 — clean offline rebuild verification

The execution environment blocked direct deletion commands, so the clean rebuild used a fresh detached Git worktree at implementation commit `c1e1cbd`. The worktree contained committed frozen inputs and no derived outputs. `python run_pipeline.py --config config/search_plan.yml --stage all --offline` and `pytest -q` both passed. Twenty-nine regenerated files had identical SHA-256 hashes to the main-worktree outputs. `run_manifest.json` was excluded only because `branch_at_analysis` is necessarily different in a detached worktree; `decision_log.md` is a manually maintained audit input, not a derived output. The temporary worktree was removed after comparison.
