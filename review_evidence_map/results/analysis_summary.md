# Evidence-map analysis summary

## Answer first

This bounded, reproducible run included **2 papers, 2 unique studies and 2 scenarios** after screening. It identified **1 unique multi-asset study** within the included corpus. The result is descriptive evidence mapping, not a systematic review or meta-analysis.

No comparability group reached the required five independent studies; **0 central numeric summaries were produced**. Individual verified values remain contextual.

## Corpus flow preview

| stage | reason | record_count | paper_count | study_count | scenario_count |
|---|---|---|---|---|---|
| identified | all_sources | 1921 | — | — | — |
| identified_by_source_query_family | crossref:field_and_operational_evidence | 200 | — | — | — |
| identified_by_source_query_family | crossref:pairwise_multi_asset | 300 | — | — | — |
| identified_by_source_query_family | crossref:prior_reviews | 200 | — | — | — |
| identified_by_source_query_family | crossref:single_asset_service | 200 | — | — | — |
| identified_by_source_query_family | crossref:three_plus_or_broad_multi_asset | 50 | — | — | — |
| identified_by_source_query_family | openalex:field_and_operational_evidence | 200 | — | — | — |
| identified_by_source_query_family | openalex:pairwise_multi_asset | 300 | — | — | — |
| identified_by_source_query_family | openalex:prior_reviews | 200 | — | — | — |
| identified_by_source_query_family | openalex:single_asset_service | 200 | — | — | — |
| identified_by_source_query_family | openalex:three_plus_or_broad_multi_asset | 50 | — | — | — |
| identified_by_source_query_family | repository:repository_seeds | 21 | — | — | — |
| deduplicated | after_normalized_doi_and_exact_title_year | 581 | — | — | — |
| title_abstract_excluded | X01_not_focal_asset | 132 | — | — | — |

_Preview shows 14 of 27 rows._

## Within-corpus evidence

- The DC record is an `E4` controlled field pilot for peak-demand response; it is not sustained market operation.
- The EV-BLDG record is an `E1` synthetic/modelled renewable-integration scenario; it is not field delivery.
- No included active-energy BS or operational 6G scenario was identified. This is only a statement about the included corpus.
- Primary-service reporting is incomplete: the field trial reports workload SLA outcomes, while the modelled EV-building scenario lacks several mobility/building guardrail outcomes.

## Fig. 4 matrix preview

| asset_class | flexibility_mechanism | service_family | evidence_code | study_count | highest_evidence_setting |
|---|---|---|---|---|---|
| BLDG | building prosumer load and on-site renewable allocation | renewable_energy_integration | M | 1 | E1 |
| DC | AI workload power modulation | demand_response_peak_management | D | 1 | E4 |
| EV | mobile battery through B2V and V2B | renewable_energy_integration | M | 1 | E1 |

`D` means E3-E5 demonstrated evidence, `M` means E1-E2 modelled/replayed evidence, and blank means not identified under this protocol—not impossible.

## Multi-asset Table 2 preview

| service_family | study_and_region | asset_combination | evidence_setting | result | limitation |
|---|---|---|---|---|---|
| renewable_energy_integration | Aoye Song et al. (2024); China/multi-region model | BLDG+EV | E1 | lifecycle battery carbon intensity in Beijing under Scenario C=-134.47 kg CO2,e kWh-1 | Renewable generators and the grid are contextual resources and are not counted as focal asset classes. |

## Comparability conclusion

Insufficient comparability for a central numeric synthesis. Peak-power reduction, duration, SLA outcomes and lifecycle-carbon values differ in metric definition, denominator, boundary, horizon, service and/or validation setting. The two gate-complete singleton values are listed individually; neither is averaged.

## Sensitivity

Excluding preprints or grey/commercial sources does not change the verified included counts because both included papers are peer reviewed. Paper- and study-level counts are identical in this small frozen corpus. The 277-item manual queue remains outside calculations.

## Output traceability

All displayed table cells and Fig. 4 cells are generated from `data/frozen/`; source IDs and page/figure locators are in the corresponding audit ledgers.
