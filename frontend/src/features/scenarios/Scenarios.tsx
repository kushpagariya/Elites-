"use client";
import { useState } from "react";
import { useWorkspace } from "@/lib/workspace";
import { money, percent } from "@/lib/format";
import { ErrorNotice, Unavailable } from "@/components/Feedback";

export default function Scenarios() {
  const w = useWorkspace();
  const [siteId, setSiteId] = useState("");
  const [lever, setLever] = useState<"rent" | "sales">("rent");
  const [lower, setLower] = useState("");
  const [upper, setUpper] = useState("");
  const draft = w.draft;
  const site =
    w.project?.data.sites.find((s) => s.site_id === siteId) ??
    w.project?.data.sites[0];
  const diagnosis = w.current
    ? w.evaluation?.data.site_analyses.find((s) => s.site_id === site?.site_id)
        ?.failfast
    : undefined;
  const proposal =
    w.current &&
    w.rescueResult?.site_id === site?.site_id &&
    w.rescueResult?.lever === lever
      ? w.rescueResult
      : null;
  const threshold = proposal?.threshold;
  const analysis = w.current
    ? w.evaluation?.data.site_analyses.find((s) => s.site_id === site?.site_id)
    : null;
  const number = (v: string) => (v === "" ? NaN : Number(v));
  const fieldValue = (v: number | undefined | null) =>
    v == null || Number.isNaN(v) ? "" : v;
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Scenario &amp; Rescue</h1>
          <p>
            Test what must change. Preserve the baseline and recheck every rule.
          </p>
        </div>
      </div>
      {!draft || !w.scenario ? (
        <Unavailable>
          {w.loading
            ? "Loading saved assumptions…"
            : "Load the project and scenarios before editing assumptions."}
        </Unavailable>
      ) : (
        <div className="scenario-grid">
          <section aria-labelledby="assumptions-heading">
            <h2 id="assumptions-heading">New scenario assumptions</h2>
            <p>
              ASSUMED inputs · saving creates an immutable scenario before
              evaluation.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void w.saveAndEvaluate();
              }}
            >
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
                <label>
                  Budget (INR)
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
                <label>
                  Demand multiplier
                  <input
                    type="number"
                    required
                    min={0}
                    max={3}
                    step="0.01"
                    value={fieldValue(draft.assumptions.demand_multiplier)}
                    onChange={(e) =>
                      w.editAssumptions({
                        demand_multiplier: number(e.target.value),
                      })
                    }
                  />
                  <input
                    type="range"
                    aria-label="Demand multiplier slider"
                    min={0}
                    max={3}
                    step="0.01"
                    value={
                      Number.isFinite(draft.assumptions.demand_multiplier)
                        ? draft.assumptions.demand_multiplier
                        : 1
                    }
                    onChange={(e) =>
                      w.editAssumptions({
                        demand_multiplier: Number(e.target.value),
                      })
                    }
                  />
                  <small>1 keeps baseline demand; 1.2 means +20%.</small>
                </label>
                <label>
                  Rent multiplier
                  <input
                    type="number"
                    required
                    min={0}
                    max={3}
                    step="0.01"
                    value={fieldValue(draft.assumptions.rent_multiplier)}
                    onChange={(e) =>
                      w.editAssumptions({
                        rent_multiplier: number(e.target.value),
                      })
                    }
                  />
                  <input
                    type="range"
                    aria-label="Rent multiplier slider"
                    min={0}
                    max={3}
                    step="0.01"
                    value={
                      Number.isFinite(draft.assumptions.rent_multiplier)
                        ? draft.assumptions.rent_multiplier
                        : 1
                    }
                    onChange={(e) =>
                      w.editAssumptions({
                        rent_multiplier: Number(e.target.value),
                      })
                    }
                  />
                  <small>
                    1 keeps baseline rent; location overrides replace it.
                  </small>
                </label>
              </div>
              <fieldset>
                <legend>Infrastructure timing</legend>
                <p className="helper">
                  Hypothetical demonstration event. A future opening is not an
                  operational asset.
                </p>
                <label>
                  Infrastructure state
                  <select
                    value={draft.assumptions.infrastructure_state}
                    onChange={(e) =>
                      w.editAssumptions({
                        infrastructure_state: e.target.value as
                          | "current"
                          | "opens"
                          | "delayed",
                      })
                    }
                  >
                    <option value="current">Current</option>
                    <option value="opens">Opens</option>
                    <option value="delayed">Delayed</option>
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Assumed opening date
                    <input
                      type="date"
                      required={
                        draft.assumptions.infrastructure_state !== "current"
                      }
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
                    <small>24 months is the demonstration delay.</small>
                  </label>
                  <label>
                    Commercial effect (decimal fraction)
                    <input
                      type="number"
                      required
                      min={-1}
                      max={2}
                      step="0.01"
                      value={fieldValue(
                        draft.assumptions.infrastructure_effect_fraction,
                      )}
                      onChange={(e) =>
                        w.editAssumptions({
                          infrastructure_effect_fraction: number(
                            e.target.value,
                          ),
                        })
                      }
                    />
                    <small>
                      0 is no commercial change; 0.1 is +10%. This is an
                      assumption.
                    </small>
                  </label>
                </div>
              </fieldset>
              <fieldset>
                <legend>Site-specific overrides</legend>
                <p className="helper">
                  Blank preserves no override. Existing saved overrides are
                  copied with the complete assumption snapshot.
                </p>
                <div
                  className="table-scroll"
                  tabIndex={0}
                  role="region"
                  aria-label="Site assumption overrides"
                >
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Candidate</th>
                        <th scope="col">Rent (INR/month)</th>
                        <th scope="col">Sales multiplier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {w.project?.data.sites.map((s) => (
                        <tr key={s.site_id}>
                          <th scope="row">{s.name}</th>
                          {(
                            ["monthly_rent_inr", "sales_multiplier"] as const
                          ).map((key) => (
                            <td key={key}>
                              <input
                                type="number"
                                aria-label={
                                  s.name +
                                  (key === "monthly_rent_inr"
                                    ? " rent override (INR/month)"
                                    : " sales multiplier override")
                                }
                                min={0}
                                max={key === "sales_multiplier" ? 3 : undefined}
                                step="0.01"
                                value={fieldValue(
                                  draft.assumptions.site_overrides[s.site_id]?.[
                                    key
                                  ],
                                )}
                                onChange={(e) => {
                                  const overrides = structuredClone(
                                    draft.assumptions.site_overrides,
                                  );
                                  const next = { ...overrides[s.site_id] };
                                  if (e.target.value === "") delete next[key];
                                  else next[key] = Number(e.target.value);
                                  if (Object.keys(next).length)
                                    overrides[s.site_id] = next;
                                  else delete overrides[s.site_id];
                                  w.editAssumptions({
                                    site_overrides: overrides,
                                  });
                                }}
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </fieldset>
              <fieldset>
                <legend>Margin, operating cost and competition</legend>
                <p className="helper">
                  ASSUMED commercial inputs. Operating costs exclude rent and
                  cost of goods. A location override replaces its global
                  setting.
                </p>
                <div className="form-grid">
                  <label>
                    Gross margin (fraction, 0–1)
                    <input
                      type="number"
                      min={0}
                      max={1}
                      step="0.01"
                      value={fieldValue(
                        draft.assumptions.gross_margin_fraction,
                      )}
                      placeholder="Keep each site's margin"
                      onChange={(e) =>
                        w.editAssumptions({
                          gross_margin_fraction:
                            e.target.value === ""
                              ? null
                              : Number(e.target.value),
                        })
                      }
                    />
                  </label>
                  <label>
                    Operating cost multiplier
                    <input
                      type="number"
                      required
                      min={0}
                      max={3}
                      step="0.01"
                      value={fieldValue(
                        draft.assumptions.operating_cost_multiplier ?? 1,
                      )}
                      onChange={(e) =>
                        w.editAssumptions({
                          operating_cost_multiplier: number(e.target.value),
                        })
                      }
                    />
                  </label>
                  <label>
                    Competition multiplier
                    <input
                      type="number"
                      required
                      min={0}
                      max={3}
                      step="0.01"
                      value={fieldValue(
                        draft.assumptions.competition_multiplier ?? 1,
                      )}
                      onChange={(e) =>
                        w.editAssumptions({
                          competition_multiplier: number(e.target.value),
                        })
                      }
                    />
                    <small>
                      Assumed competitive pressure; 1 keeps the baseline.
                    </small>
                  </label>
                </div>
                <details>
                  <summary>Additional location adjustments</summary>
                  <label>
                    Location
                    <select
                      value={site?.site_id ?? ""}
                      onChange={(e) => setSiteId(e.target.value)}
                    >
                      {w.project?.data.sites.map((s) => (
                        <option key={s.site_id} value={s.site_id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-grid">
                    {(
                      [
                        [
                          "gross_margin_fraction",
                          "Gross margin (fraction, 0–1)",
                          1,
                        ],
                        [
                          "annual_opex_inr",
                          "Annual operating cost (INR)",
                          undefined,
                        ],
                        [
                          "competition_multiplier",
                          "Local competition multiplier",
                          3,
                        ],
                      ] as const
                    ).map(([key, label, max]) => (
                      <label key={key}>
                        {label}
                        <input
                          type="number"
                          min={0}
                          max={max}
                          step="0.01"
                          value={fieldValue(
                            site
                              ? draft.assumptions.site_overrides[
                                  site.site_id
                                ]?.[key]
                              : undefined,
                          )}
                          placeholder="Inherit global setting"
                          onChange={(e) => {
                            if (!site) return;
                            const overrides = structuredClone(
                              draft.assumptions.site_overrides,
                            );
                            const next = { ...overrides[site.site_id] };
                            if (e.target.value === "") delete next[key];
                            else next[key] = Number(e.target.value);
                            overrides[site.site_id] = next;
                            w.editAssumptions({ site_overrides: overrides });
                          }}
                        />
                      </label>
                    ))}
                  </div>
                </details>
              </fieldset>
              <div className="before-after">
                <div>
                  <strong>Saved assumptions</strong>
                  <p>
                    Demand {w.scenario.assumptions.demand_multiplier}× · rent{" "}
                    {w.scenario.assumptions.rent_multiplier}×
                  </p>
                  <p>Budget {money(w.scenario.budget_inr)}</p>
                </div>
                <div>
                  <strong>Proposed assumptions</strong>
                  <p>
                    Demand {fieldValue(draft.assumptions.demand_multiplier)}× ·
                    rent {fieldValue(draft.assumptions.rent_multiplier)}×
                  </p>
                  <p>Budget {money(draft.budget_inr)}</p>
                </div>
              </div>
              <div className="form-actions">
                <button
                  type="submit"
                  disabled={w.busy || w.loading || !!w.loadError}
                >
                  {w.operation === "save"
                    ? "Saving scenario…"
                    : w.operation === "evaluate"
                      ? "Evaluating saved scenario…"
                      : "Save new scenario & evaluate"}
                </button>
                <button
                  className="secondary"
                  type="button"
                  disabled={w.busy}
                  onClick={() => w.selectScenario(w.scenario!.scenario_id)}
                >
                  Discard edits
                </button>
              </div>
            </form>
          </section>
          <div className="scenario-aside">
            <section aria-labelledby="event-heading">
              <h2 id="event-heading">Event evidence</h2>
              <ErrorNotice error={w.infrastructureError} />
              {w.infrastructure.length
                ? w.infrastructure.map((event) => (
                    <div key={event.infra_project_id}>
                      <h3>{event.name}</h3>
                      <p>
                        {event.hypothetical_demo ? "HYPOTHETICAL · " : ""}
                        {event.source_status} · {event.status}
                      </p>
                      <dl>
                        <div>
                          <dt>Verified opening date</dt>
                          <dd>{event.expected_open_date ?? "Unknown"}</dd>
                        </div>
                        <div>
                          <dt>Assumed demo opening</dt>
                          <dd>
                            {event.assumed_demo_open_date ?? "Not supplied"}
                          </dd>
                        </div>
                        <div>
                          <dt>Source</dt>
                          <dd>{event.source_id}</dd>
                        </div>
                      </dl>
                    </div>
                  ))
                : !w.infrastructureError && (
                    <Unavailable>No event evidence was returned.</Unavailable>
                  )}
            </section>
            <section aria-labelledby="rescue-heading">
              <h2 id="rescue-heading">FailFast recovery</h2>
              <p>
                Request a bounded rent or sales threshold. A financial recovery
                never waives unrelated failures.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (site)
                    void w.rescue(site.site_id, {
                      lever,
                      lower_bound: lower === "" ? null : Number(lower),
                      upper_bound: upper === "" ? null : Number(upper),
                    });
                }}
              >
                <label>
                  Candidate site
                  <select
                    value={site?.site_id ?? ""}
                    onChange={(e) => setSiteId(e.target.value)}
                  >
                    {w.project?.data.sites.map((s) => (
                      <option key={s.site_id} value={s.site_id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Recovery lever
                  <select
                    value={lever}
                    onChange={(e) => {
                      setLever(e.target.value as "rent" | "sales");
                      setLower("");
                      setUpper("");
                    }}
                  >
                    <option value="rent">
                      Maximum viable rent (INR/month)
                    </option>
                    <option value="sales">Minimum sales multiplier</option>
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Lower search bound
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      value={lower}
                      onChange={(e) => setLower(e.target.value)}
                    />
                  </label>
                  <label>
                    Upper search bound
                    <input
                      type="number"
                      min={lower === "" ? 0 : Number(lower)}
                      max={lever === "sales" ? 3 : undefined}
                      step="0.01"
                      value={upper}
                      onChange={(e) => setUpper(e.target.value)}
                    />
                  </label>
                </div>
                <p className="helper">
                  Blank bounds use the saved search policy: sales 0.5–3×; rent
                  starts at zero with a bounded upper limit. The returned bounds
                  are shown with the result.
                </p>
                <button type="submit" disabled={!w.current || w.busy || !site}>
                  {w.operation === "rescue"
                    ? "Requesting threshold…"
                    : "Request rescue threshold"}
                </button>
              </form>
              {diagnosis ? (
                <div className="rescue-result">
                  <p>
                    <strong>{diagnosis.status}</strong>
                  </p>
                  {proposal && (
                    <>
                      <p>
                        Recovery:{" "}
                        {proposal.status.replaceAll("_", " ").toLowerCase()}
                      </p>
                      <p>
                        Search bounds:{" "}
                        {proposal.lower_bound.toLocaleString("en-IN")} –{" "}
                        {proposal.upper_bound.toLocaleString("en-IN")}{" "}
                        {lever === "rent" ? "INR/month" : "× sales"}
                      </p>
                      <ul>
                        {proposal.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                      {proposal.remaining_failed_rule_ids.length > 0 && (
                        <p>
                          Other rules still need review:{" "}
                          {proposal.remaining_failed_rule_ids.join(", ")}
                        </p>
                      )}
                    </>
                  )}
                  {diagnosis.failed_rule_ids.length > 0 && (
                    <p>Failed rules: {diagnosis.failed_rule_ids.join(", ")}</p>
                  )}
                  {diagnosis.reasons.length > 0 && (
                    <ul>
                      {diagnosis.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                  {proposal?.status === "NOT_RECOVERABLE_WITHIN_BOUNDS" && (
                    <p>No recovery was found within the supplied bounds.</p>
                  )}
                  {proposal?.status === "NON_MONOTONIC" && (
                    <p>
                      A monotonic threshold could not be verified. Review the
                      scenario before applying changes.
                    </p>
                  )}
                  {proposal?.status === "SOLVED" &&
                    proposal.verified &&
                    threshold != null && (
                      <>
                        <p>
                          Verified{" "}
                          {lever === "rent"
                            ? "rent threshold: " + money(threshold) + "/month"
                            : "sales multiplier: " + threshold + "×"}
                        </p>
                        <button
                          className="secondary"
                          disabled={w.busy}
                          onClick={() =>
                            site && w.applyRescue(site.site_id, lever)
                          }
                        >
                          Apply verified threshold in a new scenario
                        </button>
                      </>
                    )}
                </div>
              ) : (
                <Unavailable>
                  A matching saved evaluation is required to show rule failures
                  and verified rescue thresholds.
                </Unavailable>
              )}
              {analysis?.infrastructure_exposure?.length ? (
                <details>
                  <summary>Infrastructure exposure for {site?.name}</summary>
                  {analysis.infrastructure_exposure.map((event) => (
                    <div key={event.event_id}>
                      <p>
                        {event.hypothetical ? "HYPOTHETICAL · " : ""}Geographic
                        exposure {percent(event.exposure_fraction)} · distance{" "}
                        {event.distance_m == null
                          ? "Unknown"
                          : event.distance_m.toFixed(0) + " m"}
                      </p>
                      <p>
                        Opening: {event.opening_date ?? "Unknown"} · assumed
                        commercial effect{" "}
                        {percent(event.assumed_effect_fraction)}
                      </p>
                      <p>
                        Active share by projection year:{" "}
                        {event.active_fractions
                          .map((v) => percent(v))
                          .join(" / ")}
                      </p>
                    </div>
                  ))}
                </details>
              ) : null}
            </section>
          </div>
        </div>
      )}
    </>
  );
}
