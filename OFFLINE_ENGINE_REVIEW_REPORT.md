# StoreScout offline ML and decision-engine review

Verdict: **OFFLINE_ENGINE_VERIFIED_WITH_LIMITATIONS**

Review date (UTC): 2026-10-24T23:12:42.166636+00:00. Branch `ML`; HEAD `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`. Review only: no implementation, repair, retraining, API/UI integration or Git mutation.

## A. Executive summary

The reported **36/36 tests were located and rerun: 36 PASS, 0 FAIL, 0 ERROR, 0 SKIP in 7.145s**. The actual selected B.2 CatBoost path executes offline for all ten unchanged Bengaluru candidates and reproduces the saved baseline exactly. Independent oracles confirm the main attraction/allocation, displacement, finance and tiny-portfolio equations. No tested fundamental spending-conservation or finance invariant failed.

An additional **33 targeted review checks produced 23 PASS and 10 FINDING outcomes**. FINDING means an adversarial requirement or boundary was not satisfied, not a failure of the original36 tests. Two checks describe the same deadline limitation. Passing36 does not establish C–G completeness.

Highest-priority issues are ambiguous/unusable direct rescue application under existing multipliers, unenforced model-readiness/snapshot semantics at the prepared-input seam, and a non-preemptive deadline. Other gaps include an infeasible-lower-bound sales search, a supported opening-hours exception-parser error, incomplete Daypart explanations/share outputs and unstructured rule evidence. None was fixed.

All ten current fitted results remain AT_RISK; the default portfolio is empty without acknowledgement. The separately labelled illustrative acknowledged-risk plan is site-05+site-10, CAPEX INR19,800,000 and modelled network NPV INR235,102,400.74. These are synthetic-model/assumed-cost economics, not real-store validation or investment approval. Backend/frontend integration remains open.

## B. Architecture compliance

Authority reviewed: AGENTS.md, docs/PRD.md (F01–F08, §§6–8 and AC01–32), ARCHITECTURE.md, CONTRACT.md, FOUR_HOUR_PLAN.md and docs/handoffs/LOGIC.md. Canonical schemas, pipeline seams, finance helper, current C-onward report/README, implementation/tests, revised data inventory/quality evidence and B/B.1/B.2 dependency records were inspected. This uses independent mathematical calculations; it is not a claim of external human or empirical validation.

| Required behaviour | Actual implementation | Relevant evidence | Verified state / missing behaviour | Severity of remaining gap |
| --- | --- | --- | --- | --- |
| C: six temporal proxies, metric radius/decay, availability/evidence, missing versus0 | [backend/app/domain/geospatial/features.py:26](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/geospatial/features.py:26>); source `build.py:376–440` | GeometryAndDaypart4 tests; R09–R11,R29–R30 | Formula/weekly weighting verified; no category contributions/raw-normalized share; source off-exception parser defective | MEDIUM |
| D: standalone reference calibration; full network and loss exactly once | [backend/app/domain/network/allocation.py:9](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/network/allocation.py:9>); `engine.freeze` | AllocationChecks5;1024-set oracle;R03–R08 | Verified on tested inputs; bounded endpoint bracket used directly rather than bounded expansion; stricter.01INR tolerance is compliant with≤1INR | LOW (algorithm deviation, no demonstrated error) |
| D: actual cashflows, NPV/ROI/payback | [backend/app/domain/network/allocation.py:70](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/network/allocation.py:70>); [backend/app/domain/finance/cashflows.py:15](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/finance/cashflows.py:15>) | FinanceOracleTests4;R01–R05,R28 | Correct tested equations/units; 2024-wallet/2026-cost inconsistency disclosed, not corrected | HIGH for commercial interpretation; no arithmetic failure |
| E: status precedence and every rule's evidence | [backend/app/domain/failfast/rules.py:5](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/failfast/rules.py:5>); `engine.prepare_evaluation` | FailFastChecks;PipelineChecks | Precedence works; hard/review strings lack structured tested values/thresholds; all simulated sites inherently warned | MEDIUM |
| E: bounded same-engine rescue and application | [backend/app/domain/engine.py:205](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:205>); `rules.rent_rescue/sales_rescue` | Existing rescue tests;R12–R14 | Numerical roots work in supplied context; returned effective/relative levers need normalization before canonical overrides; lower infeasible endpoint aborts | HIGH |
| F: Current/Opens/Delayed, single dated bridge, low/base/high | [backend/app/domain/scenario/timing.py:15](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/scenario/timing.py:15>); `engine.py:79–98,123–131` | TimingChecks;R22–R25,R28 | Dated multipliers and stress verified; actual official infrastructure ledger not loaded, operational inclusion asserted rather than reconciled | MEDIUM |
| G: NPV rank with lower CAPEX/stable ID; visible diagnoses | [backend/app/domain/engine.py:161](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:161>) | finance reversal;R31–R33 | Correct key and demonstrated lower-sales reversal/stable-ID tie; no fitted-factor/category explanations | MEDIUM explanation gap |
| G: exact/partial network portfolios, paise, eligibility, deadline | [backend/app/domain/portfolio/search.py:13](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/portfolio/search.py:13>); `engine.run_portfolio` | PortfolioChecks4;R06,R15–R16,R21 | Correct completed exact searches and empty/acknowledged policy; five-second hard limit not enforced inside valuation; UNKNOWN never emitted | HIGH deadline; LOW status coverage |
| Offline orchestration and reproducible provenance | [backend/app/domain/engine.py:118](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:118>); [ml/decision_engine/run.py:36](<C:/Users/Office Pc/OneDrive/Documents/Elites-/ml/decision_engine/run.py:36>) | PipelineChecks9,ActualFittedBengaluru5;R17–R22,R26–R28 | Actual offline model route verified; trusted input record readiness/version semantics not fully enforced; per-record snapshot mismatches accepted | HIGH |

P1 items such as SHAP, Monte Carlo, SALib, OR-Tools and empirically calibrated prediction intervals are **not mandatory missing C–G algorithms**. Full API persistence, public schema extensions, frontend flows, imports and user/release gates are distinct mandatory application work, outside this review.

## C. Part-by-part verification

### C — DaypartDNA

The six canonical bins are weekday06–11,11–15,15–20,20–next-day06 and weekend06–18,18–next-day06, Asia/Kolkata. Source `assign_daypart` correctly maps Saturday02:00 to Friday weekday-night and Monday02:00 to Sunday weekend-evening (R09). The parser correctly wraps a recorded Friday22:00–02:00 interval (R10). The numerical profile function consumes precomputed per-bin availability; it does not itself classify timestamps or parse OSM hours.

`raw=Σ category_weight×exp(−geodesic_metres/750)×availability×evidence` is correctly implemented. Default1500m radius and750m decay are supplied by the loader. The source category matrix matches the approved demo weights. R29 independently checks all six office values with availability.6/evidence.5: raw[.9,1.2,.6,.06,.15,.09]. Representative-week multipliers[25,20,25,50,24,24] total168hours. Supported nonzero **weekly** shares sum1; supported empty profiles return zeros, unknown coverage returns nulls.

The distinction matters: PRD§7 also defines `raw/sum(raw)` within-site share. The implementation exposes only `weekly_exposure_share`, not that raw-normalized share. Weekly normalization is mathematically valid and clearly named; it is not numerically equal to the PRD raw share. Category/bin contribution breakdowns are absent. `source_ids` in individual profiles collects POI sources only; weight version is separate, and availability/weight assumption-source IDs and dates are not included there. Global diagnostics/source files preserve more provenance, but the output is not self-contained.

The source-backed schedule evidence is very limited:

| Site | Mapped POI support | Parsed recorded schedules | Assumed schedules | Parsed fraction |
| --- | ---: | ---: | ---: | ---: |
| site-01 | 544 | 24 | 520 | 4.41% |
| site-02 | 441 | 20 | 421 | 4.54% |
| site-03 | 462 | 27 | 435 | 5.84% |
| site-04 | 284 | 19 | 265 | 6.69% |
| site-05 | 124 | 4 | 120 | 3.23% |
| site-06 | 128 | 6 | 122 | 4.69% |
| site-07 | 122 | 3 | 119 | 2.46% |
| site-08 | 131 | 5 | 126 | 3.82% |
| site-09 | 249 | 20 | 229 | 8.03% |
| site-10 | 206 | 19 | 187 | 9.22% |

These percentages come from revised_v2/daypart_site_support.csv (projected legacy support); the geodesic engine counts can differ near the radius boundary. Current profiles retain assumed-hours counts, but do not expose the parsed fraction or explicitly raise a low-hours-coverage warning. The frozen HTML report omits those counts/fractions; the revised source reports disclose them properly. Therefore disclosure is adequate in the source package and incomplete at the decision-report/profile boundary.

R11 finds a genuine accepted-syntax parser defect: `Mo-Su 09:00-18:00; Su off` leaves540 Sunday open minutes because `off` simply continues instead of clearing prior minutes. Current snapshot has one off-tag expression `Mo-Sa 08:15-16:00; Su,PH off`; that unsupported syntax correctly falls back to assumptions. No current accepted off-expression contamination was demonstrated. This is a mandatory correctness boundary for future supported inputs, not evidence to rewrite current data.

No measured metro entries/exits enter raw opportunity or the20 learned input fields. Historical metro fields remain separate supporting data; neither output claims store footfall. The existing geodesic-versus-legacy projected raw audit records up to~1.412% relative difference; frozen model inputs are not silently replaced with recomputed proxies.

### D — Huff allocation and cannibalisation

Attraction uses exp(theta)×(area/100)^gamma×exp(−distance/tau), defaults gamma1/tau750m, outside1. Cell wallets are finite/nonnegative; outside is strictly positive. Denominator includes outside, aggregate external mass and all included company stores. R08 checks25cells×6company attractions: allocated INR127,043,190.78734568 versus wallet INR127,043,190.78734566; share error2.22e−16. No spending was created beyond floating-point tolerance.

Each candidate is calibrated alone against external competitors/outside, not against own branches or other candidates. Bounds are exactly[−30,30], max100iterations. General helper tolerance defaults1INR; engine uses.01INR and sales rescue.001INR. Direct full-endpoint bisection replaces the handoff’s bounded-expansion bracketing step without a demonstrated numerical failure. Unattainable targets retain requested/achieved values and receive review; bounded diagnostic allocations are not labelled exact target fidelity. Zero target explicitly creates zero attraction.

Existing branch baseline is jointly allocated. Selected subsets add all candidate attractions to that same baseline; baseline-minus-after branch revenue times saved variable margin is deducted once. Candidate reference sales are never added on top of allocated sales. Independent two-cell results R03–R05 verify single/multiple openings. Actual ten-site maximum calibration residual is INR0.00961235. The100-cell whole-AOI centroid network differs from the1500m feature-wallet geometry, and equal external mass remains assumed; these approximations are disclosed.

### D — Finance

The unchanged cashflows.py helper is reused by network_cashflows. Gross profit=allocated annual sales×gross-margin fraction; annual rent=12×monthly rent; OPEX excludes rent/COGS; lost existing variable contribution is subtracted once; NPV subtracts time-zero CAPEX and discounts end-year flows. ROI is a fraction, not percentage; simple payback interpolates first recovery. R01 independently gives NPV137236.0308225341, ROI.5 and payback3.3333333333333335. Zero CAPEX/null ROI, zero demand, negative flows and unrecovered investment are exercised. Five years is the loader default; validated horizons1–10 are supported.

No tax, terminal value, working capital or inflation is inserted. HCES2023-24 nominal wallets (ending-year2024) and synthetic2026 costs are mixed under explicit warnings; arithmetic is verified, but these NPVs are not a consistent-price current commercial forecast. Routing/household fields remain absent rather than fabricated.

### E — FailFast and rescue

Precedence is hard REJECTED > REVIEW_REQUIRED > economic REJECTED > AT_RISK > VIABLE. Hard budget/out-of-area/input eligibility reasons override good economics; missing POI coverage and unattainable calibration produce review. A missing usable model prediction aborts the whole evaluation explicitly (R33), rather than fabricating a site0-sales estimate; this is safe but does not provide per-site nullable unavailable analyses.

Rules retain failed reason strings and financial NPV strings; they do not consistently capture structured tested values/thresholds for budget, coordinates, model support or coverage. All current model_simulated sites get a synthetic-outcome warning, so the actual Bengaluru route cannot reach VIABLE. This conservative policy is disclosed and requires acknowledgement for risk sites.

Rent root uses zero-rent NPV/[12Σdiscount factors], verifies within INR1 and checks both sides. Negative zero-rent NPV yields no nonnegative root. Already viable rents can return SOLVED with a verified root above requested bounds, explicitly marked `threshold_within_bounds=False`; integrations must preserve that distinction. Sales root recalibrates/reallocates each year, searches.5–3, samples17points, reports cumulative declines>INR1, and verifies a nonnegative root residual≤INR1. This is sampled, not a global monotonicity proof. An upper infeasible frontier is searched, but an infeasible first lower point stops immediately (R14).

Crucially, a solved lever is expressed in **current-context coordinates**, not necessarily the canonical override coordinates. R12: rent_multiplier1.2 gives effective monthly threshold44.6834772416 and verified NPV~0; putting that value directly into SiteOverride reapplies1.2 and yields NPV−406.5252369233/REJECTED. R13: an existing sales_multiplier2 gives relative rescue.5355529785 with verified NPV+.749; directly replacing the absolute override with.53555 yields NPV−1826.4052045591. A consumer could normalize these values, but no canonical normalized application helper/contract exists. Current tests do not exercise this required journey. Financial rescue does not clear hard eligibility flags; the existing test verifies no waiver, not a complete applied-rescue workflow.

### F — Infrastructure and sensitivity

Current/Opens/Delayed bridge is applied once to the baseline standalone target. Model features are not re-inferred with the same uplift. Positive/zero/negative effects keep targets nonnegative. Opening2028-04-01 with valuation2026-10-24 produces fraction206/366 in financial year2;24-month delay opens2030-04-01, first activates in year4 at206/365 (R23). Fractions use actual anniversary-year lengths. Cancelled assets never activate; operational assets receive no additional future uplift.

Operational inclusion is not independently established by writing `ALREADY_IN_BASELINE`: the function performs no source/geometry/baseline reconciliation for such assets. The actual loader sets infrastructure=[] and uses mapped transit POIs/precomputed features. It does not load the revised official Yellow/Blue infrastructure ledger. Thus its separate hypothetical connector proves lifecycle arithmetic, not complete official-infrastructure integration. Proposed/unknown future events need explicit date and Point geometry; unknown status additionally requires hypothetical evidence. More than one selected event and non-Point geometry are explicitly unavailable in this P0 path. One OSM transit record has construction=yes; it is outside all ten1500m candidate circles, so no demonstrated current candidate effect, but operational filtering is not a general verified-status policy.

Low uses wallet×.8/rent×1.1; high wallet×1.2/base rent. Actual allocations are recomputed. Across all50 annual site flows, independent algebra matches low/high within6.34e−8INR (R28). Global demand changes both wallets and reference targets once; actual allocations scale within.016INR at.8/1.2 and exactly0 at zero demand (R22). Infrastructure changes capture via target, not wallet; reference infeasibility is reviewed.

### G — Ranking and portfolio

Ranking uses computed incremental base NPV descending, then lower raw CAPEX and stable site ID. Rejected/review diagnoses remain in site_analyses while not entering rankings. R31 independently demonstrates a6000-INR-sales/.05margin site NPV938.18 ranking below a3000-INR-sales/.30margin site NPV3101.04; R32 verifies an identical-economics stable-ID tie. The legacy.75 quality indicator is absent from learned features and ranking keys; it is not used as calibrated confidence.

The optimiser enumerates eligible/count-limited subsets, including empty, with integer-paise budget checks. It recomputes full joint network value; no singleton sum or pairwise penalty substitute appears. Ties use lower accepted CAPEX, fewer stores, sorted IDs. Budget-pruned sets count as examined even without objective evaluation; total_subsets counts the eligible/count-limited search space, not always1024. Complete searches are FULL_NETWORK_EXACT; cutoff between subsets is FEASIBLE_PARTIAL with a valid empty incumbent at minimum. UNKNOWN is a public enum but is not produced by this implementation; objective/validation errors propagate instead. Since empty is always valid for a valid problem, absence of UNKNOWN is not by itself false exactness.

The hard deadline is incomplete. The clock is checked only before a subset. R15 advances the controlled clock to6seconds inside the last objective and still returns exact2/2 after exceeding5seconds. R16 confirms requested.01s deadline with a.05s callback takes~.0506s. **Exactness remains mathematically truthful when all subsets finished; elapsed-time compliance fails.** No incomplete search was observed falsely claiming all subsets complete. README already discloses non-preemption, but that does not satisfy the handoff’s hard5-second budget.

## D. Mathematical correctness and targeted evidence

Independent two-cell oracle: wallets[100,200], external[1,2], outside1, existing attractions[2,1], existing variable margin.2, candidate attractions a[3,1]/b[1,4]. Candidate gross margins.3/.4, monthly rent1 each, OPEX1/2, CAPEX10/20, one-year discount0. Manually calculating per-cell denominators gives:

| Opening | New-store sales INR | Lost branch contribution INR | NPV INR |
| --- | --- | ---: | ---: |
| a | 82.8571428571 | 6.2857142857 | −4.4285714286 |
| b | 120.0000000000 | 7.0000000000 | 7.0000000000 |
| a+b | a59.7222222222; b101.3888888889 | 10.5555555556 | −9.0833333333 |

Budget30/count2 therefore selects b, NPV7, not both. This is independently computed, not derived by summing standalone NPVs. A one-cell standalone target400 from wallet1000, external1/outside1/unit attraction1 has analytical theta=ln(4/3)=.28768207245; production obtains.28768301010 with achieved400.00022504INR.

Every additional read-only check is recorded below. FINDING entries include invalid-input robustness and output completeness checks; they are not all failures of core arithmetic.

| ID | Check | Result | Evidence type |
| --- | --- | --- | --- |
| R01 | Finance oracle | PASS | independent mathematical oracle |
| R02 | Zero CAPEX and unrecovered negative flows | PASS | independent mathematical oracle |
| R03 | Two-cell full-network a | PASS | independent mathematical oracle |
| R04 | Two-cell full-network b | PASS | independent mathematical oracle |
| R05 | Two-cell full-network a,b | PASS | independent mathematical oracle |
| R06 | Independent tiny portfolio including empty | PASS | independent mathematical oracle |
| R07 | Analytical standalone theta | PASS | independent mathematical oracle |
| R08 | Nonnegative probability and spending conservation | PASS | independent mathematical oracle |
| R09 | Overnight starting-day attribution | PASS | actual source schedule functions |
| R10 | Recorded overnight schedule wraps midnight | PASS | actual source parser |
| R11 | Accepted off clause removes previously set opening minutes | FINDING | adversarial parser boundary; not present as accepted syntax in current sources |
| R12 | Rent rescue directly applicable to canonical override with multiplier | FINDING | independent mathematical oracle |
| R13 | Sales rescue directly applicable to existing canonical multiplier | FINDING | independent mathematical oracle |
| R14 | Sales rescue searches beyond infeasible lower endpoint | FINDING | adversarial bounded objective |
| R15 | Five-second deadline accounts for in-flight last subset | FINDING | controlled clock, no real sleep |
| R16 | Wall-clock confirmation of non-preemptive deadline | FINDING | controlled50ms numerical callback stand-in |
| R17 | Mixed snapshot input rejected | FINDING | input consistency boundary |
| R18 | Explicit integration block cannot silently pass | FINDING | prepared-record trust boundary; no genuine model changed |
| R19 | Coverage flag is type-safe | FINDING | invalid-type input boundary |
| R20 | Actual fitted Bengaluru route reproducible and unchanged | PASS | actual fitted inference with network disabled |
| R21 | Actual portfolio policy and exact search | PASS | actual fitted downstream run |
| R22 | Actual wallet shock applied once | PASS | actual fitted predictions with scaled cell wallets |
| R23 | Actual24-month delay and dated bridge | PASS | independent mathematical oracle |
| R24 | operational does not gain a new future uplift | PASS | independent mathematical oracle |
| R25 | cancelled does not gain a new future uplift | PASS | independent mathematical oracle |
| R26 | Actual source snapshot identity alignment | PASS | saved actual source records |
| R27 | Actual canonical response schema validation | PASS | canonical Pydantic validation, dummy identities only |
| R28 | All50 annual sensitivity cashflows match independent algebra | PASS | actual saved allocations plus independent cashflow algebra |
| R29 | Approved category weights and weighted temporal shares | PASS | actual approved weights, synthetic co-located POI, independent arithmetic |
| R30 | Per-category contributors and raw-normalized shares exposed | FINDING | response completeness inspection |
| R31 | Higher sales does not dictate NPV rank | PASS | controlled assumed review fixture |
| R32 | Stable site-ID rank tie | PASS | controlled assumed review fixture |
| R33 | Missing usable prediction blocks recommendations | PASS | controlled assumed review fixture |

## E. Audit of all36 reported tests

Original writer command: `python -m ml.decision_engine.verify`. It writes existing test_results.json, so **it was not invoked in this review**. Its exact suite was rerun through an instrumented `unittest` runner loading `tests.unit.test_decision_engine` and `tests.unit.test_finance`, equivalent to:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m unittest tests.unit.test_decision_engine tests.unit.test_finance -v
```

The instrumented runner redirected results to `.runtime/offline-engine-review/existing_36_results.json`; it did not update original reports. O=independent mathematical oracle; S=explicitly synthetic/assumed fixture; M=actual saved fitted inference. All tests call the real numerical implementation. Mocks deny socket connections or control the clock; no sales estimator is mocked. Synthetic fixture prediction records are explicitly labelled UNIT_TEST_ASSUMED_INPUT inside the tests and **must not be counted as fitted-model evidence**.

| Exact test (class.method) | Component | Evidence | Result | Meaningful assertion | Important uncovered boundary |
| --- | --- | --- | --- | --- | --- |
| `ActualFittedBengaluru.test_actual_artifact_and_ten_site_end_to_end` | Offline actual model | M | PASS | Actual artifact ID,10 sites,219 external competitors, no failed calibration | No real outcomes or independent NPV oracle in this test |
| `ActualFittedBengaluru.test_actual_model_changes_boundary_diagnosis_and_selected_set` | Model dependency | M+S | PASS | Fitted perturbation plus synthetic midpoint CAPEX changes sign/status/set | CAPEX boundary constructed from engine outputs; dependency test, not external financial validation |
| `ActualFittedBengaluru.test_frozen_arrays_unchanged_by_joint_search` | G actual route | M | PASS | Context unchanged; exact nonnegative budget-feasible portfolio | Does not compare actual10-site winner to an independent reference implementation |
| `ActualFittedBengaluru.test_model_perturbation_changes_economics_not_only_label` | Model dependency | M | PASS | Actual wallet-feature+10% inference raises allocated sales and NPV | Only prediction features change; network wallets fixed; not a coherent all-market demand shock |
| `ActualFittedBengaluru.test_portable_bundle_restores_inference_without_original_artifact_directory` | Artifact restore | M | PASS | Restored selected model reproduces prediction; altered support refuses overwrite | Temporary restored files only; not full application clean checkout |
| `AllocationChecks.test_calibration_and_unattainable_target` | D calibration | O+S | PASS | Target400 within.001;1001>wallet reviewed; zero target exact | No target near lower theta endpoint; no iteration exhaustion assertion |
| `AllocationChecks.test_hand_calculated_shares_and_money_conservation` | D allocation | O | PASS | One-cell shares2/7,3/7; allocated+outside+external=100 | One cell only; broader checkR08 |
| `AllocationChecks.test_invalid_numerics_fail` | D validation | S | PASS | Negative wallet, zero outside, NaN attraction rejected | Not exhaustive shape/overflow validation |
| `AllocationChecks.test_own_branch_loss_deducted_once` | D cannibalisation | O | PASS | Branch loss(50−200/7)×.2; cash=300/7×.3−loss | Single branch/cell; independent multi-cell checkR03–R05 |
| `AllocationChecks.test_wallet_scaling_and_competition` | D allocation | O+S | PASS | Wallet×1.25 scales revenue; more competition reduces it | Fixed geometry only; no model economics conclusion |
| `FailFastChecks.test_all_states_and_full_precedence` | E rules | S | PASS | All4 statuses; hard>review>economic; records4 failed rules | No structured actual-vs-threshold rule evidence |
| `FailFastChecks.test_rent_threshold_oracle_and_no_rescue` | E rent | O | PASS | Independent annuity root; signs; negative zero-rent case; out-of-bound viable root flagged | No application through rent_multiplier≠1;R12 exposes gap |
| `FailFastChecks.test_sales_bounds_nonmonotonic_and_verified_root` | E sales | O+S | PASS | Affine root1.1, decreasing/no-recovery and upper feasibility frontier | No infeasible lower point;R14 exposes gap |
| `GeometryAndDaypart.test_availability_override_and_duplicate_rejection` | C schedules | S | PASS | Recorded availability overrides neutral weights; duplicate bins rejected | Does not parse actual hours or reject orphan POI IDs |
| `GeometryAndDaypart.test_dayparts_duration_and_frequency` | C proxy | O+S | PASS | Co-located office raw.25; weekday-night share50/168; six shares sum1 | One category; no opening-hours parser or category contributors |
| `GeometryAndDaypart.test_geodesic_metres_and_invalid_coordinates` | C geometry | O | PASS | Great-circle1degree≈111194.9266m; latitude91 rejected | No radius boundary/antipodal oracle |
| `GeometryAndDaypart.test_unknown_differs_from_supported_zero` | C missingness | S | PASS | Supported empty0 differs from null unknown | No missing-row or non-boolean coverage flag |
| `PipelineChecks.test_demand_scale_and_zero_demand` | F demand scenario | S | PASS | Wallet.8 yields.8 sales; zero demand yields zero sales | Selected first site; all actual sites covered byR22/R28 |
| `PipelineChecks.test_future_effect_applied_once_with_frozen_model` | F bridge | O+S | PASS | Co-located target3000×1.2=3600; saved prediction unchanged | One site/year; not official event lineage |
| `PipelineChecks.test_missing_unsupported_and_invalid_inputs_fail_explicitly` | Input safety | S | PASS | No inputs, null usable prediction, duplicate sites and unknown override reject | No stale snapshot or blocked-record flags;R17–R19 |
| `PipelineChecks.test_pure_deterministic_immutable_pipeline_and_schema` | Orchestration | S | PASS | Two equal runs; inputs unchanged; canonical schemas; finite JSON serializable | Assumed prediction records, not fitted inference |
| `PipelineChecks.test_rent_only_preserves_network_and_dayparts` | F rent scenario | S | PASS | Rent×1.2 changes NPV, preserves frozen matrices/profiles | No rescue application in that multiplied scenario |
| `PipelineChecks.test_rescue_does_not_clear_hard_failure` | E eligibility | S | PASS | UNAVAILABLE remains REJECTED; rent root verifies; no waiver flag | No new scenario applying rescue; marker alone does not test that journey |
| `PipelineChecks.test_risk_acknowledgement_and_budget_source` | G eligibility | S | PASS | Unacknowledged risk excluded; acknowledged enters; scenario0 budget; unknown acknowledgement rejected | No persisted evaluation-ID or human acknowledgement lifecycle |
| `PipelineChecks.test_stale_modified_and_missing_context_rejected` | Context | S | PASS | Changed scenario/network/project and singleton-only context rejected | Seal is an integrity digest, not an authentication mechanism |
| `PipelineChecks.test_unattainable_target_is_review_not_silent_clipping` | D/E feasibility | S | PASS | 27000 target against10000 wallet retained; achieved bounded; status REVIEW_REQUIRED | Does not independently assert portfolio exclusion of that site |
| `PortfolioChecks.test_all_1024_sets_and_independent_overlap_oracle` | G search | S | PASS | Enumerates1024 against brute force; interacting objective differs from sum of singles | Search oracle reuses supplied objective; not independent domain valuation |
| `PortfolioChecks.test_forced_cutoff_is_truthful` | G deadline | S+clock mock | PASS | Clock0→6 before first nonempty subset returns partial1 examined | No in-flight objective or final-subset overrun;R15–R16 expose gap |
| `PortfolioChecks.test_full_network_1024_sets_against_independent_cashflow_formula` | G exact network | O+S | PASS | All1024 subsets versus separate one-cell revenue/displacement cashflow oracle | Independent but1year/1cell; not empirical decision regret |
| `PortfolioChecks.test_paise_budget_ties_and_empty_zero` | G constraints | O+S | PASS | Half-up.105→11paise; stable ID; zero budget and negative objective select empty | Limited count/lower-CAPEX/fewer-stores tie boundaries |
| `TimingChecks.test_current_operational_cancelled_unknown_and_effect_signs` | F lifecycle | S | PASS | Positive/zero/negative multipliers; operational/cancelled no new uplift; unknown errors | Does not prove operational asset actually entered baseline |
| `TimingChecks.test_midyear_and_delay_fraction` | F dates | O | PASS | Leap-year206/366 fraction, later opening fractions, Feb29 month clamp | Supplies delayed date directly; bridge delay covered byR23 |
| `FinanceOracleTests.test_invalid_values_rejected` | D finance | S | PASS | Negative CAPEX, empty/NaN flows and discount−1 rejected | Not all numeric type/overflow cases |
| `FinanceOracleTests.test_prd_cashflow_oracle` | D finance | O | PASS | INR137236.03 / ROI.5 / payback3.3333 | Constant annual flows |
| `FinanceOracleTests.test_worked_sites_reverse_sales_order` | D finance reversal | O | PASS | PRD A−5837134 and B5895761.47; B>A | Finance-helper check, not ranking/network;R31 adds ranking proof |
| `FinanceOracleTests.test_zero_capex_and_no_recovery` | D finance | O | PASS | Zero CAPEX gives null ROI/zero payback; unrecovered gives null | No explicit terminal-value/tax model (excluded by specification) |

There are32 decision-engine tests plus4 finance tests. Every test method contains meaningful assertions; none was found vacuous or unconditionally skipped. Some assertions establish internal consistency/dependency rather than independent correctness: the synthetic objective search reuses its objective for brute force, the fitted boundary derives midpoint CAPEX from engine results, and the actual portfolio test checks feasibility/exact status without an independent ten-site optimum. These are useful limited tests, not empirical forecast validation.

Critical missing coverage includes applying rescues with non-unit existing multipliers, stale snapshot/model hard-block flags, objective overrun during a subset, lower infeasible sales bounds, recorded off exceptions, per-category contributions/source completeness, structured eligibility rule values, and actual official operational-asset reconciliation. No broad historical B/B.1/B.2 suite or new API/UI tests were run. Original stage-specific HEAD/pipeline-stub assertions remain preserved rather than silently rewritten. The prior API scaffold attempt is recorded as stalled/interrupted and remains **unverified**. A joblib/NumPy2.5 shape-assignment deprecation warning recurred; no numerical failure accompanied it.

## F. Offline end-to-end status

**Actual fitted route, verified:** read-only `build_project()` → saved B.2 estimator → prepared source inputs → `prepare_evaluation()` → calibration/network/finance/FailFast/ranking → `run_portfolio()`, with socket connections denied. No FastAPI server, frontend or SQLite is needed. All ten predictions and numerical NPVs are finite; source snapshots on actual cells/POIs align; identical inputs yield identical complete results and match saved baseline JSON exactly. The public computed fields validate against canonical EvaluationData/PortfolioResult after adding validation-only dummy identities, not a fabricated persisted API result.

**Numerical assumed fixtures:** R01–R19 and other synthetic boundaries are isolated review inputs with no observed sales and no genuine estimator provenance. They verify equations and expose contracts; they are not labelled successful fitted inference in this review.

**Fallback:** current C–G engine does not implement an assumption-mode evaluation path. It rejects mode scenario_assumptions and missing/unusable fitted records; the old inference adapter’s explicit fallback is a separate preserved capability, not used here. No fallback end-to-end success is claimed.

**Blocked paths:** missing usable prediction blocks the complete evaluation; unattainable calibrated targets remain explicit REVIEW_REQUIRED and are excluded; lack of trusted model readiness/feature identity may still be accepted if caller-supplied booleans/strings claim compatibility. All current actual sites are AT_RISK rather than automatically approved. Public API/UI/persistence and the Navi Mumbai scaffold’s required fitted-feature preparation remain unconnected.

The exact pipeline order is not a fresh geospatial feature build feeding inference: the loader feeds **frozen precomputed20-field features** to B.2; geodesic DaypartDNA is recomputed afterward for diagnostics. That preserves reproducibility and avoids double uplift but is a material qualification to “spatial→inference” completeness.

## G. Part B dependencies (no separate model re-verification)

The historical B.1 **PART_B_INTEGRATION_BLOCKED** verdict remains valid for its preserved v1 Ridge, not silently overturned. `ml/inference/reference_sales.py` still loads v1 with hardening warnings/automatic-integration block. The current offline loader explicitly imports `ReferenceSalesEstimatorV2` from the separate v2 adapter, loads CatBoost `reference-sales-sim-v2-438774e0a585`, and uses B.2’s **PART_B_READY_WITH_WARNINGS** output set. Its selected model SHA256 is `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`. No model was switched, weakened, tuned, retrained or replaced during review.

Saved B.2 metadata records a synthetic activation gate and OOD/test WAPE ratio4.357; all candidate warnings retain shifted-market review. Its own ablation does not demonstrate added Daypart predictive advantage. These are dependencies and reported historical evidence, not re-estimated metrics in this review. Synthetic support and feasible calibrated sales cannot establish real-outcome accuracy, commercial response validity, current costs or decision lift.

The v2 adapter returns `automatic_calibration_permitted=False` for all ten actual records. The domain nevertheless calibrates after checking usable target/joint_support_pass/hard_schema_compatible/mode/artifact ID; it does not consume that flag or an explicit integration_status hard block. Full calibration does independently test numerical reference feasibility, which is stronger than the preliminary endpoint status, but the semantic transition from “automatic calibration not permitted” to allowed C–G execution is not encoded. R18 demonstrates that a prepared record explicitly containing INTEGRATION_BLOCKED is accepted when the other fields are supplied. The current genuine v1 record does not supply the v2 required compatibility fields, so this is **not proof that v1 was actually run or that its block was removed**. Resolve/enforce the gate contract before automatic downstream integration; do not just change a flag to make it pass. Detailed model verification remains the next separate task.

## H. Prioritised problems and suggested fixes — none applied

| ID | Severity | File/function and root cause | Evidence / needed correction |
| --- | --- | --- | --- |
| H01 | HIGH | [backend/app/domain/engine.py:64](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:64>) and `calculate_rescue:215–230`: rent root is effective rent; sales root is relative to already-scaled target, while canonical overrides are pre-global-rent and absolute-baseline multipliers | R12/R13 solved→directly-applied negative NPV. Define typed effective/relative/absolute semantics; return normalized canonical override values (rent/global rent multiplier, relative sales×current sales multiplier), handle zero rent multiplier and enforce final allowed bounds. Verify fresh-scenario application with same engine and hard rules. |
| H02 | HIGH | [backend/app/domain/engine.py:84](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:84>): prepared model gate flags/provenance not enforced beyond a few fields | R18; actual v2 automatic_calibration_permitted=False. Agree explicit preliminary→fully calibrated readiness policy; honor hard integration blocks and artifact identity. Keep legacy v1 blocked pending its own qualification. |
| H03 | HIGH | [backend/app/domain/engine.py:48](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/engine.py:48>): no per-record snapshot/feature-to-prediction binding; string booleans accepted through truthiness | R17 mixed source snapshot accepted; R19 string"False" becomes supported coverage. Validate typed internal records, snapshot equality, prediction feature hashes/units and source revision before sealing context. Current genuine loaded snapshots do align (R26). |
| H04 | HIGH | [backend/app/domain/portfolio/search.py:30](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/portfolio/search.py:30>): clock checked only before objective | R15/R16 overrun hard budget; exact status still correct if all finished. Make valuation/search cancellation cooperative and bound worst-case in-flight work, or explicitly change approved deadline semantics. Preserve feasible incumbent and truthful examined counts. |
| H05 | MEDIUM | [backend/app/domain/failfast/rules.py:53](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/failfast/rules.py:53>): first infeasible lower point terminates with empty samples | R14 has valid root1.2 but reports unrecoverable. Locate the attainable interval within declared bounds before root search; distinguish lower/upper reference infeasibility. Sampling monotonicity remains only a tested-range claim. |
| H06 | MEDIUM | [ml/bengaluru/build.py:402](<C:/Users/Office Pc/OneDrive/Documents/Elites-/ml/bengaluru/build.py:402>): accepted `off` clause skips rather than clears prior schedule | R11 leaves540 Sunday minutes. Correct exception/override semantics or reject such syntax as unsupported; add independent weekday/weekend overnight/exception tests. No accepted current off expression was shown corrupted; do not rewrite frozen data during review. |
| H07 | MEDIUM | [backend/app/domain/geospatial/features.py:70](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/geospatial/features.py:70>) and `ml/decision_engine/report.py`: only weekly share, no category/bin explanations, partial per-profile source/coverage disclosure | R30 and source parsed-hours2.46–9.22%. Expose distinctly named raw-normalized and weekly shares, category contributions, parsed/assumed fractions and relevant source/assumption dates/IDs; carry them into the frozen decision report. SHAP is not required. |
| H08 | MEDIUM | [backend/app/domain/scenario/timing.py:37](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/scenario/timing.py:37>) and `ml/decision_engine/run.py:70–80`: operational state treated as already present; official ledger not loaded | R24 proves no duplicate uplift only. Reconcile verified operational assets with baseline features/POIs and preserve official source/status/date IDs; keep hypothetical event evidence separate. Current construction-tagged transit record affects none of ten catchments. |
| H09 | MEDIUM | [backend/app/domain/failfast/rules.py:7](<C:/Users/Office Pc/OneDrive/Documents/Elites-/backend/app/domain/failfast/rules.py:7>): reasons are generic strings; no consistent measured value/threshold/unit evidence for every rule | Financial values appear in strings; hard budget/location/model/coverage reasons lack complete tested values. Add private structured rule evidence and coordinate public exposure with backend owner. |
| H10 | HIGH interpretation limitation | `ml/decision_engine/run.py` source/price warnings: historical2020 population and nominal2023-24 wallet compared with synthetic2026 costs | Existing report correctly discloses mismatch; no consistent-price forecast is established. Obtain current compatible commercial inputs or an explicit documented price conversion before real investment interpretation. Do not invent inflation or labels. |
| H11 | LOW/UNVERIFIED gate | Public UNKNOWN enum, historical suite state, official-event lifecycle and full application checks | UNKNOWN has no producer; valid empty incumbent explains ordinary partial mode. Test intended failure contract separately. Full backend persistence/stale-response/UI/rehearsal gates remain open; do not claim broad suite or complete app acceptance. |

No CRITICAL core-mathematics defect was demonstrated. HIGH findings block an unqualified automatic-integration/readiness claim but do not prevent the current offline fitted route from executing. Extra-field/invalid-type findings describe a trusted-boundary validation gap, not a claim of malicious input or corrupted current source data.

## I. Completion checklist

- [x] Locate all claimed numerical implementations and36 tests; rerun without overwriting historical evidence.
- [x] Verify core spending conservation, reference-versus-network distinction, exactly-once lost contribution, finance oracle and independent tiny portfolio.
- [x] Verify actual ten-site offline v2 fitted run and saved-result reproduction; no assumption fallback substituted.
- [x] Verify six-bin proxy/weekly weights, overnight attribution, nonprobabilistic sensitivity, lifecycle fractions, ranking and risk-default policy within tested scope.
- [x] Preserve explicit model/source/business assumptions, raw predictions, calibration residuals and all original files.
- [ ] Normalize and verify applied rescue levers in scenarios with existing multipliers and feasibility-boundary cases.
- [ ] Resolve/enforce model integration flags, typed prepared inputs and snapshot/prediction-source identity checks before automatic integration.
- [ ] Meet or explicitly renegotiate the approved hard deadline; test in-flight cutoff.
- [ ] Complete Daypart category/share/coverage/source output and recorded-hours exception correctness.
- [ ] Reconcile operational-asset baseline and complete tested-value rule evidence.
- [ ] Perform the separate Part B verification, then backend/frontend/persistence integration under agreed contracts.
- [ ] Complete full-application acceptance: imports, atomic/stale handling, clean checkout, accessibility, rehearsals and specified performance/user/decision-regret gates. Real comparable outcome validation is unavailable, not fabricated.

## J. Git and file safety

Before review, a SHA256 baseline captured **364 existing project files**, including datasets, source snapshots, model artifacts, code, tests and prior reports. Excluded directories were `.git`, `.runtime`, node_modules, virtualenv/build/dependency caches; the new review report was excluded from comparison. All364 original file hashes match after review. Branch remains `ML` and HEAD remains `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`. Existing worktree changes predate this review; no clean-worktree claim is made. No commit, push, branch switch, merge, rebase or PR action was performed.

The only new non-temporary deliverable is `OFFLINE_ENGINE_REVIEW_REPORT.md`. Optional review evidence/scripts are isolated under `.runtime/offline-engine-review/` (ignored temporary directory); existing artifact-restoration tests also used temporary subdirectories under `.runtime/decision-engine-tests/`. No source/data/model/original report was edited. Existing writer entrypoints (`run`, `verify`, `report`, data builders and training scripts) were not invoked; only safe component functions/test runners were executed.

Temporary evidence: `baseline.json`, `existing_36_results.json`, `targeted_results.json`, `probes.py`, `extra_probes.py`, `write_report.py`. The audit timestamp is a review timestamp, not a source collection date. Source attributions/dates were taken from repository evidence, not invented or refreshed online.

**Final verdict: OFFLINE_ENGINE_VERIFIED_WITH_LIMITATIONS. Stop after review.**
