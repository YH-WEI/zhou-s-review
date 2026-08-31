# Sources, search and provenance protocol

## 1. What counts as a source

Use three source layers and keep their roles separate.

### Layer A — repository seeds

| Repository path | Permitted role | Not permitted |
|---|---|---|
| `../周跃宽的idea.docx` | Formal source of the original idea; seed terminology and cited literature | Treating every statement as verified evidence |
| `../案例论文/s41560-025-01927-1(1).pdf` | Seed primary study; code if it passes inclusion rules | Generalising one case to all data centres or assets |
| `../案例论文/AI数据中心作为电网互动型资产_逐段翻译与深度解读.docx` | Reading aid | Citing the translation instead of the original paper |
| `../Data_centers_6G_中文逐句翻译与通俗解读.docx` | Reading aid and keyword seed | Using it as an original source |
| `../周跃宽本人论文/*.pdf` | Candidate studies and context; each must pass the same rules | Allowing one author corpus to dominate or bypass screening |
| `../nature energy综述例子集合/*.pdf` | Review-style, figure and narrative exemplars | Adding unrelated content to the topical evidence corpus |

Repository presence is not an inclusion criterion.

### Layer B — reproducible discovery and metadata

| Source | Role | Access notes |
|---|---|---|
| [OpenAlex API](https://help.openalex.org/api/) | Broad work discovery, abstracts/keywords where available, citation links, OA locations and identifiers | Current OpenAlex usage is credit based; support `OPENALEX_API_KEY` through an environment variable and never commit it. Cache responses. See [authentication](https://help.openalex.org/api/authentication/) and [search](https://help.openalex.org/api/searching/). |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | DOI validation, publisher metadata, dates, types, licenses and update/retraction relationships | Public JSON API; include a descriptive user agent and contact via environment/config. Use cursor pagination and cache raw responses. |
| [Unpaywall API](https://unpaywall.org/products/api) | DOI-based open-access status and lawful OA locations | Use only to locate OA copies; record host, version and license. Do not treat OA status as study quality. |
| [DataCite API](https://support.datacite.org/docs/api) | Public metadata for datasets, software and other DOI objects not registered through Crossref | Use after checking DOI registration agency; retain version/concept DOI and license. |
| [Semantic Scholar API](https://api.semanticscholar.org/api-docs/) | Optional recall and citation-graph supplement | Not the canonical DOI authority; respect authentication/rate limits and save raw responses. |
| [arXiv API](https://info.arxiv.org/help/api/user-manual.html) | Preprint metadata and version history | Link preprint and journal version; do not double count. Respect documented throttling. |
| [Zenodo API](https://developers.zenodo.org/) | Public project datasets, software and attachments | Record record DOI, concept DOI, version, file license and access date. |
| DOI resolver and publisher landing page | Canonical identity, correction/retraction status, version of record | Do not scrape paywalled full text or bypass access controls. |
| Manual database exports | Coverage supplement from Web of Science, Scopus, IEEE Xplore or institutional subscriptions | Accept RIS/BibTeX/CSV exports placed in `data/manual_imports/`; record database, exact query and export date. Do not automate credentialed scraping. |

OpenAlex and Crossref are discovery/metadata sources, not substitutes for reading the paper. Search snippets are never evidence for a quantitative claim.

Google Scholar has no official public search API and must not be scraped. IEEE Xplore, Scopus and Web of Science APIs/exports may supplement coverage when legitimately available, but credentials or institutional access must never be a hidden reproducibility dependency.

### Layer C — authoritative contextual and deployment sources

Use official sources for definitions, standards, technology status, system background and market rules. Record jurisdiction and version/date. Official reports do not automatically prove asset performance.

| Domain | Recommended official/open sources | Permitted use and limitation |
|---|---|---|
| Data centres | [LBNL US data-centre energy update](https://eta.lbl.gov/publications/united-states-data-center-energy-2025), [LBNL modelling and forecasting](https://datacenters.lbl.gov/modeling-forecasting), [EU data-centre reporting](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficiency-targets-directive-and-rules/energy-efficiency-directive/energy-performance-data-centres_en), [IEA Energy and AI](https://www.iea.org/reports/energy-and-ai) | System background, reporting definitions and scenarios. Modelled national estimates are not site dispatch telemetry. |
| Base stations/networks | [ITU IMT-2030 process](https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/pages/default.aspx), [ITU-R M.2160](https://www.itu.int/rec/R-REC-M.2160-0-202311-I/en), [3GPP releases](https://www.3gpp.org/specifications-technologies/releases), [ETSI ES 203 228](https://www.etsi.org/deliver/etsi_es/203200_203299/203228/01.03.00_50/es_203228v010300m.pdf), [ETSI ES 202 706-1](https://www.etsi.org/deliver/etsi_es/202700_202799/20270601/01.08.00_50/es_20270601v010800m.pdf) | Technology status, terminology and energy-efficiency test methods. These do not supply open station-level load/SOC telemetry. |
| Electric vehicles | [IEA Global EV Data Explorer](https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer), [US AFDC downloads](https://afdc.energy.gov/data_download), [NLR/AFDC API](https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/), [DOE bidirectional charging](https://www.energy.gov/cmei/femp/bidirectional-charging-and-electric-vehicles-mobile-storage), [CEC EPIC projects](https://www.energizeinnovation.fund/projects) | Fleet/charger context, official project and policy evidence. Charger counts cannot be converted into dispatchable capacity; connection, SOC and user availability are generally absent. |
| Buildings | [ResStock datasets](https://resstock.nlr.gov/datasets), [OEDI End-Use Load Profiles](https://data.openei.org/submissions/4520), [EU Building Stock Observatory](https://building-stock-observatory.energy.ec.europa.eu/database/), [DOE GEB projects](https://www.energy.gov/eere/buildings/articles/grid-interactive-efficient-buildings-projects-summary) | Building-stock context, simulation baselines and project discovery. ResStock/OEDI profiles are modelled/validated profiles, not live dispatch evidence. |
| Demonstrations | [EU BRIDGE projects](https://bridge-smart-grid-storage-systems-digital-projects.ec.europa.eu/projects), [CORDIS](https://cordis.europa.eu/projects), [DOE Smart Grid Demonstration reports](https://www.energy.gov/oe/recovery-act-reports-and-other-materials-smart-grid-demonstration-projects-sgdp) | Locate project reports and deployment evidence. Separate funded concept, lab, pilot, prequalified service and independently measured sustained operation. |

There is currently no single authoritative open dataset containing joint operation of all four focal assets, and major gaps remain for site-level data-centre dispatch, base-station load/battery SOC and population-scale EV connection/SOC. Therefore these contextual datasets must not be combined into an invented multi-asset operational simulation.

Standards and protocols may include [OpenADR 3](https://www.openadr.org/openadr-3-0), [OCPP](https://openchargealliance.org/download-ocpp/), [ISO 15118-20](https://www.iso.org/standard/77845.html), [IEEE 1547-2018](https://standards.ieee.org/standard/1547-2018.html), [IEC CIM 61970-301](https://webstore.iec.ch/en/publication/62698) and [BACnet/ASHRAE 135](https://bacnet.org/about-bacnet-standard/). Record whether only metadata or the normative text was actually consulted; do not imply that one standard spans the full four-asset chain.

Grid-service response and duration requirements must come from a named jurisdiction/operator and effective rule version, for example [Fingrid FCR](https://www.fingrid.fi/en/electricity-market/reserves/reserve-products/frequency-containment-reserves-fcr-products/) or [Fingrid FFR](https://www.fingrid.fi/en/electricity-market/reserves/reserve-products/fast-frequency-reserve-ffr/). Never average different market qualification rules into a “global” response threshold.

For 6G, separate current 4G/5G operations, 5G-Advanced/B5G trials and prospective IMT-2030/6G. A roadmap, performance target or testbed is not deployed 6G grid-service evidence.

## 2. Review type and search claim

The intended method is a **transparent structured narrative Review with evidence mapping**. Maintain PRISMA-style identification/screening counts as reproducibility bookkeeping, but do not label the paper a systematic review unless the authors later adopt the full protocol, exhaustive database coverage, dual screening and applicable reporting requirements. The official [PRISMA 2020 flow diagram](https://www.prisma-statement.org/prisma-2020-flow-diagram) may be used only as a reporting aid.

If any query is deliberately capped, any database is unavailable, or full-text screening is incomplete, all distribution statements must say “within the included corpus”. A global scarcity claim is prohibited.

## 3. Time and language bounds

- Main window: `2015-01-01` through `2026-08-31` inclusive.
- Earlier foundational V2G, demand-response, data-centre scheduling and building-flexibility studies may be added through backward citation tracing and must be labelled `foundational_pre_2015`.
- Primary screening language: English. Non-English authoritative standards or field reports may be included when a reliable translation and original stable source are available; record the language.
- Freeze the actual search timestamp in UTC in every run manifest. Never silently move the end date.

## 4. Search axes

The machine-readable terms and query families are in `config/search_plan.yml`.

### Asset axis

- data centre, AI data centre, cloud, high-performance computing, edge data centre;
- base station, radio access network, telecom tower, 4G, 5G, 5G-Advanced, B5G, IMT-2030, prospective 6G;
- electric vehicle, smart charging, V1G, V2G, V2B, V2H, fleet charging;
- smart/active/grid-interactive building, BEMS, HVAC flexibility, building thermal storage.

### Service axis

Frequency response/regulation; demand response and peak management; renewable-energy integration and curtailment reduction; local energy sharing, voltage/congestion and distribution support; resilience, reserve and emergency operation.

### Coordination/digital axis

Coordination, co-optimization, aggregation, integrated energy management, multi-asset, VPP, state/flexibility estimation, forecasting, MPC/distributed control, edge/MEC, communication latency, measurement and verification.

### Evidence axis

Field, pilot, demonstration, experiment, HIL, real-world data, market participation and case study.

Do not search only for all four assets together. Search:

1. each single asset plus grid-service terms;
2. all six pairwise focal-asset combinations plus a common service/coordination term;
3. three-or-more asset and broad multi-asset frameworks;
4. prior reviews for each asset and cross-asset coordination;
5. forward/backward citations from included seed and review papers.

## 5. Mandatory retrieval log

Every request or manual import must append a row containing:

- `search_run_id`;
- source/database;
- exact query as sent;
- full request URL with secrets removed;
- UTC timestamp;
- date bounds, filters and sort order;
- page/cursor;
- returned count and total count if supplied;
- whether results were capped/truncated;
- HTTP status/retry count;
- raw response path and SHA-256;
- software version/commit.

Network requests must use bounded retries with backoff, clear user agent, source-specific rate limits and local caching. A rerun should not redownload unchanged records unnecessarily.

## 6. Deduplication and unit of analysis

Deduplicate in this order:

1. normalized DOI;
2. stable report/standard identifier;
3. exact normalized title plus year;
4. high-similarity title/author/year candidates flagged for manual verification.

Never auto-merge solely on fuzzy title similarity.

Maintain separate identifiers:

- `paper_id` — one publication/report;
- `study_id` — one underlying project, experiment, dataset or deployment campaign;
- `scenario_id` — one separately reported scenario or service result when needed.

Several papers from one project may be retained, but headline evidence counts must normally use unique `study_id`. Report paper-level counts separately. One scenario must not inflate study-level maturity counts.

## 7. Screening rules

### Include a primary study when it:

- evaluates at least one focal asset’s constrained flexibility under an external grid/market signal, or actively coordinates at least two focal assets toward a common grid service;
- provides extractable system boundaries, mechanisms, architecture, metrics or deployment conditions;
- makes it possible to distinguish technical flexibility from actual service delivery;
- has an original full text or authoritative report accessible for verification.

### Include a review when it:

- materially covers one or more focal assets in grid-interactive operation, digital coordination, evidence maturity or deployment;
- has enough methodological/source detail to populate Supplementary Table S1.

### Exclude when it:

- concerns only internal energy efficiency with no external grid response;
- concerns only communication or AI prediction without an energy decision/service;
- merely sums or co-locates assets without joint control or a common service;
- lacks an identifiable system boundary, baseline or asset role;
- presents prospective 6G capability as if operational;
- is retracted, unverifiable, duplicated or only available as a search snippet.

Use controlled exclusion codes from the codebook and retain one primary reason plus optional notes.

## 8. Full-text and licensing rules

- Retrieve only lawful OA copies, author manuscripts, repository copies or files already legitimately supplied by the user.
- Do not bypass paywalls, automate sign-in, evade robots/rate limits or commit newly downloaded copyrighted PDFs.
- Keep any temporary lawful full text in an ignored local cache and store only bibliographic metadata, short supporting excerpts within fair-use limits, paraphrased evidence and page/table/figure locations in Git.
- If full text is unavailable, keep the record in `needs_manual_review.csv`; do not code numerical outcomes from the abstract unless the manuscript explicitly reports them and the limitation is recorded.
- Chinese explanatory documents must always trace claims to the original source.

## 9. Retractions, versions and corrections

Before freezing inclusion:

- resolve the DOI/stable identifier;
- check Crossref/publisher metadata for corrections, retractions and version changes;
- distinguish preprint from peer-reviewed version and link them as one study where appropriate;
- prefer the version of record for extraction while retaining preprint history;
- record access date for mutable official/market pages.

## 10. Provenance minimum

Every coded claim or value requires:

- `paper_id`, `study_id` and optional `scenario_id`;
- DOI or stable URL;
- page/section plus table/figure/equation when available;
- a concise supporting excerpt or faithful paraphrase;
- whether the value is directly reported, calculated by the paper or derived by this pipeline;
- original unit/term and normalized unit/category;
- extractor confidence and manual-verification status.

No manuscript table cell, plotted point or strong synthesis sentence may exist only in plotting code.
