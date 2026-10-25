"use client";
import { useState } from "react";
import { useWorkspace } from "@/lib/workspace";
import { money, percent } from "@/lib/format";
import {
  changePercent,
  changeMultiplier,
  compactMoney,
  reasonLabel, riskSummary,
} from "@/lib/presentation";
import StatusBadge from "@/components/StatusBadge";
import { ErrorNotice, Unavailable } from "@/components/Feedback";
import type { EvaluationData, Scenario, SiteOverride } from "@/lib/types";
const eventLabels = {
  current: "Today",
  opens: "Project Opens",
  delayed: "Project Delayed",
} as const;
const fieldValue = (v: number | null | undefined) =>
  v == null || !Number.isFinite(v) ? "" : v;
const number = (v: string) => (v === "" ? NaN : Number(v));
export default function Scenarios() {
  const w = useWorkspace();
  const [siteId, setSiteId] = useState(w.focusedSiteId ?? w.selection[0] ?? "");
  const [lever, setLever] = useState<"rent" | "sales">("rent");
  const [lower, setLower] = useState("");
  const [upper, setUpper] = useState("");
  const [before, setBefore] = useState<{
    scenario: Scenario;
    evaluation: EvaluationData;
  } | null>(null);
  const draft = w.draft;
  const site =
    w.project?.data.sites.find((s) => s.site_id === siteId) ??
    w.project?.data.sites[0];
  const analysis = w.current
    ? w.evaluation?.data.site_analyses.find((s) => s.site_id === site?.site_id)
    : undefined;
  const proposal =
    w.current &&
    w.rescueResult?.site_id === site?.site_id &&
    w.rescueResult?.lever === lever
      ? w.rescueResult
      : null;
  const hasAfter = Boolean(
    w.current &&
      before &&
      w.scenario?.base_scenario_id === before.scenario.scenario_id &&
      before.evaluation.evaluation_id !== w.evaluation?.data.evaluation_id,
  );
  const currentSnapshot =
    w.evaluation &&
    w.evaluatedScenario &&
    w.scenario &&
    w.evaluatedScenario.scenario_id === w.scenario.scenario_id
      ? { scenario: w.evaluatedScenario, evaluation: w.evaluation.data }
      : null;
  const displayBefore = w.dirty
    ? currentSnapshot
    : hasAfter
      ? before
      : currentSnapshot;
  const earlier = displayBefore?.evaluation.site_analyses.find(
    (s) => s.site_id === site?.site_id,
  );
  const override = (
    key: keyof SiteOverride,
    value: string,
    kind: "money" | "change",
  ) => {
    if (!draft || !site) return;
    const values = structuredClone(draft.assumptions.site_overrides);
    const next = { ...values[site.site_id] };
    if (value === "") delete next[key];
    else
      next[key] =
        kind === "change"
            ? changeMultiplier(Number(value))
            : Number(value);
    if (Object.keys(next).length) values[site.site_id] = next;
    else delete values[site.site_id];
    w.editAssumptions({ site_overrides: values });
  };
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Test Changes</h1>
          <p>What happens if business conditions change?</p>
        </div>
      </div>
      {!draft || !w.scenario ? (
        <Unavailable>
          {w.loading
            ? "Loading your saved assumptions…"
            : "Load a saved scenario to start testing changes."}
        </Unavailable>
      ) : (
        <div className="scenario-builder">
          <section
            className="scenario-input-panel"
            aria-labelledby="builder-heading"
          >
            <h2 id="builder-heading">Build a scenario</h2>
            <p>
              Change the conditions. Compare the new analysis with your saved
              starting point.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (w.evaluation && w.evaluatedScenario)
                  setBefore({
                    evaluation: w.evaluation.data,
                    scenario: w.evaluatedScenario,
                  });
                void w.saveAndEvaluate();
              }}
            >
              <label>
                Expansion budget (INR)
                <input
                  type="number"
                  required
                  min={0}
                  step="0.01"
                  value={fieldValue(draft.budget_inr)}
                  onChange={(e) =>
                    w.edit({ budget_inr: number(e.target.value) })
                  }
                />
              </label>
              {(
                [
                  ["demand_multiplier", "Customer demand change"],
                  ["rent_multiplier", "Rental cost change"],
                ] as const
              ).map(([key, label]) => (
                <div className="change-control" key={key}>
                  <label>
                    {label} (%)
                    <input
                      type="number"
                      required
                      min={-100}
                      max={200}
                      step="0.1"
                      value={fieldValue(changePercent(draft.assumptions[key]))}
                      onChange={(e) =>
                        w.editAssumptions({
                          [key]: changeMultiplier(number(e.target.value)),
                        })
                      }
                    />
                  </label>
                  <input
                    type="range"
                    aria-label={label + " slider"}
                    min={-100}
                    max={200}
                    step={1}
                    value={
                      Number.isFinite(draft.assumptions[key])
                        ? changePercent(draft.assumptions[key])
                        : 0
                    }
                    onChange={(e) =>
                      w.editAssumptions({
                        [key]: changeMultiplier(Number(e.target.value)),
                      })
                    }
                  />
                  <div className="range-labels">
                    <span>−100%</span>
                    <span>Unchanged: 0%</span>
                    <span>+200%</span>
                  </div>
                </div>
              ))}
              <fieldset className="infrastructure-choice">
                <legend>Future infrastructure</legend>
                <div
                  className="segmented"
                  role="group"
                  aria-label="Infrastructure scenario"
                >
                  {(["current", "opens", "delayed"] as const).map((state) => (
                    <button
                      key={state}
                      type="button"
                      aria-pressed={
                        draft.assumptions.infrastructure_state === state
                      }
                      onClick={() =>
                        w.editAssumptions({ infrastructure_state: state, ...(state !== "current" && draft.assumptions.infrastructure_effect_fraction === 0 ? {infrastructure_effect_fraction: w.infrastructure[0]?.assumed_effect_fraction ?? 0} : {}) })
                      }
                    >
                      {eventLabels[state]}
                    </button>
                  ))}
                </div>
                <p className="helper">
                  {draft.assumptions.infrastructure_state === "current"
                    ? "Future projects are excluded from today’s operating network."
                    : "A commercial assumption, not a confirmed sales uplift. Save to evaluate its effect."}
                </p>
              </fieldset>
              <details className="advanced-assumptions">
                <summary>Advanced Assumptions</summary>
                <div className="form-grid">
                  <label className="full-width">
                    Scenario name
                    <input
                      required
                      maxLength={100}
                      value={draft.name}
                      onChange={(e) => w.edit({ name: e.target.value })}
                    />
                  </label>
                </div>
                <h3>Individual-location overrides</h3>
                <label>
                  Location
                  <select
                    value={site?.site_id ?? ""}
                    onChange={(e) => {
                      setSiteId(e.target.value);
                      w.focusSite(e.target.value);
                    }}
                  >
                    {w.project?.data.sites.map((s) => (
                      <option key={s.site_id} value={s.site_id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="helper">
                  Blank fields inherit the scenario settings.{" "}
                  {Object.keys(draft.assumptions.site_overrides).length}{" "}
                  locations have overrides.
                </p>
                <div className="form-grid">
                  {(
                    [
                      [
                        "monthly_rent_inr",
                        "Monthly rent (INR)",
                        "money",
                        undefined,
                      ],
                      [
                        "sales_multiplier",
                        "Customer demand change (%)",
                        "change",
                        200,
                      ],
                    ] as const
                  ).map(([key, label, kind, max]) => {
                    const value = site
                      ? draft.assumptions.site_overrides[site.site_id]?.[key]
                      : null;
                    return (
                      <label key={key}>
                        {label}
                        <input
                          type="number"
                          min={kind === "change" ? -100 : 0}
                          max={max}
                          step="0.01"
                          value={fieldValue(
                            value == null
                              ? null
                              : kind === "change"
                                  ? changePercent(value)
                                  : value,
                          )}
                          onChange={(e) => override(key, e.target.value, kind)}
                          placeholder="Inherit scenario"
                        />
                      </label>
                    );
                  })}
                </div>
                <h3>Infrastructure timing &amp; effect</h3>
                <div className="form-grid">
                  <label>
                    Assumed opening date
                    <input
                      type="date"
                      value={draft.assumptions.opening_date ?? ""}
                      onChange={(e) =>
                        w.editAssumptions({
                          opening_date: e.target.value || null,
                        })
                      }
                    />
                  </label>
                  <label>
                    Delay (months)
                    <input
                      type="number"
                      required
                      min={0}
                      max={120}
                      step={1}
                      value={fieldValue(draft.assumptions.delay_months)}
                      onChange={(e) =>
                        w.editAssumptions({
                          delay_months: number(e.target.value),
                        })
                      }
                    />
                  </label>
                  <label>
                    Assumed commercial effect (%)
                    <input
                      type="number"
                      required
                      min={-100}
                      max={200}
                      step="0.1"
                      value={fieldValue(
                        draft.assumptions.infrastructure_effect_fraction * 100,
                      )}
                      onChange={(e) =>
                        w.editAssumptions({
                          infrastructure_effect_fraction:
                            number(e.target.value) / 100,
                        })
                      }
                    />
                  </label>
                </div>
                <p className="helper">
                  Default delay is 24 months. A blank date uses the event’s
                  labelled opening assumption. Effects depend on geographic
                  exposure and time within the saved projection horizon.
                </p>
              </details>
              <div className="form-actions">
                <button
                  type="submit"
                  disabled={w.busy || w.loading || !!w.loadError}
                >
                  {w.operation === "save"
                    ? "Saving…"
                    : w.operation === "evaluate"
                      ? "Analysing changes…"
                      : "Save & analyse changes"}
                </button>
                <button
                  className="secondary"
                  type="button"
                  disabled={w.busy}
                  onClick={() => w.selectScenario(w.scenario!.scenario_id)}
                >
                  Reset edits
                </button>
              </div>
              <p className="helper">
                Creates a new saved scenario. Your baseline stays unchanged.
              </p>
            </form>
          </section>
          <aside className="scenario-results">
            <section aria-labelledby="impact-heading">
              <h2 id="impact-heading">Before &amp; after</h2>
              <label>
                Location to review
                <select
                  value={site?.site_id ?? ""}
                  onChange={(e) => {
                    setSiteId(e.target.value);
                    w.focusSite(e.target.value);
                  }}
                >
                  {w.project?.data.sites.map((s) => (
                    <option key={s.site_id} value={s.site_id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="before-after">
                <div>
                  <strong>Starting point</strong>
                  <p>
                    Budget{" "}
                    {compactMoney(
                      displayBefore?.scenario.budget_inr ??
                        w.scenario.budget_inr,
                    )}
                  </p>
                  <p>
                    Demand{" "}
                    {changePercent(
                      (displayBefore?.scenario ?? w.scenario).assumptions
                        .demand_multiplier,
                    )}
                    %
                  </p>
                  <p>
                    Rent{" "}
                    {changePercent(
                      (before?.scenario ?? w.scenario).assumptions
                        .rent_multiplier,
                    )}
                    %
                  </p>
                  <p>
                    NPV{" "}
                    {compactMoney(
                      earlier?.npv_inr ??
                        (w.dirty
                          ? w.evaluation?.data.site_analyses.find(
                              (s) => s.site_id === site?.site_id,
                            )?.npv_inr
                          : undefined),
                    )}
                  </p>
                  {earlier && <StatusBadge status={earlier.failfast.status} />}
                </div>
                <div>
                  <strong>{hasAfter ? "New result" : "Proposed change"}</strong>
                  <p>Budget {compactMoney(draft.budget_inr)}</p>
                  <p>
                    Demand{" "}
                    {fieldValue(
                      changePercent(draft.assumptions.demand_multiplier),
                    )}
                    %
                  </p>
                  <p>
                    Rent{" "}
                    {fieldValue(
                      changePercent(draft.assumptions.rent_multiplier),
                    )}
                    %
                  </p>
                  <p>
                    NPV{" "}
                    {hasAfter
                      ? compactMoney(analysis?.npv_inr)
                      : "Awaiting analysis"}
                  </p>
                  {hasAfter && (
                    <StatusBadge status={analysis?.failfast.status} />
                  )}
                </div>
              </div>
              {hasAfter && w.evaluation?.data.rankings.length ? (
                <p className="helper">
                  Top locations now:{" "}
                  {w.evaluation.data.rankings
                    .slice(0, 3)
                    .map(
                      (id) =>
                        w.project?.data.sites.find((s) => s.site_id === id)
                          ?.name ?? id,
                    )
                    .join(", ")}
                  .
                </p>
              ) : (
                <p className="helper">
                  Save and analyse to see changes in value, rankings and
                  viability.
                </p>
              )}
            </section>
            <section className="risk-rescue" aria-labelledby="risk-heading">
              <div className="section-heading">
                <h2 id="risk-heading">FailFast · location health</h2>
                <StatusBadge status={analysis?.failfast.status} />
              </div>
              {analysis ? (
                <>
                  <p>{riskSummary(analysis.failfast.reasons)}</p>
                  {analysis.failfast.reasons.length ? (
                    <details><summary>All checks and evidence</summary><ul>
                      {analysis.failfast.reasons.map((r, i) => (
                        <li key={i}>{reasonLabel(r)}</li>
                      ))}
                    </ul></details>
                  ) : (
                    <p>No rules failed in the evaluated cases.</p>
                  )}
                </>
              ) : (
                <p>
                  Analyse a saved scenario to check financial and evidence
                  risks.
                </p>
              )}
              <h3>What could improve it?</h3>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (site)
                    void w.rescue(site.site_id, {
                      lever,
                      lower_bound: lever === "rent" ? 0 : lower === "" ? null : Number(lower),
                      upper_bound: upper === "" ? null : Number(upper),
                    });
                }}
              >
                <label>
                  What needs to improve?
                  <select
                    value={lever}
                    onChange={(e) => {
                      setLever(e.target.value as "rent" | "sales");
                      setLower("");
                      setUpper("");
                    }}
                  >
                    <option value="rent">
                      Find the maximum affordable rent
                    </option>
                    <option value="sales">
                      Find the minimum required sales
                    </option>
                  </select>
                </label>
                <details>
                  <summary>Search bounds</summary>
                  <div className="form-grid">
                    <label>
                      Lower bound
                      <input
                        type="number"
                        min={lever === "sales" ? 0.5 : 0}
                        readOnly={lever === "rent"}
                        max={lever === "sales" ? 3 : undefined}
                        step="0.01"
                        value={lever === "rent" ? "0" : lower}
                        onChange={(e) => setLower(e.target.value)}
                      />
                    </label>
                    <label>
                      Upper bound
                      <input
                        type="number"
                        min={
                          lower === ""
                            ? lever === "sales"
                              ? 0.5
                              : 0
                            : Number(lower)
                        }
                        max={lever === "sales" ? 3 : undefined}
                        step="0.01"
                        value={upper}
                        onChange={(e) => setUpper(e.target.value)}
                      />
                    </label>
                  </div>
                  <p className="helper">
                    Rent is base INR/month, before the global rent change. Sales search uses 0.5–3× the current target; the applied result is an absolute reference-sales multiplier.
                  </p>
                </details>
                <button
                  className="secondary"
                  type="submit"
                  disabled={!w.current || w.busy || !site}
                >
                  {w.operation === "rescue"
                    ? "Checking…"
                    : "Find an improvement"}
                </button>
              </form>
              {proposal && (
                <div className="rescue-result">
                  <strong>
                    {proposal.status === "SOLVED"
                      ? proposal.threshold_kind === "VIABLE_BOUND" ? "A viable setting was verified" : "Break-even setting verified"
                      : proposal.status === "NON_MONOTONIC"
                        ? "This relationship needs review"
                        : "No viable threshold in these bounds"}
                  </strong>
                  <p>{proposal.status === "SOLVED" ? proposal.threshold_kind === "VIABLE_BOUND" ? "This setting remains viable at the tested bound. It is not the zero-NPV break-even point." : "The engine verified this setting on a fresh copy of your scenario." : proposal.application_status === "BLOCKED_ZERO_RENT_MULTIPLIER" ? "Rent is already zero after the global adjustment. A finite base-rent threshold cannot be calculated." : proposal.application_status === "BLOCKED_ZERO_CURRENT_SALES_MULTIPLIER" ? "The current sales target is zero. Change that assumption before searching for a relative improvement." : "No setting within the checked range passed all required financial and eligibility checks."}</p>
                  {proposal.status === "SOLVED" &&
                    proposal.verified &&
                    proposal.threshold != null && (
                      <>
                        <p className="threshold-value">
                          {lever === "rent"
                            ? money(proposal.threshold) + " / month"
                            : proposal.threshold.toFixed(3) +
                              "× baseline reference sales"}
                        </p>
                        <button
                          type="button"
                          disabled={w.busy}
                          onClick={() =>
                            site && w.applyRescue(site.site_id, lever)
                          }
                        >
                          Try this change
                        </button>
                      </>
                    )}
                  <p className="helper">
                    Verified setting range:{" "}
                    {proposal.lower_bound.toLocaleString("en-IN")}–
                    {proposal.upper_bound.toLocaleString("en-IN")}.{" "}
                    {proposal.remaining_failed_rule_ids.length
                      ? "Other risks still apply. A new analysis will recheck every rule."
                      : "A new analysis is required before making an investment decision."}
                  </p>
                </div>
              )}
            </section>
            <section
              className="infrastructure-outlook"
              aria-labelledby="infra-heading"
            >
              <div className="section-heading">
                <h2 id="infra-heading">Infrastructure outlook</h2>
                <span className="quiet-tag">
                  {eventLabels[draft.assumptions.infrastructure_state]}
                </span>
              </div>
              <ErrorNotice error={w.infrastructureError} />
              {w.infrastructure.length ? (
                w.infrastructure.map((event) => (
                  <div
                    className="infrastructure-event"
                    key={event.infra_project_id}
                  >
                    <h3>{event.name}</h3>
                    <p className="helper">
                      {event.type?.replaceAll("_", " ") ?? "Infrastructure"} ·{" "}
                      {event.status.replaceAll("_", " ")} ·{" "}
                      {event.hypothetical_demo
                        ? "Assumed opening scenario"
                        : event.source_status}
                    </p>
                    {event.geometry_note && <p className="helper">{event.geometry_note}</p>}
                    <dl>
                      <div>
                        <dt>Opening date</dt>
                        <dd>
                          {draft.assumptions.opening_date ??
                            event.expected_open_date ??
                            event.assumed_demo_open_date ??
                            "Unknown"}
                          {(draft.assumptions.opening_date ||
                            !event.expected_open_date) &&
                            " · assumed"}
                        </dd>
                      </div>
                      <div>
                        <dt>Commercial effect</dt>
                        <dd>
                          {percent(
                            draft.assumptions.infrastructure_effect_fraction,
                          )}{" "}
                          · assumed
                        </dd>
                      </div>
                    </dl>
                  </div>
                ))
              ) : (
                <p className="helper">
                  No infrastructure project evidence is available.
                </p>
              )}
              {analysis?.infrastructure_exposure?.map((event) => (
                <div key={event.event_id}>
                  <p>
                    Exposure for {site?.name}:{" "}
                    <strong>{percent(event.exposure_fraction)}</strong>
                    {event.distance_m != null &&
                      " · " + event.distance_m.toFixed(0) + " m away"}
                    .
                  </p>
                  <div
                    className="event-timeline"
                    aria-label="Infrastructure active share by projection year"
                  >
                    {event.active_fractions.map((v, i) => (
                      <div key={i}>
                        <span>Year {i + 1}</span>
                        <meter
                          min={0}
                          max={1}
                          value={v}
                          aria-label={"Year " + (i + 1) + " active share"}
                        />
                        <small>{percent(v)}</small>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {w.current && w.evaluation && (
                <details>
                  <summary>Affected locations</summary>
                  <ul>
                    {w.evaluation.data.site_analyses
                      .filter((a) =>
                        a.infrastructure_exposure?.some(
                          (event) => event.exposure_fraction > 0,
                        ),
                      )
                      .map((a) => (
                        <li key={a.site_id}>
                          {w.project?.data.sites.find(
                            (s) => s.site_id === a.site_id,
                          )?.name ?? a.site_id}{" "}
                          ·{" "}
                          {a.infrastructure_exposure
                            ?.filter((event) => event.exposure_fraction > 0)
                            .map(
                              (event) =>
                                percent(event.exposure_fraction) +
                                " geographic exposure",
                            )
                            .join(", ")}
                        </li>
                      ))}
                  </ul>
                  <p className="helper">
                    Exposure is an assumed geographic relationship, not evidence
                    of measured sales uplift.
                  </p>
                </details>
              )}
              {w.dirty && (
                <p className="helper">
                  Timing shown above is a proposed assumption. Save to calculate
                  affected locations and financial impact.
                </p>
              )}
            </section>
          </aside>
        </div>
      )}
    </>
  );
}
