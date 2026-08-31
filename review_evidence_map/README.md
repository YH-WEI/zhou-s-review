# Review evidence map: Codex execution contract

## Objective

Build a transparent, reproducible **literature evidence map with descriptive synthesis** for the Review titled:

> **Energy–digital coordination of data centres, next-generation base stations, electric vehicles and smart buildings for multi-asset grid services**

The work must answer four practical questions:

1. What evidence was searched, screened and included?
2. Which asset mechanisms have been proposed, modelled, tested or operated for which grid services?
3. What do the included studies actually report about response, duration, delivery, primary-service safeguards and deployment conditions?
4. Which results are comparable enough for a descriptive numeric summary, and which must remain contextual?

This package does **not** authorize a new power-system model, joint scheduling optimization, AI controller, causal study, meta-analysis or proof of “synergy”.

## Read order

Codex must read all of the following before writing code:

1. `../energy_digital_coordination_review_detailed_framework.md`
2. `00_SCOPE_AND_NONCLAIMS.md`
3. `01_SOURCES_AND_SEARCH.md`
4. `02_EVIDENCE_CODEBOOK.md`
5. `03_ANALYSIS_SPEC.md`
6. `04_CODEX_EXECUTION.md`
7. `config/search_plan.yml`

If instructions conflict, the scope/non-claims file and the fixed framework take priority.

## Required implementation tree

Codex should create the missing implementation and output files under this directory:

```text
review_evidence_map/
├── config/
│   └── search_plan.yml
├── templates/
│   ├── screening_template.csv
│   ├── papers_template.csv
│   ├── studies_template.csv
│   ├── scenarios_template.csv
│   ├── case_assets_template.csv
│   ├── quantitative_values_template.csv
│   ├── safeguards_template.csv
│   ├── reviews_template.csv
│   ├── resources_template.csv
│   ├── resource_links_template.csv
│   └── claim_evidence_ledger_template.csv
├── src/
│   ├── discover.py
│   ├── normalise.py
│   ├── validate.py
│   ├── analyse.py
│   └── render.py
├── tests/
├── data/
│   ├── raw_metadata/
│   ├── interim/
│   └── frozen/
├── results/
│   ├── tables/
│   ├── figures/
│   └── audit/
├── requirements.txt
└── run_pipeline.py
```

Names may be refined only if the same responsibilities and outputs remain obvious.

## Required run contract

The completed pipeline must support a documented command equivalent to:

```bash
python run_pipeline.py --config config/search_plan.yml
```

It must be safe to rerun, cache network responses, preserve raw retrieval logs, validate every frozen row, and deterministically regenerate all computed tables and figures from the frozen CSV files.

## Mandatory outputs

At minimum, the result branch must contain:

- exact search and retrieval log;
- deduplication and screening log with exclusion reasons;
- frozen paper/study/scenario evidence tables;
- frozen prior-review coverage table;
- claim-to-source provenance ledger;
- corpus-flow counts;
- within-corpus descriptive count tables;
- evidence maturity and reporting-completeness tables;
- comparability-group audit;
- drafts of Table 1, Table 2, Supplementary Tables S1–S2;
- the data-backed draft of Fig. 4 and, if justified, Supplementary Fig. S1;
- a run manifest, QA report and concise analysis summary;
- tests and instructions that reproduce the outputs.

The expected filenames are listed in `04_CODEX_EXECUTION.md`.

## Handoff rule

Codex must work on a new branch named `codex/review-evidence-map-results` (or a timestamped variant if it already exists), commit the implementation and results, and open a pull request to `main`. Do not merge the pull request. The PR body must state:

- what was completed;
- exact command used;
- corpus counts at each stage;
- unresolved manual checks or inaccessible sources;
- which manuscript-level claims are supported, conditional or prohibited;
- whether any aggregate passed the comparability gate.

The final ChatGPT review will inspect the PR, rerun the calculations and verify cited source locations before any result is used in the manuscript.
