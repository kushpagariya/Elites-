"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import WorkspaceNavigation from "./WorkspaceNavigation";
import { useWorkspace } from "@/lib/workspace";
import { money, methodLabel } from "@/lib/format";
import { compactMoney } from "@/lib/presentation";
import { ErrorNotice } from "./Feedback";
import BrandMark from "./BrandMark";
import SignOut from "./SignOut";
export default function WorkspaceShell({ children }: { children: ReactNode }) {
  const w = useWorkspace();
  return (
    <div className="workspace-frame">
      <aside className="workspace-sidebar">
        <Link className="workspace-brand" href="/" aria-label="StoreScout home">
          <BrandMark size={28} />
          StoreScout
        </Link>
        <p className="workspace-scope">Bengaluru grocery planning prototype</p>
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
              : "Your workspace"}
          </span>
          <span>{w.project?.data.source_status ?? "Source unavailable"}</span>
          <SignOut/>
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
                {w.operation === 'evaluate'
                  ? 'Running analysis'
                  : w.dirty
                  ? "Unsaved assumptions"
                  : w.current
                    ? "Analysis up to date"
                    : w.evaluation
                      ? "Previous results · refresh needed"
                      : w.analyticsStatus === 'unavailable'
                        ? 'Analysis unavailable · retry'
                        : w.analyticsStatus === 'starting'
                          ? 'Analysis service starting'
                          : w.error ? 'Analysis failed · retry' : 'Ready to analyse'}
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
            </div>
          )}
          {w.loading && (
            <p role="status" className="loading-state">
              Loading your project and saved scenarios…
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
              Showing saved results from{" "}
              {w.evaluatedScenario?.name ?? w.evaluation.data.scenario_id}. They
              remain available for review and PDF export. Run analysis before calculating a new portfolio or rescue.
            </div>
          )}
          <ErrorNotice error={w.error} />
          {w.notice && (
            <p className="message" role="status">
              {w.notice}
            </p>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
