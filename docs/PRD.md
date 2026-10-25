# StoreScout
## Product Requirements Document

**Retail expansion decisions that explain where to open, where to wait, and what must change.**

24 October 2026 | Team Elites | Round 1 submission  
Scope: Bengaluru grocery, 10 candidate sites, four fictional branches, 219 mapped competitor shops | Delivery: 36 hours including all rounds

**Evidence status.** This is a proposed product specification. Model results, latency targets and user tests remain unmeasured. Business records and any simulated geography are labelled SYNTHETIC; commercial assumptions are ASSUMED; verified source records are REAL. No interviews, retailer outcomes or live integrations are claimed. These labels persist in the interface and export. The exact event deadlines and named team assignments must be recorded at kickoff; relative checkpoints below are planning commitments.

## Current prototype scope

Implemented: Bengaluru grocery only; fixed ten candidates/four fictional branches; mapped competitors as context; area-wide demand/rent, per-location base rent/sales overrides, scenario budget and infrastructure timing/effect; immutable saved analyses and portfolios; persistent before/after references; stored PDF reports.

Deferred: new projects and CSV import UI/API; user-adjustable horizon, valuation date, margin, OPEX, CAPEX and competition; other categories/cities; verified rental listings. Existing PRD requirements for these remain unmet rather than implied delivered. Public rollout also requires persistent hosting, backups, HTTPS and monitoring.

## 1. Executive Summary

StoreScout helps an expansion team choose new grocery stores under a capital budget by connecting demand, competitors, accessibility, operating costs and existing-branch displacement. It returns an explained shortlist, a budget-feasible portfolio, rejected sites and the rent or sales conditions that could make a weak location viable. The prototype evaluates **10 sites**, includes **four fictional existing branches**, and compares **three infrastructure states: Current, Opens and Delayed**. Its decision criterion is incremental network NPV rather than gross new-store sales.

Three mechanisms carry the product: cannibalisation-adjusted financial ranking; FailFast's inverse calculation of maximum affordable rent or minimum sales change; and infrastructure-conditional portfolios. DaypartDNA provides POI-derived temporal opportunity and supporting evidence. These mechanisms form one reviewable investment case, with every result linked to its source, model, assumptions and scenario.

A locally loaded, trained tabular model must affect sales estimates and downstream decisions. When real comparable outcomes are unavailable, an explicitly synthetic training/evaluation pipeline demonstrates meaningful ML; it does not establish real-market forecasting accuracy. Exact enumeration selects the best feasible set under the declared full-network model for the capped 10-site problem. The application supports human approval and does not execute investments.

## 2. Problem, Users and Decision Impact

### 2.1 The decision that needs improvement

An expansion team can approve a high-sales site whose rent and transferred existing-branch sales consume its apparent value. Population, destination mix, costs and competition are often evaluated separately; StoreScout's workflow hypothesis is that bringing them into one consistent calculation will improve the clarity and speed of investment review. This hypothesis awaits user validation.

A fictional exposure example makes the consequence tangible: INR 2 crore fit-out CAPEX plus INR 6 lakh monthly rent over 60 months equals INR 5.6 crore of modelled gross outlay before other costs. This is arithmetic on ASSUMED inputs, not a market benchmark or a claim about legal lease obligations. StoreScout is intended to expose such commitments and their dependencies before approval.

### 2.2 Personas and pain-to-metric links

| User and context | Current workflow hypothesis and failure | Output acted on | Success measure |
| --- | --- | --- | --- |
| Expansion manager preparing a shortlist for site visits | Compares maps, property listings and field notes; a sales estimate hides network overlap | Ranked comparison with named decision drivers | Shortlist task completion and decision comprehension, K06-K07 |
| Finance analyst defending an investment request | Reconciles rent, fit-out and forecast spreadsheets; assumptions drift across alternatives | Reproducible NPV bridge and rent-rescue threshold | Financial oracle and rescue accuracy, K04 |
| Regional operations manager protecting four branches | Reviews catchment overlap separately from the new-store case | Before/after allocation and lost contribution by branch | Allocation conservation and explainable reversal, K04/K08 |
| Investment approver allocating a limited budget | Reviews individually attractive proposals without a consistent combination analysis | Selected set, exclusions and opening-delay comparison | Feasible portfolio and held-out decision regret, K03/K09 |

Validation plan: observe two expansion/finance users on their current comparison workflow, then run the same task in StoreScout. Record actual role, baseline duration, errors and approval evidence requested. Until these conversations occur, no quotations or validation findings are inserted into the PRD. Five representative or proxy testers are the later usability sample; proxies are identified explicitly.

### 2.3 Worked investment example

All values below are fictional, annual amounts in INR lakh except CAPEX. Five-year cash flows are constant and discounted at 12%; the annuity factor is approximately 3.604776. Lost branch contribution is supplied as an ASSUMED fixture input, not inferred from the table.

| Calculation | Site A: higher sales | Site B: lower sales |
| --- | --- | --- |
| Revenue / gross margin | 300 / 30% | 240 / 30% |
| Gross profit | 90 | 72 |
| Rent / other cash OPEX | 48 / 24 | 18 / 18 |
| New-store operating contribution | 18 | 36 |
| Lost existing-branch contribution | 12 | 3 |
| Annual incremental network cash flow | 6 | 33 |
| Initial CAPEX | 80 | 60 |
| Five-year incremental NPV | -58.37 | +58.96 |

Site A's extra sales do not cover its larger costs and branch displacement. FailFast rejects A on base NPV and computes its recovery condition; B ranks above A. These independently calculated values anchor AC09. They demonstrate the intended reasoning rather than observed returns.

## 3. Core Journeys and Differentiation

### 3.1 The complete decision journey

1. Open the labelled Bengaluru grocery prototype and its fixed candidate dataset. Set budget and supported what-if assumptions. Project creation, CSV imports and additional financial controls remain deferred acceptance work, as listed in the implementation scope below.
2. Inspect map and table evidence for demand, competition, access and existing coverage. Compare weekday-lunch and weekend-evening DaypartDNA profiles and their POI contributors.
3. Compare two sites using modelled sales, displaced branch contribution, incremental NPV, sensitivity and FailFast diagnosis. Missing critical evidence yields REVIEW_REQUIRED.
4. For a weak site, request the maximum viable rent or minimum sales multiplier. Apply a feasible change to a new immutable scenario; recheck all rules, ranking and eligibility.
5. Switch Current, Opens and Delayed by 24 months. Inspect the event status and proxy changes; keep any assumed commercial response explicit.
6. Optimise the eligible sites under the scenario's budget and store-count cap. Review the empty plan if no positive set is supported. Export the frozen portfolio, exclusions, assumptions and evidence.

The value moment is an explainable decision reversal: a lower-sales location creates more incremental value, or an apparent winner is attractive only if an infrastructure assumption holds. A rent rescue changes the relevant rule without waiving unrelated hard failures.

### 3.2 What existing tools establish

| Alternative | Capability verified from the cited source | Consequence for StoreScout's claim |
| --- | --- | --- |
| ArcGIS Business Analyst | Weighted site-suitability criteria, map-based rankings and export | Mapping and ranked suitability are established capabilities; they are not claimed as new |
| Placer.ai Site Selection Report | Customisable fit parameters include demographics, competition and cannibalisation | Cannibalisation-aware comparison is established; StoreScout cannot claim to invent it |
| StoreScout, proposed | One trace from assumed/modelled demand through network cash flow, inverse rescue and dated infrastructure scenarios to exact capped portfolio choice | Differentiation is the integrated, inspectable decision workflow; broader vendor feature absence has not been established |

Primary sources: [ArcGIS suitability documentation](https://doc.arcgis.com/en/business-analyst/web/suitability-analysis.htm), [Placer.ai Site Selection Report](https://marketplace.placer.ai/app/site-selection), accessed 24 October 2026. No source here establishes exclusivity, Indian coverage, prices or competitor inability to support further workflows.

DaypartDNA has a decision consequence: supported baseline POI/daypart descriptors enter the learned demand model. An ablation records their effect on held-out prediction and economic ordering. Without evidence of improvement, the profile remains useful context and is not called a proven predictive advantage. Its future-infrastructure display has a separate, single commercial-response path defined in section 7.

A possible future asset is a permissioned record of decisions, assumptions and later store outcomes for recalibration. That dataset does not exist in the prototype and is not presented as a current moat.

## 4. Functional Requirements and Scope

All supplied F01-F08 outcomes remain mandatory. The build phases below order implementation, not permission to remove a feature. Provenance, validation and evaluation versions apply from the first slice onward.

### 4.1 Delivery tiers within P0

| Tier | Work included | Gate |
| --- | --- | --- |
| **P0-A: core investment loop** | F01, F03, F05 and F06 using exact enumeration capped at 10 sites; rent/demand edits from F02; saved report | One input reaches model inference, network allocation, cash flow, ranking, full-network selection and saved report |
| **P0-B: required differentiators** | F08 rejection and rent rescue; F07 DaypartDNA profiles plus Current/Opens/Delayed; remaining F02 propagation | Both innovations recompute results on the P0-A project |
| **P0-C: decision integrity** | F04 source/sensitivity evidence; atomic versioned saves; project validation; stale-response protection; truthful exact/partial status | Every decision-driving value is traceable and screen/report outputs share one evaluation ID |

All three tiers belong in the MVP and Round 1 commitment. They order dependencies; none makes F01-F08 optional. The demo covers the P0-A decision reversal and both P0-B differentiators.

| ID | Mandatory P0 outcome | Build phase | Acceptance |
| --- | --- | --- | --- |
| F01 | Disclosed demand inference; sales, contribution, incremental cash flows, NPV, horizon ROI and simple payback | A: economic loop | AC03-04, AC28 |
| F02 | Saved baseline; rent/demand edits first, then margin, costs, competition, budget and infrastructure timing; consistent recomputation | A then B | AC07, AC13, AC24-27, AC29 |
| F03 | NPV-based ranking with ties, named drivers, downside flags and visible exclusions | A | AC09-10, AC21 |
| F04 | Sources, freshness, missingness, method labels, explanations and low/base/high sensitivity | Cross-cutting A/B | AC06, AC08, AC10, AC15 |
| F05 | Bounded before/after allocation; existing-branch contribution deducted once; full selected-set interaction | A | AC05, AC12 |
| F06 | Exact budget/count/eligibility-constrained full-network portfolio for at most 10 sites; truthful completion status and empty set | A | AC11-12, AC23, AC30 |
| F07 | POI time profiles plus one infrastructure event's Current/Opens/Delayed comparison, with explicit demand assumptions | B: differentiators | AC18-20, AC24-27 |
| F08 | VIABLE / AT_RISK / REJECTED / REVIEW_REQUIRED; rule evidence and bounded rent/sales rescue | B | AC21-23 |

Required support is limited to saved projects, validated imports, two-site comparison, map/table, source details, usable errors and a downloadable decision report. Three MVP screens deliver the five existing surfaces: **Explore & Compare**, **Scenario & Rescue**, and **Portfolio & Report**. Separate pages are optional presentation depth.

| Priority / item | Trigger and value | Reason to defer |
| --- | --- | --- |
| P1: Monte Carlo sensitivity | Deterministic stress cases pass; uncertainty distributions are defensible | Extra runtime and interpretation burden |
| P1: road-network catchments | A permitted routing dataset is available and cached | Radius-based features already support the truthful P0 workflow |
| P1: real-data calibration/intervals | Representative permissioned outcomes and calibration split exist | Synthetic labels cannot validate real-world interval coverage |
| P1: additional projects/richer exports | Single-event flow and standard report pass | Adds coverage rather than a missing core outcome |
| P1: scenario-robust portfolio | Exact single-scenario portfolio is correct and all three infrastructure scenarios persist | Adds a multi-scenario decision objective; show worst-case NPV or regret under delay without changing the P0 recommendation |
| P1: CP-SAT scale extension | Candidate cap is formally raised and exact runtime no longer meets target | Unnecessary second solver for 10 sites; requires its own approximation audit |
| P2: more cities/formats, satellite features | A second market has adequate sources and validation capacity | Does not improve correctness of the first-city decision |
| P2: POS integration, refresh/retraining, collaboration | Permissioned pilot and operational owner exist | Adds external access, lifecycle and identity scope |

**Critical path:** validated fixture -> actual model inference -> bounded network -> finance -> FailFast/scenarios -> exact portfolio -> consistent report. **Cut ladder:** animation; extra visual layers and ingestion automation; optional profile detail beyond the two demonstrated profiles; separate page layouts and basemap polish. Retain underlying time-bin data, Current/Opens/Delayed, all eight outcomes, source labels, model inference and correctness. Non-goals include investment execution, guaranteed returns, measured footfall without measurements, personal movement tracking, national real-time coverage and production multi-user security.

## 5. Architecture, Feasibility and Contracts

### 5.1 One local modular application

| Decision | P0 choice and reason | Deferred alternative |
| --- | --- | --- |
| Client/map | Next.js + TypeScript + MapLibre; local GeoJSON boundaries, sites and evidence layers on a plain background | Licensed PMTiles basemap or elaborate animation |
| Backend | FastAPI/Pydantic with Python/NumPy domain functions | Separate services or job infrastructure |
| Persistence | SQLite plus versioned GeoParquet; sufficient for one operator and small fixed geography | PostgreSQL/PostGIS when workload warrants a server |
| Demand | Offline CatBoost and regularised linear baseline; load the selected fitted artifact locally | More complex models without measured benefit |
| Portfolio | Full-network enumeration of <=1,024 sets | CP-SAT at a separately approved scale trigger |

The city is fixed to Bengaluru for P0. Use a bounded OSM extract and chosen population release where permitted. If source acquisition fails, retain the city and use an explicitly synthetic geographic fixture; do not claim real source coverage. Fictional financials and a hypothetical same-city event are allowed. No paid API, external LLM or online basemap is required in the judging path.

```text
Offline: source validation -> feature snapshot -> training/evaluation -> model artifact

Inputs + immutable scenario (L7)
             |
 L1 validate + provenance
             |
 L2 spatial + DaypartDNA + infrastructure exposure
             |
 L3 local demand inference -> L4 bounded network allocation
                                      |
                             L5 cash flows and NPV
                                      |
                        L6 evidence + FailFast/rescue
                                      |
                         L8 ranking -> L9 exact portfolio
                                      |
                   atomic Evaluation + PortfolioRun -> UI/report

L7 applies deltas before execution and reruns affected L2-L9 modules.
```

Use at most 2,000 geographic cells, 10 candidates and four branches. A simple 2,000 x 14 x 1,024 scale estimate is about 28.7 million cell/store/subset contributions for one static allocation pass; this excludes multiple periods, sensitivity cases and calibration. Cache baseline denominators and attraction matrices, process subsets in bounded batches, and reuse allocations for rent-only changes. This explains the computational scale, not a latency benchmark. Measure the five-year, three-state path on the target laptop.

The 5-second portfolio target and a 5-second hard enumeration deadline apply to one requested scenario. Start with feasible empty NPV 0 and always recheck an incumbent. If all subsets finish, return FULL_NETWORK_EXACT; otherwise return FEASIBLE_PARTIAL with evaluated/total counts or UNKNOWN if no valid result is available. Do not activate another solver in P0. Reduce optional cell resolution only through a recorded data-version change and label the changed spatial precision.

### 5.2 Minimum API contract

All paths begin `/api/v1`; derived queries require `evaluation_id`. Domain schemas belong to CONTRACT.md before implementation, while this document defines required semantics.

| Endpoint | Required behaviour |
| --- | --- |
| POST /projects; GET /projects/{id} | Create/reopen validated project and assumptions |
| POST /projects/{id}/imports/{stores-or-sites} | Validate and atomically import; enforce project caps |
| GET /projects/{id}/features | Versioned source and feature snapshot |
| GET /projects/{id}/dayparts | Evaluation/time-bin indices, shares and support |
| GET /projects/{id}/infrastructure | Sourced or explicitly hypothetical event records |
| POST /projects/{id}/scenarios; GET /projects/{id}/scenarios | Save immutable deltas; list saved scenarios |
| POST /projects/{id}/evaluate | Produce complete saved evaluation or explicit error |
| GET /projects/{id}/sites/{site_id}/analysis | Demand, allocation, finance, diagnosis and evidence |
| POST /projects/{id}/sites/{site_id}/rescue | Evaluation, lever and bounds -> verified threshold/status; no silent mutation |
| GET /projects/{id}/rankings | Ordered sites plus rejected/review-required records |
| GET /projects/{id}/model | Model card, artifact hash, mode, feature schema and actual evaluation evidence |
| POST /projects/{id}/portfolios | Evaluation, count and acknowledged risks -> saved feasible/exact portfolio |
| GET /projects/{id}/reports/{evaluation_id} | Frozen report; `portfolio_run_id` selects the portfolio included |

Compact examples; values are illustrative, not executed responses:

```json
POST /api/v1/projects/p1/evaluate
{"scenario_id":"s1","feature_snapshot_id":"f1","model_version":"m1"}
200 {"data":{"evaluation_id":"e1","status":"COMPLETE"},
     "meta":{"scenario_id":"s1","method_mode":"model_simulated"}}

POST /api/v1/projects/p1/portfolios
{"evaluation_id":"e1","max_stores":2,"acknowledged_risk_site_ids":[]}
200 {"data":{"portfolio_run_id":"r1","selected_site_ids":["B"],
     "capex_used_inr":6000000,"full_network_npv_inr":5895762,
     "status":"FULL_NETWORK_EXACT","evaluated_subsets":1024}}
```

Budget comes from the evaluated scenario; changing budget creates a new scenario/evaluation so affordability cannot remain stale. Bind risk acknowledgements to that evaluation. Deduplicate using SHA-256 of canonical sorted-key JSON containing project/scenario input hash, feature/source snapshot IDs, model artifact hash, rule/weight versions and financial-engine version. A portfolio key additionally includes evaluation ID, count and sorted acknowledgements. Identical inputs return the same saved result; a changed analytical version creates a different key.

Responses identify project, scenario, evaluation, data and model versions plus computation timestamp. Errors return stable code, safe message and field details: 422 invalid inputs, 404 missing/cross-project object, 409 stale versions, 413 file size, 503 failed computation. A valid empty portfolio is 200. Save evaluations atomically; late responses cannot replace another active scenario; exports never read unsaved slider state.

## 6. Data and Meaningful AI

### 6.1 Sources, labels and reproducibility

| Input | Fixed P0 method | Evidence retained |
| --- | --- | --- |
| Destinations, competitors and boundaries | Bounded OSM-derived extract or synthetic Bengaluru fixture | Origin, licence/permission, retrieved date, category mapping and coverage |
| Population/households | Selected WorldPop release where usable; otherwise synthetic grid | Release/resolution and household-size assumption; never current census by implication |
| Category spending | Relevant HCES aggregate or ASSUMED parameter | Geography/vintage; broad spending proxy is not measured local purchasing power |
| Rent, margin, CAPEX, store history | Four fictional branches and 10 sites | SYNTHETIC/ASSUMED labels, units, generator/fixture version |
| Infrastructure | One primary-source record or hypothetical event | Status, geometry, date uncertainty and hypothetical flag |

Store source/assumption IDs, release and retrieval dates, checksum, transformations, licence record and missing-value rules with every decision-driving feature. Model labels and public geographic features remain distinct. No customer-level personal information is needed.

### 6.2 Model target and simulator

Predict **competitors-only reference annual sales**, before any own-company branch displacement. Inputs are addressable households, spending context, external competition, accessibility, area and supported baseline POI/daypart descriptors. Exclude own-branch coverage, own-branch distance, site identifiers, desired demo ranks and post-opening outcomes. Own-branch effects enter only the allocation stage. Real observed sales are not automatically a valid target for this counterfactual reference; they require a compatible calibration design.

P0 uses `model_simulated` when comparable real targets are unavailable. Create at least 2,000 observations: 100 synthetic markets with 20 independently generated potential stores each. The simulator generates cell wallets, external attractions and store format effects; a gravity process yields competitors-only target sales, with heterogeneous market parameters, noise, sparse-source cases and capacity limits. Apply lognormal observation noise and cap targets to the physical wallet. Save the generator code, parameters and seed; the showcase 10 sites are excluded from training and testing.

Freeze market-grouped 60/20/20 train/validation/test partitions; shared market/store records never cross them. Add 20 separate shifted markets with changed decay, spending and competition parameters for out-of-distribution stress evaluation, never for tuning. Fit preprocessing on training only. Synthetic results measure performance under that generator and do not establish empirical retail accuracy.

Compare CatBoost against median and regularised-linear baselines. Record MAE/RMSE/WAPE, sample counts, segment/stress errors, artifact hash, split and latency. WAPE is `sum(abs(actual-predicted))/sum(abs(actual))`, undefined at zero denominator. Activate the model only after the proposed >=10% relative test-WAPE improvement over median; report the linear comparison and use the stronger supported learned model. A shifted-market WAPE more than twice the ordinary test WAPE triggers a scope warning and REVIEW_REQUIRED for matching unsupported regimes.

Modes are `model_simulated`, `model_real_evaluated` only when a compatible real-data evaluation exists, and `scenario_assumptions` for transparent fallback. Missing model artifacts visibly invoke assumption mode and fail AC28 readiness. No text generation substitutes for learned analysis. P0 explanations combine fitted-model factors, allocation changes and cash-flow terms; optional SHAP is not a prerequisite.

### 6.3 Stress cases and model dependency

Low applies -20% to cell spending and +10% to rent; base uses entered values; high applies +20% spending with unchanged rent. These editable assumptions are nonprobabilistic sensitivity cases. Real calibrated forecast intervals are P1.

AC28 exercises actual hashed inference, an economically meaningful perturbation, and a separately seeded decision-boundary fixture. Record how prediction changes allocation, cash flow and diagnosis/ranking/portfolio where warranted. Daypart-feature ablation is reported separately; removing features is not assumed to improve or worsen the model. Generated explanations refer to saved evidence rather than unsupported causal claims.

## 7. DaypartDNA and Infrastructure Timing

For site i and disjoint time bin t, compute `raw(i,t) = sum_p weight(category_p,t) * exp(-distance_m(i,p)/750) * availability(p,t) * evidence_weight(p)`. The 750 m decay length and 1.5 km radius are ASSUMED, versioned defaults. `share(i,t)=raw(i,t)/sum_t raw(i,t)` when supported and nonzero. Show raw cross-site opportunity on one scale and within-site shares separately.

Six bins in Asia/Kolkata are weekday 06-11, 11-15, 15-20, 20-06, and weekend 06-18, 18-06; Monday-Friday are weekdays and overnight bins belong to their starting day. Publish the category matrix with duration/day-frequency weights. Unknown opening hours use a flagged neutral assumption. Missing coverage returns null/review; known supported zero is separate. Label the visual POI-derived opportunity proxy; it does not count visits or identify people.

Infrastructure records contain type, geometry, source, verification date, nullable opening range and status: proposed, approved, funded, under_construction, operational, delayed, cancelled or unknown. Current includes supported operational assets only. Opens uses an explicit completion assumption; Delayed adds 24 months; cancelled never activates. Unknown dates/geometry require a hypothetical assumption or review. Do not invent numerical completion probabilities from status.

Geometry produces a proximity exposure in [0,1]; it does not establish measured travel-time savings. Future POI-profile changes are descriptive. **The single P0 commercial bridge** is an explicit multiplier on the baseline standalone target: `target(i,y)=baseline_target(i)*(1+exposure(i)*assumed_effect*active_fraction(y))`. Require a nonnegative result. Do not feed the same hypothetical uplift back into model features and re-infer it a second time. Solve the target's attraction using the fixed reference, once per affected period, then freeze it across subsets.

Keep one valuation date and five-year horizon. Active fraction is zero before opening and the fraction of that financial year after opening otherwise. Positive, zero and negative effects are supported. Global demand shocks change cell spending; the infrastructure multiplier changes capture within that bounded wallet. An already-operational asset cannot be counted as a new future benefit. Every event assumption and resulting portfolio remains under the same scenario ID.

## 8. Reproducible Network Economics and FailFast

### 8.1 Attraction, calibration and conservation

Let D_g be annual grocery spending in cell g. External competitors are explicit attractions; a strictly positive outside term covers other spending. For store s, use:

```text
A(g,s) = exp(theta_s) * (area_s / 100 sqm)^gamma * exp(-distance_m(g,s)/tau)
p(g,s) = A(g,s) / [outside(g) + sum_all_stores A(g,store)]
revenue(s) = sum_g D_g * p(g,s)
```

Set gamma=1, tau=750 m and outside(g)=1 as disclosed synthetic defaults; competitors have saved assumed coefficients. These values are not empirical estimates. Use metric/geodesic distances. For **each candidate alone**, fit theta by bisection in the fixed competitors-plus-outside reference with no own branches and no other candidates, until revenue matches its model target within INR 1 or 100 iterations. Bracket by bounded expansion of theta in [-30,30]. If target exceeds supported attainable wallet, clip to the bracket's attainable revenue, record requested/achieved target and flag model-support review; never silently claim target fidelity.

The four fictional branches use saved assumed theta values and synthetic baseline sales generated jointly by the full existing-branch network. Do not independently fit their sales in isolated networks and assume the combined history still reconciles. Any later real-data branch calibration must be joint and report residuals; it is outside the synthetic P0 requirement.

Freeze all scenario-specific attractions before enumerating portfolios. For each subset, add its candidates to the same four-branch/external baseline and recompute shares without refitting theta. Scenario baseline and subset use the same wallets and event/competition assumptions. Company plus outside shares sum to one within 1e-6; predicted standalone sales are never added to already allocated spending.

Displaced contribution is `sum_existing[(revenue_before-revenue_after)*variable_contribution_margin]`. In a fixed baseline, adding positive attractions cannot increase existing shares. Define that margin as revenue less costs avoided when those sales disappear; existing fixed costs remain. Candidate contribution uses its own gross margin and cash OPEX. A hypothetical competitor changes the denominator in both no-expansion baseline and selected-set comparison. Missing required evidence is review-required rather than an automatic commercial failure.

### 8.2 Finance and rescue

```text
gross_profit_y = allocated_revenue_y * gross_margin_y
store_contribution_y = gross_profit_y - 12*monthly_rent_y - annual_opex_y
network_cashflow_y = sum_new_store_contribution_y - lost_existing_contribution_y
NPV = -sum_new_CAPEX + sum_y network_cashflow_y/(1+discount_rate)^y
horizon_ROI = (sum_y network_cashflow_y - CAPEX)/CAPEX
```

OPEX excludes rent and COGS already counted, and no displaced sales are deducted again as costs. Defaults are five years and 12% discount rate, editable assumptions; constant-price, before-tax, no terminal value. Tax, working capital and inflation are excluded unless entered consistently. Simple payback interpolates first cumulative recovery; null means not recovered. Zero CAPEX yields null ROI.

Independent oracle: INR 1,000,000 CAPEX and INR 300,000 yearly incremental cash flow for five years at 10% gives NPV INR 137,236.03, ROI 50% and payback 3.3333 years. Numerical tolerance is INR 1, 0.1 percentage point ROI and 0.01 year payback.

| State in precedence order | Condition | Portfolio rule |
| --- | --- | --- |
| REJECTED, hard | Invalid/out-of-area/unavailable site or CAPEX above evaluated budget | Excluded; recheck affordability only after a budget-scenario change |
| REVIEW_REQUIRED | Critical missing/unsupported input or unresolved calibration | Excluded pending correction |
| REJECTED, economic | Base incremental NPV < 0 | Excluded under default policy; reconsider through a changed scenario |
| AT_RISK | Base NPV >=0 but downside <0 or noncritical evidence warning | Include only with evaluation-bound acknowledgement |
| VIABLE | Required inputs complete; base/downside NPV >=0; no hard failure | Eligible |

Record all rules even when precedence chooses one displayed state. For constant rent and fixed other inputs, `max_monthly_rent=NPV_at_zero_rent/[12*sum_y(1+d)^(-y)]`. Verify in the same engine; negative zero-rent NPV means no nonnegative rent rescue. For minimum sales, scale the standalone target, recalibrate in the same reference and reallocate; use bounded search only after checking monotonicity. Default bounds are rent 0..2x current and sales multiplier 0.5..3.0. Return NOT_RECOVERABLE_WITHIN_BOUNDS or NON_MONOTONIC as needed. A computed financial threshold does not clear other failed rules.

### 8.3 Ranking and exact portfolio

Rank eligible supported sites by base incremental NPV descending, then lower CAPEX, then stable site ID. Retain rejected/review lists. Show downside/evidence separately rather than hiding them in a score.

For each eligible subset, use the complete network cash-flow equation above, deduct branch displacement once for the entire set, and enforce CAPEX budget/count/acknowledgements. Use integer paise for accepted budget/CAPEX; do not reuse rounded display amounts. Include empty NPV 0 and select the highest feasible value. Ties favour lower CAPEX, then fewer stores, then sorted site IDs. All subsets evaluated yields full-model optimality for the specified assumptions, not real-world certainty. Partial enumeration returns a feasible incumbent with a gap explicitly unknown; it never proves that no positive set exists. Reject a negative incumbent in favour of feasible empty zero.

## 9. Experience, Persistence and Trust

Explore & Compare merges map/list, evidence, rankings and two-site detail. Scenario & Rescue holds sliders, rule diagnoses and the event timeline. Portfolio & Report combines selected stores, exclusions, budget, method/status and export. These three screens preserve all five original functional surfaces.

Use restrained light styling, keyboard navigation, visible focus, text status labels and a table equivalent to map decisions. Clearly distinguish loading, stale, empty, review-required and failed computation. A visual highlight never implies investment approval.

Persist project, scenario, source snapshot, model artifact, evaluation and portfolio-run identities. Unknown is null with a reason; money is INR, fractions are decimals, coordinates WGS84, distances metric and timestamps UTC. Imports are UTF-8 CSV with required headers, finite numbers, unique IDs and same-city/category checks. Safety ceilings are 5 MB/5,000 rows, while **project caps remain 10 candidates and four branches**; reject excess records atomically. Escape text in HTML and neutralise spreadsheet formula prefixes on export.

The P0 boundary is one local operator, fictional business data and no customer PII. Bind the API locally, validate object/project association and restrict the application origin. Keep secrets and raw uploads out of logs; remove raw files after parsing. Reset only labelled demo state. Public multi-user deployment requires a separate access design.

## 10. Success Metrics and Build Gates

The metric tree is **a correct, understood, budget-feasible decision** -> financial/allocation correctness and source integrity -> task completion/comprehension -> model evidence and latency. Decision-quality simulation is evaluated independently of the optimiser's own objective.

| ID / metric | Proposed threshold and measurement | Owner / action on failure |
| --- | --- | --- |
| K01 cached load | p95 <=3 s over 30 loads, fixed 10/four demo, recorded laptop | Frontend: remove optional layers; investigate critical delay |
| K02 scenario update | p95 <=2 s over 30 rent/demand/event edits, consistent visible evaluation; excludes portfolio | Integration: profile recomputation and preserve stale-state label |
| K03 portfolio | p95 <=5 s over 30 fixed-cap runs; exact/partial status truthful | Core: optimise caching; incomplete enumeration never earns exact status |
| K04 correctness | Finance tolerances in section 8; allocation error <=1e-6; zero budget/empty plan valid | Finance/QA: block release on any invariant failure |
| K05 evidence/model | 100% decision inputs labelled; fitted local inference is used (`model_real_evaluated` or `model_simulated`); >=10% test-WAPE gain versus median in the declared data mode; shifted-market report | Data/ML: block AI-ready claim if inference/evaluation gate fails |
| K06 decision time | >=4/5 testers finish shortlist -> rescue -> portfolio uncoached in <=6 min; compare the same task's spreadsheet time | UX: revise blocking steps; no speedup claim without measured baseline |
| K07 comprehension | >=4/5 identify rejection reason and distinguish proxy from footfall | UX/QA: fix explanation and labels before demo |
| K08 explained reversal | Controlled AC09/AC28 fixtures reverse for the stated economic reason; record driver/NPV changes | QA: block if output is hardcoded or reasons disagree |
| K09 simulated decision quality | On 100 held-out market cases, report median true-simulator NPV difference versus sales-greedy baseline, loss count and regret; target nonnegative median difference | ML/QA: analyse negative result; do not claim business improvement |
| K10 reliability | Three consecutive 3.5-4 minute complete demos with external access disabled | Release: block promotion on a mandatory-flow failure |

For K09, the simulator's hidden test outcomes, not the fitted prediction objective, value the chosen sets. Both policies receive the same observable inputs and budget; the sales baseline selects by predicted sales until budget/count fills. Include empty actions consistently under a preregistered policy and report negative outcomes. Freeze cases before interpretation. This is a simulated comparison, not proof of investment lift. Record runtime, data/model versions, warm/cold state and actual results with all metrics.

### 10.1 Round 1 rubric coverage

| Published dimension | Weight | Where the submission addresses it |
| --- | ---: | --- |
| Problem Definition & Empathy | 20% | Section 2: role-based decision pain, labelled investment example and an explicit user-validation plan |
| Technical Architecture & Feasibility | 25% | Sections 5-8: data flow, model/evaluation, allocation, finance, failure paths and timed workload bounds |
| Feature Scope & Prioritisation | 20% | Section 4: F01-F08, staged P0, triggered P1/P2 and a mandatory-feature cut boundary |
| Innovation & Differentiation | 20% | Section 3: verified category comparison, DaypartDNA consequence and FailFast recovery; no unsupported “first” claim |
| Structure & Measurable KPIs | 15% | Section 10 and Appendix A: owner, threshold, action, measurable outcomes and acceptance tags |

Weights come from the supplied Round 1 notice. This map supports review; it is not a predicted judge score.

### 10.2 Delivery within 36 hours

Four responsibilities are data/ML, economic core, UI/integration and QA/release; actual people may combine them. The following are proposed concurrent allocations, not claimed staffing or completed effort. Data/ML and core each have roughly 14 focused build hours, UI/integration 18, and QA/release 8 plus shared checks; feasibility depends on the actual team. If capacity is lower, take the cut ladder before weakening mandatory outcomes.

| Gate | Relative deadline and work | Exit evidence |
| --- | --- | --- |
| G0 | H00-H02: intake, fixture, dependencies, model mode, contract | Parse one real input; fit/predict spike; save/reopen state; actual deadline/owners recorded |
| G1 | H02-H08: model/core/UI slice | Real inference -> allocation -> finance -> persisted UI output; one error path |
| G2 | H08-H14: differentiators and scenarios | Daypart contrast, Current/Opens/Delayed, FailFast and verified rent rescue |
| G3 | H14-H22: portfolio/report/integration | F01-F08 use shared versions; exact portfolio, exclusions and export; freeze features |
| G4 | H22-H28: acceptance and failure testing | All ACs and numerical oracles recorded; no unresolved mandatory failure |
| G5 | H28-H36: freeze, independent review, clean-run and submission | Three rehearsals, known-good commit, backup and accessible final artifacts |

All round activities consume this clock. Convert checkpoints to actual event timestamps at kickoff and submit Round 1 by its own deadline; H36 is not assumed to be the PRD deadline. Independent review cannot be replaced by the author's confidence summary. No new scope after H22; after H28 accept only critical fixes.

## Appendix A. Acceptance Criteria

**D = demo-critical end-to-end gate; S = full-suite check. Every D and S remains required for P0 completion.** Tags focus rehearsal and failure triage; they do not waive integrity, security or arithmetic checks. Each evidence record identifies owner, commit, input/version, command, expected value, actual result and limitation.

| ID | Gate | Observable check and expected result |
| --- | --- | --- |
| AC01 | D | Save/restart/reopen: project, assumptions and scenario IDs persist unchanged |
| AC02 | D | Canonical demo plots exactly 10 candidates/four fictional branches with source labels; over-cap imports fail |
| AC03 | D | Supported site shows annual INR sales, model mode and analytical versions; unsupported input receives review |
| AC04 | S | Finance oracle meets INR 1/0.1 percentage point/0.01 year tolerances; zero CAPEX/null ROI and no payback/null work |
| AC05 | S | Overlap fixture conserves wallet and deducts existing contribution once; frozen attraction remains unchanged across subsets |
| AC06 | S | Without real calibration labels, sensitivity is never presented as a real-world forecast interval |
| AC07 | D | Rent +20% updates finance without changing POI/population; demand changes allocation and dependent results |
| AC08 | S | Every analysis/report preserves source IDs, dates, missingness, mode and model/formula factors |
| AC09 | D | Section 2.3 higher-sales site ranks below the higher-NPV alternative; calculations/ties match stated rules |
| AC10 | D | Recommendation identifies three computed drivers and an evidence-linked risk where applicable |
| AC11 | D | Normal/tight/zero budgets enforce budget/count/eligibility; zero produces explained empty plan |
| AC12 | S | Tiny hand-checkable network and all feasible 10-site subsets verify the selected highest full-network NPV; no pairwise substitute |
| AC13 | D | Switching scenarios keeps map, cards, FailFast, ranking, portfolio and report on matching saved versions |
| AC14 | S | Clean checkout starts documented demo, local model and essential assets without undocumented files |
| AC15 | S | REAL/SYNTHETIC/ASSUMED labels survive export; fictional stores have no invented brand affiliation |
| AC16 | D | External LLM/paid-data/network access disabled: local model, boundary map/table and report still work |
| AC17 | D | Three consecutive 3.5-4 minute complete demos pass without a blocking error |
| AC18 | D | Weekday-lunch/weekend-evening contrast updates actual category-weighted profile/map values deterministically |
| AC19 | S | Missing and supported POIs show coverage/date distinctions; neither is claimed as measured footfall |
| AC20 | S | Supported nonzero shares sum to 1 within 1e-6; zero and unknown differ; rent alone does not alter profile |
| AC21 | S | All four status classes match precedence, rule values, reasons and eligibility |
| AC22 | S | Rent/sales threshold verifies within INR 1; either side crosses NPV zero; bounded/no-solution/non-monotonic cases explicit |
| AC23 | D | Applying feasible rescue refreshes diagnosis/ranking/eligibility; hard failures persist and risk acknowledgement is logged |
| AC24 | D | Current excludes unbuilt access; Opens changes supported event exposure with source/status labels |
| AC25 | D | +24-month delay activates in correct year fraction; cancelled event never activates |
| AC26 | S | Unknown date/geometry requires hypothetical assumption/review; operational assets are not counted as future openings |
| AC27 | S | Positive/zero/negative commercial effects propagate once through bounded network/economics; zero preserves commercial baseline |
| AC28 | D | Hashed fitted inference + held-out perturbation changes sales/allocation/cash flow; boundary fixture changes diagnosis/rank/set where warranted; record baseline/OOD/ablation; assumption-only fails |
| AC29 | S | Reverse response order and fail before commit: stale/partial results neither replace active evaluation nor export |
| AC30 | S | Force enumeration cutoff: truthful FEASIBLE_PARTIAL/UNKNOWN, counts and unknown gap; feasible incumbent checked against empty zero; never false exactness |
| AC31 | S | Bad coordinates, duplicate IDs, excess records, oversize files and formula-like names produce safe errors/no partial writes |
| AC32 | S | Keyboard traversal of three screens/all five functions; reopen export with source/version IDs, exclusions and chosen portfolio |

## Appendix B. Traceability, Risks and Source Record

| Requirement | Feature/enabler | Acceptance |
| --- | --- | --- |
| R01 geography/demographics/competition/access/coverage/costs | Data, F01/F05/F07 | AC02-03, AC08 |
| R02 demand and viability | F01 + learned inference | AC03-04, AC28 |
| R03 ranked explanation | F03/F04 | AC09-10 |
| R04 risk/evidence | F04/F08 | AC06, AC08, AC21 |
| R05 what-if | F02 | AC07, AC13, AC27 |
| R06 cannibalisation | F05 | AC05, AC12 |
| R07 budgeted combinations | F06 | AC11-12, AC30 |
| R08 truthful sources/model | F04/all outputs | AC06, AC15, AC28 |
| R09 saved coherent project | Persistence, F01-F08 | AC01, AC13, AC29 |
| R10 integrated 36-hour demo | Delivery gates | AC14, AC16-17 |
| R11 auditable specification | Requirement/test map | AC01-32 evidence |
| R12 local non-LLM core | Architecture/model | AC16, AC28 |
| R13 temporal opportunity | F07 | AC18-20 |
| R14 rejection/rescue | F08 | AC21-23 |
| R15 event status/open/delay | F02/F07 | AC24-27 |
| R16 meaningful AI | Learned demand affects decisions | AC28 |
| R17 required sections/single file | Sections 1-10 and appendices | Submission inspection |
| R18 data honesty/limitations | Sources/methods | AC06, AC08, AC15, AC26, AC28 |

Principal unresolved assumptions: exact event timestamps/people/hardware; permitted real source coverage; no assumed real training labels; economic parameters and infrastructure response are assumptions. Owners verify timing/capacity at G0, sources/model mode by G0, runtime at G1 and user comprehension by G4. Synthetic city data is an allowed explicit fallback, not evidence of a retrieved source. Missing model readiness, violated finance/allocation invariants, mixed scenario versions or a failing mandatory event flow blocks completion.

The principal risks are unsupported synthetic generalisation, model/network double counting, future-event leakage, source incompleteness, over-cap computation and stale results. Their mitigations are the target/reference definition, grouped and shifted-market evaluation, single event bridge, review status, strict project cap/deadline and atomic versioned saves. No optional feature can replace these checks.

Source basis: the supplied Round 1 notice/problem statement; StoreScout_PRD_Final.pdf; the 37-page FutureInfrastructure handoff; the 107-page complete handoff; the 70-page Reusable AI Project Engineering Playbook; and the supplied improvement feedback. The combined handoff duplicates the standalone handoff and handbook, as checked in the earlier preparation. The handbook supplies process rather than retail-market facts. Vendor references are cited in section 3; neither interviews nor actual product performance were established by this revision.

The specification preserves mandatory F01-F08 and AC01-32, tiers the P0 sequence, moves the second solver to optional scale work, defines the demand reference/calibration and single infrastructure bridge, fixes dataset caps, orders build gates, closes APIs and adds independently evaluated outcome metrics. Suggested interviews, industry-first claims, actuals-upload features and other scope without evidence or timing justification were not inserted. Changes to financial meaning, input units or acceptance thresholds require an updated decision, contract and affected test record.

Glossary: **NPV** = discounted future incremental cash flow less initial investment; **CAPEX** = upfront capital expenditure; **POI** = point of interest; **WAPE** = weighted absolute percentage error; **OOD** = outside the training distribution.
