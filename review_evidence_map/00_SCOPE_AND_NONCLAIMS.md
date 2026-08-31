# Scope and non-claims

## Fixed purpose

This is a structured narrative Review plus evidence mapping. The calculations describe the evidence collected under a disclosed protocol. They do not constitute new system optimization or a formal meta-analysis.

The four focal asset classes are:

1. data centres;
2. next-generation communication base stations;
3. electric vehicles;
4. smart and active buildings.

“Multi-asset” means at least two of these heterogeneous asset classes are actively coordinated toward the same grid service in the same scenario. All four need not participate.

## Multi-asset classification rules

A study is multi-asset only when decisions, constraints, power exchange or a common grid-service objective couple at least two focal asset classes.

- A base station used only as a communication link is not a participating energy asset.
- A data centre used only to run an optimizer is not a participating energy asset.
- The grid, a renewable generator, a generic battery or an aggregator does not automatically count as one of the four focal assets.
- A building containing PV, HVAC and a stationary battery is still one building asset unless another focal class participates.
- Co-location or co-appearance in a microgrid does not by itself establish coordination.
- A paper that separately analyses two assets without a coupled decision or common service remains single-asset evidence.

## Coordination is not synergy

“Coordinated” means jointly controlled. Terms such as “synergy”, “superior”, “incremental benefit” or “greater value” are allowed only when a matched counterfactual uses:

1. the same grid service;
2. the same resource boundary;
3. the same operational and primary-service constraints;
4. independent/single-asset or the best available non-joint baseline;
5. an incremental outcome attributable to coordination.

Comparison only with “no control” can show that control helped, not that multi-asset coordination added value.

## Claim ladder

Every paper and every synthesis statement must be assigned to the highest level it truly supports:

1. `L1 nominal_resource` — storage, controllable load, thermal state or compute capability exists.
2. `L2 available_flexibility` — feasible flexibility is quantified under asset constraints.
3. `L3 delivered_service` — grid-relevant tracking or service delivery is evaluated.
4. `L4 net_system_outcome` — losses, digital overheads, rebound, degradation and system boundaries are considered.
5. `L5 deployable_value` — primary service, field operation, economics, standards, security, ownership and market conditions are sufficiently addressed.

Evidence at one level cannot automatically support the next.

## Evidence setting and publication status are separate

Use the fixed evidence settings:

- `E0 concept` — architecture, framework or proposition without numerical validation;
- `E1 synthetic_simulation` — synthetic/modelled inputs and simulated assets;
- `E2 measured_data_replay` — real measurements or calibrated models used offline, without live control;
- `E3 lab_or_HIL` — laboratory, hardware-in-the-loop or controlled experimental platform;
- `E4 controlled_field_pilot` — physical operational assets in a bounded field pilot;
- `E5 sustained_operation_or_market` — sustained operational or real-market delivery.

Also record publication status independently: peer-reviewed article, conference paper, preprint, institutional report, standard, official market/agency document or commercial material. A field pilot is not automatically methodologically strong; a simulation using measured data is still a simulation/replay.

## Response-time variables must never be conflated

Record separately:

- command or activation latency;
- time to full physical response;
- sustainable delivery duration;
- scheduling/forecasting horizon;
- communication latency;
- controller computation time;
- sampling interval and market interval.

An algorithm time step, communication delay, market interval or sampling rate cannot substitute for physical response time.

## Explicitly prohibited work

Codex must not:

- create a four-asset dispatch simulation or optimization;
- train a new AI model or controller;
- invent synthetic operational results to fill evidence gaps;
- average heterogeneous percentage improvements;
- rank asset classes by a composite “maturity”, “importance” or “value” score;
- convert missing information to zero or “not considered”;
- treat a blank evidence-map cell as technical impossibility;
- call prospective IMT-2030/6G concepts deployed 6G evidence;
- count communication or computation capability itself as grid-service delivery;
- use the “brain–nerve–terminal” metaphor or “1+1>2” as a formal proposition;
- claim that more assets are always better or that coordination necessarily creates net benefit;
- describe an illustrative or truncated corpus as the whole literature.

## Wording rules

Prefer:

- “within the included corpus”;
- “reported in the reviewed studies”;
- “modelled evidence”;
- “limited field evidence was identified under this protocol”;
- “no eligible evidence was identified in this corpus”.

Do not use “proves”, “first”, “mature”, “commercially viable”, “scalable”, “real-time”, “field validated”, “synergistic” or “6G deployment” without the exact evidence required by this file and the codebook.

## Automatic failure conditions

The result fails review if any of the following occurs:

- no exact search log, codebook, frozen corpus or exclusion reasons;
- co-presence is coded as coordination;
- repeated papers from one project are counted as independent studies;
- real-data simulation is coded as field operation;
- heterogeneous metrics are pooled;
- preprints, commercial claims and peer-reviewed evidence are silently mixed;
- any displayed number lacks a traceable frozen row and source location;
- study count is interpreted as technical potential, performance, quality or deployment readiness;
- “synergy” is claimed without a matched counterfactual;
- prospective 6G material is coded as deployed grid-service evidence.

