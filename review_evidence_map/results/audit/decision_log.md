# Decision log

## 2026-08-31 — bounded metadata discovery

All enabled Crossref and OpenAlex query families will be executed, but this run freezes only the first 10 records returned by each source/query combination. The configured upper safety bound remains 500. Every request records the provider total, sort order, cap and truncation status. This prevents an illustrative evidence-map run from being misrepresented as an exhaustive systematic review; final status must be `PARTIAL`, and all distribution language must say “within the included corpus”.

## 2026-08-31 — repository source boundary

The immutable source-hash contract covers every pre-existing `.pdf` and `.docx` outside `review_evidence_map/`. Protocol Markdown files and generated pipeline artifacts are version-controlled implementation inputs/outputs, not source documents in this inventory.

## 2026-08-31 — broad multi-asset query placeholder

`three_plus_or_broad_multi_asset` refers to `{multi_asset_terms}` but the supplied YAML does not define that placeholder. It is operationalized as `multi-asset OR cross-sector OR integrated energy management OR virtual power plant`, combined with at least one focal-asset term, one service group and the configured coordination terms. Exact rendered queries are frozen in `data/frozen/search_log.csv`.
