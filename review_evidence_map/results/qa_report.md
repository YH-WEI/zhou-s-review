# QA report

**Validation result:** PASS with disclosed limitations

Checks: 40 total; 0 failures; 2 warnings.

| Check | Status | Message | Affected records |
|---|---|---|---|
| `schema_papers` | PASS | papers.csv header matches its template | — |
| `schema_studies` | PASS | studies.csv header matches its template | — |
| `schema_scenarios` | PASS | scenarios.csv header matches its template | — |
| `schema_case_assets` | PASS | case_assets.csv header matches its template | — |
| `schema_quantitative_values` | PASS | quantitative_values.csv header matches its template | — |
| `schema_safeguards` | PASS | safeguards.csv header matches its template | — |
| `schema_reviews` | PASS | reviews.csv header matches its template | — |
| `schema_resources` | PASS | resources.csv header matches its template | — |
| `schema_resource_links` | PASS | resource_links.csv header matches its template | — |
| `schema_claim_evidence_ledger` | PASS | claim_evidence_ledger.csv header matches its template | — |
| `unique_papers` | PASS | papers IDs are unique and non-empty | — |
| `unique_studies` | PASS | studies IDs are unique and non-empty | — |
| `unique_scenarios` | PASS | scenarios IDs are unique and non-empty | — |
| `unique_case_assets` | PASS | case_assets IDs are unique and non-empty | — |
| `unique_quantitative_values` | PASS | quantitative_values IDs are unique and non-empty | — |
| `unique_safeguards` | PASS | safeguards IDs are unique and non-empty | — |
| `unique_reviews` | PASS | reviews IDs are unique and non-empty | — |
| `unique_resources` | PASS | resources IDs are unique and non-empty | — |
| `unique_resource_links` | PASS | resource_links IDs are unique and non-empty | — |
| `unique_claim_evidence_ledger` | PASS | claim_evidence_ledger IDs are unique and non-empty | — |
| `no_pending` | PASS | Frozen evidence tables contain no pending status | — |
| `foreign_keys` | PASS | All evidence-table foreign keys resolve | — |
| `doi_unique` | PASS | Included paper DOIs are unique | — |
| `one_main_version` | PASS | Each included work family has exactly one main version | — |
| `controlled_vocabularies` | PASS | Controlled vocabulary values are valid | — |
| `evidence_setting_derived` | PASS | E0-E5 codes derive from validation environment | — |
| `multi_asset_classification` | PASS | Multi-asset status derives from distinct active focal roles and all coordination tests | — |
| `safeguard_links` | PASS | Safeguards reference active assets and every active asset has coverage | — |
| `quantitative_values` | PASS | Quantitative values preserve provenance, baselines, units and reversible conversions | — |
| `six_g_status` | PASS | Prospective IMT-2030/6G is never classified as operational delivery | — |
| `claim_traceability` | PASS | Every claim has a source locator or explicit derived-input lineage | — |
| `screening_complete` | PASS | Every candidate record has one screening disposition | — |
| `exclusion_codes` | PASS | Every excluded record has a controlled exclusion reason | — |
| `manual_review_queue` | PASS | Every low-confidence screen is queued for manual review | — |
| `enabled_query_families` | PASS | All 95 configured query-family instances ran for both Crossref and OpenAlex | — |
| `raw_response_hashes` | PASS | Raw metadata responses match frozen SHA-256 values | — |
| `source_hashes` | PASS | All inventoried source PDF/DOCX hashes are unchanged | — |
| `source_inventory_coverage` | PASS | All 21 pre-existing source PDF/DOCX files are inventoried | — |
| `manual_verification_limit` | WARN | 277 potentially relevant metadata records remain without full-text manual verification; status cannot be DONE. | — |
| `prior_review_limit` | WARN | No prior review passed full-text verification in this bounded run; Supplementary Table S1 remains header-only. | — |

Warnings are coverage/manual-verification limitations, not schema or logic failures. Any FAIL blocks analysis rendering.
