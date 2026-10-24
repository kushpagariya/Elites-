"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  loadProject,
  getScenarios,
  getInfrastructure,
  createScenario,
  evaluateScenario,
  optimisePortfolio,
  requestRescue,
  getDayparts,
  getSavedReport,
} from "./api";
import type {
  ApiEnvelope,
  Assumptions,
  EvaluationData,
  InfrastructureEvent,
  PortfolioResult,
  Project,
  Scenario,
  ScenarioCreate,
  RescueRequest,
} from "./types";
import {
  FEATURE_SNAPSHOT_ID,
  RequestClock,
  scenarioDraft,
  matchesEvaluation,
  matchesPortfolio,
  isCurrentEvaluation,
} from "./workspace-model";

export interface Failure {
  title: string;
  message: string;
  fields: string[];
}
export function failure(error: unknown): Failure {
  const e =
    error instanceof ApiError
      ? error
      : new ApiError(
          error instanceof Error
            ? error.message
            : "An unexpected error occurred.",
          500,
        );
  const title =
    e.status === 0
      ? "Connection unavailable"
      : e.status === 501
        ? "Computation not connected"
        : e.status === 422
          ? "Check your assumptions"
          : e.status === 409
            ? "Results need refreshing"
            : e.status === 404
              ? "Resource unavailable"
              : "Request failed";
  const details = e.details as
    | { error?: { details?: { field: string; reason: string }[] } }
    | undefined;
  return {
    title,
    message: e.message,
    fields:
      details?.error?.details?.map((d) => d.field + ": " + d.reason) ?? [],
  };
}
const SCENARIO_KEY = "storescout:demo:scenario";
function rememberScenario(id: string) {
  try {
    localStorage.setItem(SCENARIO_KEY, id);
  } catch {
    /* Storage may be disabled; server state remains authoritative. */
  }
}
function rememberedScenario() {
  try {
    return localStorage.getItem(SCENARIO_KEY);
  } catch {
    return null;
  }
}
type Operation =
  | "save"
  | "evaluate"
  | "portfolio"
  | "rescue"
  | "dayparts"
  | "report"
  | null;
function useWorkspaceState() {
  const [project, setProject] = useState<ApiEnvelope<Project> | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioId, setScenarioId] = useState("baseline");
  const [draft, setDraft] = useState<ScenarioCreate | null>(null);
  const [dirty, setDirty] = useState(false);
  const [evaluationFresh, setEvaluationFresh] = useState(false);
  const [evaluation, setEvaluation] =
    useState<ApiEnvelope<EvaluationData> | null>(null);
  const [evaluatedScenario, setEvaluatedScenario] = useState<Scenario | null>(
    null,
  );
  const [portfolio, setPortfolio] = useState<PortfolioResult | null>(null);
  const [infrastructure, setInfrastructure] = useState<InfrastructureEvent[]>(
    [],
  );
  const [infrastructureError, setInfrastructureError] =
    useState<Failure | null>(null);
  const [loadError, setLoadError] = useState<Failure | null>(null);
  const [error, setError] = useState<Failure | null>(null);
  const [loading, setLoading] = useState(true);
  const [operation, setOperation] = useState<Operation>(null);
  const [selection, setSelection] = useState<string[]>([]);
  const [maxStores, setMaxStores] = useState(2);
  const [acknowledged, setAcknowledged] = useState<string[]>([]);
  const [notice, setNotice] = useState("");
  const [report, setReport] = useState<{ text: string; type: string } | null>(
    null,
  );
  const clock = useRef(new RequestClock());
  const request = useRef<AbortController | null>(null);
  const loadClock = useRef(new RequestClock());
  const loadRequest = useRef<AbortController | null>(null);
  const scenario = scenarios.find((s) => s.scenario_id === scenarioId) ?? null;
  const current = isCurrentEvaluation(
    evaluation?.data ?? null,
    scenario?.scenario_id,
    dirty || !evaluationFresh,
    loading || !!loadError || operation === "save" || operation === "evaluate",
  );
  const busy = operation !== null;
  const invalidate = useCallback(() => {
    setEvaluationFresh(false);
    clock.current.next();
    request.current?.abort();
    setOperation(null);
    setPortfolio(null);
    setAcknowledged([]);
    setError(null);
    setReport(null);
    setNotice("");
  }, []);
  const begin = (op: Operation) => {
    request.current?.abort();
    const token = clock.current.next();
    const controller = new AbortController();
    request.current = controller;
    setOperation(op);
    setError(null);
    setNotice("");
    return { token, controller };
  };
  const finish = (token: number) => {
    if (clock.current.accepts(token)) setOperation(null);
  };
  const load = useCallback(async () => {
    loadRequest.current?.abort();
    const controller = new AbortController();
    loadRequest.current = controller;
    const token = loadClock.current.next();
    setLoading(true);
    setLoadError(null);
    invalidate();
    const [p, s, infra] = await Promise.allSettled([
      loadProject(controller.signal),
      getScenarios(controller.signal),
      getInfrastructure(controller.signal),
    ]);
    if (controller.signal.aborted || !loadClock.current.accepts(token)) return;
    if (p.status === "fulfilled") setProject(p.value);
    if (s.status === "fulfilled") {
      setScenarios(s.value.data);
      setScenarioId((old) => {
        const preferred = rememberedScenario() ?? old;
        return s.value.data.some((v) => v.scenario_id === preferred)
          ? preferred
          : (s.value.data[0]?.scenario_id ?? "baseline");
      });
    }
    if (p.status === "rejected" || s.status === "rejected")
      setLoadError(
        failure(
          p.status === "rejected"
            ? p.reason
            : s.status === "rejected"
              ? s.reason
              : new Error("Could not load the workspace."),
        ),
      );
    if (infra.status === "fulfilled") {
      setInfrastructure(infra.value.data);
      setInfrastructureError(null);
    } else setInfrastructureError(failure(infra.reason));
    setLoading(false);
  }, [invalidate]);
  useEffect(() => {
    void load();
    return () => {
      loadRequest.current?.abort();
      request.current?.abort();
      clock.current.next();
      loadClock.current.next();
    };
  }, [load]);
  useEffect(() => {
    if (scenario) setDraft(scenarioDraft(scenario));
  }, [scenario]);
  const selectScenario = (id: string) => {
    rememberScenario(id);
    invalidate();
    setDirty(false);
    setScenarioId(id);
    const next = scenarios.find((s) => s.scenario_id === id);
    if (next) setDraft(scenarioDraft(next));
  };
  const edit = (patch: Partial<ScenarioCreate>) => {
    invalidate();
    setDirty(true);
    setDraft((d) => (d ? { ...d, ...patch } : d));
  };
  const editAssumptions = (patch: Partial<Assumptions>) => {
    if (draft) edit({ assumptions: { ...draft.assumptions, ...patch } });
  };
  const commitEvaluation = (
    response: ApiEnvelope<EvaluationData>,
    s: Scenario,
    token: number,
  ) => {
    if (!clock.current.accepts(token)) return;
    if (
      !project ||
      !matchesEvaluation(response.data, s.scenario_id, project.data) ||
      response.meta.fixture_id !== project.meta.fixture_id ||
      (response.meta.scenario_id !== undefined &&
        response.meta.scenario_id !== s.scenario_id)
    )
      throw new ApiError(
        "The returned evaluation does not match this project and scenario. No results were applied.",
        409,
      );
    setEvaluation(response);
    setEvaluationFresh(true);
    setEvaluatedScenario(s);
    setDirty(false);
    setPortfolio(null);
    setReport(null);
    setAcknowledged([]);
    setNotice(
      "Saved evaluation loaded. Every result below uses this evaluation.",
    );
  };
  const evaluate = async () => {
    if (!scenario || dirty || loading || loadError) return;
    setEvaluationFresh(false);
    const { token, controller } = begin("evaluate");
    setPortfolio(null);
    setReport(null);
    setAcknowledged([]);
    try {
      const result = await evaluateScenario(
        scenario.scenario_id,
        controller.signal,
      );
      commitEvaluation(result, scenario, token);
    } catch (e) {
      if (clock.current.accepts(token) && !controller.signal.aborted)
        setError(failure(e));
    } finally {
      finish(token);
    }
  };
  const saveAndEvaluate = async (body: ScenarioCreate | null = draft) => {
    if (!body || !project || loadError || loading) return;
    const snapshot = structuredClone(body);
    let savedIdentity: string | null = null;
    const { token, controller } = begin("save");
    setPortfolio(null);
    setReport(null);
    setAcknowledged([]);
    try {
      const saved = await createScenario(snapshot, controller.signal);
      if (!clock.current.accepts(token) || controller.signal.aborted) return;
      if (
        saved.data.project_id !== project.data.project_id ||
        saved.data.base_scenario_id !== snapshot.base_scenario_id
      )
        throw new ApiError(
          "The saved scenario has an unexpected identity.",
          409,
        );
      savedIdentity = saved.data.scenario_id;
      rememberScenario(saved.data.scenario_id);
      setScenarios((old) => [
        ...old.filter((s) => s.scenario_id !== saved.data.scenario_id),
        saved.data,
      ]);
      setScenarioId(saved.data.scenario_id);
      setDraft(scenarioDraft(saved.data));
      setDirty(false);
      setOperation("evaluate");
      setNotice("Scenario saved. Requesting its evaluation…");
      const result = await evaluateScenario(
        saved.data.scenario_id,
        controller.signal,
      );
      commitEvaluation(result, saved.data, token);
    } catch (e) {
      if (clock.current.accepts(token) && !controller.signal.aborted) {
        setError(failure(e));
        if (savedIdentity)
          setNotice(
            "Scenario saved as " +
              savedIdentity +
              ". Its evaluation did not complete. You can retry evaluation without saving again.",
          );
      }
    } finally {
      finish(token);
    }
  };
  const toggleSite = (id: string) =>
    setSelection((old) =>
      old.includes(id)
        ? old.filter((v) => v !== id)
        : old.length < 2
          ? [...old, id]
          : old,
    );
  const changePortfolioInputs = (max: number, ack: string[]) => {
    clock.current.next();
    request.current?.abort();
    setOperation(null);
    setError(null);
    setPortfolio(null);
    setReport(null);
    setMaxStores(max);
    setAcknowledged(ack);
    setNotice("");
  };
  const optimise = async () => {
    if (!current || !evaluation || !scenario) return;
    const e = evaluation.data;
    const ack = [...acknowledged];
    const max = maxStores;
    const { token, controller } = begin("portfolio");
    setPortfolio(null);
    setReport(null);
    try {
      const result = await optimisePortfolio(
        {
          evaluation_id: e.evaluation_id,
          max_stores: max,
          acknowledged_risk_site_ids: ack,
        },
        controller.signal,
      );
      if (!clock.current.accepts(token)) return;
      if (
        !matchesPortfolio(result.data, e, max, ack) ||
        result.data.budget_used_inr > scenario.budget_inr
      )
        throw new ApiError(
          "The returned portfolio does not match the active evaluation, eligibility or budget. No plan was applied.",
          409,
        );
      setPortfolio(result.data);
      setNotice("Portfolio result loaded from the saved evaluation.");
    } catch (e) {
      if (clock.current.accepts(token) && !controller.signal.aborted)
        setError(failure(e));
    } finally {
      finish(token);
    }
  };
  const rescue = async (
    siteId: string,
    body: Omit<RescueRequest, "evaluation_id">,
  ) => {
    if (!current || !evaluation) return;
    const { token, controller } = begin("rescue");
    try {
      await requestRescue(
        siteId,
        { ...body, evaluation_id: evaluation.data.evaluation_id },
        controller.signal,
      );
      if (clock.current.accepts(token))
        setNotice(
          "A rescue response was received, but its verified result schema is not yet agreed. No assumptions have been changed.",
        );
    } catch (e) {
      if (clock.current.accepts(token) && !controller.signal.aborted)
        setError(failure(e));
    } finally {
      finish(token);
    }
  };
  const applyRescue = (siteId: string, lever: "rent" | "sales") => {
    if (!current || !evaluation || !scenario) return;
    const result = evaluation.data.site_analyses.find(
      (s) => s.site_id === siteId,
    )?.failfast;
    if (result?.rescue_status !== "SOLVED") return;
    const threshold =
      lever === "rent"
        ? result.max_viable_monthly_rent_inr
        : result.required_sales_multiplier;
    if (
      threshold === null ||
      !Number.isFinite(threshold) ||
      threshold < 0 ||
      (lever === "sales" && threshold > 3)
    )
      return;
    const override = {
      ...scenario.assumptions.site_overrides[siteId],
      ...(lever === "rent"
        ? { monthly_rent_inr: threshold }
        : { sales_multiplier: threshold }),
    };
    void saveAndEvaluate({
      base_scenario_id: scenario.scenario_id,
      name: "Rescue review — " + siteId,
      budget_inr: scenario.budget_inr,
      assumptions: {
        ...structuredClone(scenario.assumptions),
        site_overrides: {
          ...structuredClone(scenario.assumptions.site_overrides),
          [siteId]: override,
        },
      },
    });
  };
  const loadDayparts = async () => {
    if (!current || !evaluation) return;
    const { token, controller } = begin("dayparts");
    const results = await Promise.allSettled([
      getDayparts(
        evaluation.data.evaluation_id,
        "weekday_lunch",
        controller.signal,
      ),
      getDayparts(
        evaluation.data.evaluation_id,
        "weekend_evening",
        controller.signal,
      ),
    ]);
    if (!clock.current.accepts(token) || controller.signal.aborted) return;
    const rejected = results.find((r) => r.status === "rejected");
    if (rejected?.status === "rejected") setError(failure(rejected.reason));
    else
      setNotice(
        "Opportunity responses received. Profiles, support and dates await the agreed DaypartDNA schema; no proxy values have been inferred.",
      );
    finish(token);
  };
  const downloadReport = async () => {
    if (
      !current ||
      !evaluation ||
      !portfolio ||
      portfolio.evaluation_id !== evaluation.data.evaluation_id
    )
      return;
    const { token, controller } = begin("report");
    try {
      const result = await getSavedReport(
        evaluation.data.evaluation_id,
        portfolio.portfolio_run_id,
        controller.signal,
      );
      if (!clock.current.accepts(token)) return;
      const reopened = await result.blob.text();
      if (!clock.current.accepts(token)) return;
      const url = URL.createObjectURL(result.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        "storescout-" +
        evaluation.data.evaluation_id +
        (result.type.includes("html") ? ".html" : ".json");
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setReport({ text: reopened, type: result.type });
      setNotice(
        "Saved report downloaded. The preview reopens the downloaded content.",
      );
    } catch (e) {
      if (clock.current.accepts(token) && !controller.signal.aborted)
        setError(failure(e));
    } finally {
      finish(token);
    }
  };
  return {
    project,
    scenarios,
    scenario,
    draft,
    dirty,
    evaluation,
    evaluatedScenario,
    portfolio,
    infrastructure,
    infrastructureError,
    loadError,
    error,
    loading,
    operation,
    busy,
    selection,
    maxStores,
    acknowledged,
    notice,
    report,
    current,
    featureSnapshotId: FEATURE_SNAPSHOT_ID,
    load,
    selectScenario,
    edit,
    editAssumptions,
    evaluate,
    saveAndEvaluate,
    toggleSite,
    changePortfolioInputs,
    optimise,
    rescue,
    applyRescue,
    loadDayparts,
    downloadReport,
  };
}
type Workspace = ReturnType<typeof useWorkspaceState>;
const Context = createContext<Workspace | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const value = useWorkspaceState();
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useWorkspace() {
  const value = useContext(Context);
  if (!value) throw new Error("WorkspaceProvider is required");
  return value;
}
