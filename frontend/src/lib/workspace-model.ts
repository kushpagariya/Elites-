import type {
  EvaluationData,
  PortfolioResult,
  Project,
  Scenario,
  ScenarioCreate,
} from "./types";

export const FEATURE_SNAPSHOT_ID = "bengaluru-features-20261024-v1";
export function scenarioDraft(s: Scenario): ScenarioCreate {
  return {
    base_scenario_id: s.scenario_id,
    name: s.name.slice(0, 100),
    budget_inr: s.budget_inr,
    assumptions: structuredClone(s.assumptions),
  };
}

/** Ignore object-key order and null inherited overrides when comparing saved inputs. */
export function sameScenarioInputs(draft: ScenarioCreate, saved: Scenario): boolean {
  const normalize = (a: Scenario['assumptions']) => ({...a, site_overrides:
    Object.fromEntries(Object.entries(a.site_overrides).sort(([a], [b]) => a.localeCompare(b)).map(([id, v]) =>
      [id, Object.fromEntries(Object.entries(v).filter(([, v]) => v != null).sort(([a], [b]) => a.localeCompare(b)))]).filter(([, v]) => Object.keys(v).length))});
  return draft.name === saved.name && draft.budget_inr === saved.budget_inr &&
    JSON.stringify(normalize(draft.assumptions)) === JSON.stringify(normalize(saved.assumptions));
}

export function delayedOpening(opening: string | null, months: number): string | null {
  if (!opening) return null;
  const [year, month, day] = opening.split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1 + months, 1));
  const last = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
  date.setUTCDate(Math.min(day, last));
  return date.toISOString().slice(0, 10);
}
export function matchesEvaluation(
  e: EvaluationData,
  scenarioId: string,
  project: Project,
): boolean {
  const expected = new Set(project.sites.map((s) => s.site_id));
  const actual = new Set(e.site_analyses.map((s) => s.site_id));
  return (
    e.project_id === project.project_id &&
    e.scenario_id === scenarioId &&
    e.site_analyses.length === expected.size &&
    actual.size === expected.size &&
    [...actual].every((id) => expected.has(id)) &&
    e.rankings.every((id) => actual.has(id)) &&
    (!e.evidence || e.evidence.feature_snapshot_id === FEATURE_SNAPSHOT_ID) &&
    (e.method_mode === "scenario_assumptions" || e.model_artifact_id !== null)
  );
}
export function matchesPortfolio(
  p: PortfolioResult,
  e: EvaluationData,
  max: number,
  ack: string[],
): boolean {
  return (
    p.evaluation_id === e.evaluation_id &&
    p.selected_site_ids.length <= max &&
    p.selected_site_ids.every((id) => {
      const site = e.site_analyses.find((s) => s.site_id === id);
      return (
        site &&
        (site.failfast.status === "VIABLE" ||
          (site.failfast.status === "AT_RISK" && ack.includes(id)))
      );
    })
  );
}
/** A revision changes on edits/selections as well as requests; abort alone is insufficient. */
export class RequestClock {
  private revision = 0;
  next() {
    return ++this.revision;
  }
  accepts(token: number) {
    return token === this.revision;
  }
}
export function isCurrentEvaluation(
  e: EvaluationData | null,
  scenarioId: string | undefined,
  dirty: boolean,
  busy: boolean,
): boolean {
  return !!e && e.scenario_id === scenarioId && !dirty && !busy;
}
