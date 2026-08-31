# Decision log

## 2026-08-31 — bounded metadata discovery

All enabled Crossref and OpenAlex query families will be executed, but this run freezes only the first 10 records returned by each source/query combination. The configured upper safety bound remains 500. Every request records the provider total, sort order, cap and truncation status. This prevents an illustrative evidence-map run from being misrepresented as an exhaustive systematic review; final status must be `PARTIAL`, and all distribution language must say “within the included corpus”.

## 2026-08-31 — repository source boundary

The immutable source-hash contract covers every pre-existing `.pdf` and `.docx` outside `review_evidence_map/`. Protocol Markdown files and generated pipeline artifacts are version-controlled implementation inputs/outputs, not source documents in this inventory.
