"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useWorkspace } from "@/lib/workspace";
import { money } from "@/lib/format";
import { ErrorNotice } from "./Feedback";
const links = [
  ["/app", "Explore & Compare"],
  ["/app/scenarios", "Scenario & Rescue"],
  ["/app/portfolio", "Portfolio & Report"],
];
export default function WorkspaceShell({ children }: { children: ReactNode }) {
  const w = useWorkspace();
  const pathname = usePathname();
  return (
    <div className="workspace-frame">
      <aside className="workspace-sidebar">
        <Link className="workspace-brand" href="/" aria-label="StoreScout home">
          <svg aria-hidden="true" viewBox="0 0 32 36" width="25" height="28">
            <path d="M16 1 30 9v18l-14 8L2 27V9Z" fill="currentColor" />
            <path d="m9 13 7-4 7 4v10l-7 4-7-4Z" fill="var(--paper)" />
          </svg>
          StoreScout
        </Link>
        <p className="workspace-scope">Retail expansion workspace</p>
        <nav aria-label="Investment workflow">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              aria-current={pathname === href ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <strong>One investment case</strong>
          <p>
            Compare locations, test assumptions, then review the whole network.
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
              Saved scenario
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
              <span>Scenario budget · ASSUMED</span>
              <strong>{money(w.scenario?.budget_inr)}</strong>
            </div>
            <div className="context-state" role="status">
              <span>
                {w.dirty
                  ? "Unsaved assumptions"
                  : w.current
                    ? "Matching saved evaluation"
                    : w.evaluation
                      ? "Previous evaluation · stale"
                      : "Awaiting evaluation"}
              </span>
              <button
                disabled={
                  !w.scenario || w.dirty || w.loading || w.busy || !!w.loadError
                }
                onClick={() => void w.evaluate()}
              >
                {w.operation === "evaluate"
                  ? "Evaluating…"
                  : "Evaluate scenario"}
              </button>
            </div>
          </div>
          {w.loading && (
            <p role="status" className="loading-state">
              Loading the saved demo project and scenarios…
            </p>
          )}
          <ErrorNotice error={w.loadError} retry={() => void w.load()} />
          {w.dirty && (
            <div className="message" role="status">
              Assumptions changed. Previous results are stale. Save and evaluate
              before creating a portfolio or exporting a report.{" "}
              <Link href="/app/scenarios">Review changes</Link>
            </div>
          )}
          {w.evaluation && !w.current && !w.dirty && (
            <div className="message" role="status">
              Previous results are retained from{" "}
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
          <details className="identity-details">
            <summary>Evidence and computation identities</summary>
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
                <dt>Feature snapshot requested</dt>
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
                <dt>Model artifact</dt>
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
          </details>
        </main>
      </div>
    </div>
  );
}
