"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import WorkspaceNavigation from "./WorkspaceNavigation";
import { useWorkspace } from "@/lib/workspace";
import { money, methodLabel } from "@/lib/format";
import { compactMoney } from "@/lib/presentation";
import { ErrorNotice } from "./Feedback";
import BrandMark from "./BrandMark";
export default function WorkspaceShell({ children }: { children: ReactNode }) {
  const w = useWorkspace();
  return (
    <div className="workspace-frame">
      <aside className="workspace-sidebar">
        <Link className="workspace-brand" href="/" aria-label="StoreScout home">
          <BrandMark size={28} />
          StoreScout
        </Link>
        <p className="workspace-scope">Retail expansion workspace</p>
        <WorkspaceNavigation contentReady={!!w.project && !w.loading} />
        <div className="sidebar-note">
          <strong>Your next store, considered</strong>
          <p>
            Explore a location. Test the conditions. Decide where to invest.
          </p>
          <Link href="/">Back to overview</Link>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-topbar">
          <span>
            {w.project
              ? w.project.data.city + " / " + w.project.data.category
              : "Local demonstration"}
          </span>
          <span>{w.project?.data.source_status ?? "Source unavailable"}</span>
        </header>
        <main id="main-content" className="workspace-sheet">
          <div className="context-bar">
            <label>
              <span>Scenario</span>
              <select
                aria-label="Saved scenario"
                value={w.scenario?.scenario_id ?? ""}
                disabled={w.loading || !w.scenarios.length}
                onChange={(e) => w.selectScenario(e.target.value)}
              >
                {!w.scenarios.length && (
                  <option value="">
                    {w.loading ? "Loading scenarios…" : "No scenario available"}
                  </option>
                )}
                {w.scenarios.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>
            <div>
              <span>Budget · assumed</span>
              <strong title={money(w.scenario?.budget_inr)}>
                {compactMoney(w.scenario?.budget_inr)}
              </strong>
            </div>
            <div className="context-state" role="status">
              <span>
                {w.dirty
                  ? "Unsaved assumptions"
                  : w.current
                    ? "Analysis up to date"
                    : w.evaluation
                      ? "Previous results · refresh needed"
                      : "Ready to analyse"}
              </span>
              <button
                disabled={
                  !w.scenario || w.dirty || w.loading || w.busy || !!w.loadError
                }
                onClick={() => void w.evaluate()}
              >
                {w.operation === "evaluate" ? "Analysing…" : "Run analysis"}
              </button>
            </div>
          </div>
          {w.evaluation && (
            <div className="method-notice">
              <span>
                {w.evaluation
                  ? w.evaluation.data.method_mode === "scenario_assumptions"
                    ? "Assumption-based estimates · review the saved inputs."
                    : methodLabel(w.evaluation.data.method_mode)
                  : "Select a location, then run your saved scenario."}
              </span>
              <a href="#evidence-details">Technical Details</a>
            </div>
          )}
          {w.loading && (
            <p role="status" className="loading-state">
              Loading the saved demo project and scenarios…
            </p>
          )}
          <ErrorNotice error={w.loadError} retry={() => void w.load()} />
          {w.dirty && (
            <div className="message" role="status">
              Conditions changed. Save and analyse them before creating an
              investment plan or report.{" "}
              <Link href="/app/scenarios">Review changes</Link>
            </div>
          )}
          {w.evaluation && !w.current && !w.dirty && (
            <div className="message" role="status">
              Showing previous results from{" "}
              {w.evaluatedScenario?.name ?? w.evaluation.data.scenario_id}. They
              are not current for this selection.
            </div>
          )}
          <ErrorNotice error={w.error} />
          {w.notice && (
            <p className="message" role="status">
              {w.notice}
            </p>
          )}
          {children}
          <details className="identity-details" id="evidence-details">
            <summary>Data and analysis details</summary>
            <dl>
              <div>
                <dt>Project</dt>
                <dd>{w.project?.data.project_id ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>Scenario</dt>
                <dd>{w.scenario?.scenario_id ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>Displayed evaluation</dt>
                <dd>{w.evaluation?.data.evaluation_id ?? "Not computed"}</dd>
              </div>
              <div>
                <dt>Data version requested</dt>
                <dd>{w.featureSnapshotId}</dd>
              </div>
              <div>
                <dt>Fixture</dt>
                <dd>
                  {w.evaluation?.meta.fixture_id ??
                    w.project?.meta.fixture_id ??
                    "Unavailable"}
                </dd>
              </div>
              <div>
                <dt>Model reference</dt>
                <dd>
                  {w.evaluation?.data.model_artifact_id ??
                    "No model artifact available"}
                </dd>
              </div>
              <div>
                <dt>Method</dt>
                <dd>{w.evaluation?.data.method_mode ?? "No computation"}</dd>
              </div>
              <div>
                <dt>Saved at (UTC)</dt>
                <dd>{w.evaluation?.data.created_at_utc ?? "Not evaluated"}</dd>
              </div>
            </dl>
            {w.evaluation?.data.evidence && (
              <>
                <h3>Evidence and methods</h3>
                <p>
                  Valuation date: {w.evaluation.data.evidence.valuation_date}
                </p>
                <ul>
                  {w.evaluation.data.evidence.limitations.map((text, i) => (
                    <li key={i}>{text}</li>
                  ))}
                </ul>
                <pre className="report-preview">
                  {JSON.stringify(w.evaluation.data.evidence, null, 2)}
                </pre>
              </>
            )}
          </details>
        </main>
      </div>
    </div>
  );
}
