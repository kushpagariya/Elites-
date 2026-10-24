"use client";

import { useCallback, useEffect, useState } from "react";
import { getDemoProject, getHealth } from "@/lib/api";
import type { DemoProjectResponse, HealthResponse } from "@/lib/types";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [project, setProject] = useState<DemoProjectResponse | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [pending, setPending] = useState(true);

  const checkConnection = useCallback(async (signal?: AbortSignal) => {
    setPending(true);
    setErrors([]);
    const results = await Promise.allSettled([getHealth(signal), getDemoProject(signal)]);
    if (signal?.aborted) return;
    const [healthResult, projectResult] = results;
    setHealth(healthResult.status === "fulfilled" ? healthResult.value : null);
    setProject(projectResult.status === "fulfilled" ? projectResult.value : null);
    setErrors(results.flatMap((result) => result.status === "rejected"
      ? [result.reason instanceof Error ? result.reason.message : "The connection check failed."] : []));
    setPending(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void checkConnection(controller.signal);
    return () => controller.abort();
  }, [checkConnection]);

  return (
    <div className="shell">
      <header className="brand">StoreScout <span>Retail investment workspace</span></header>
      <main id="main-content">
        <div className="title-row">
          <div><h1>Connection check</h1><p>Connect the local services before building the investment workflow.</p></div>
          <button type="button" disabled={pending} onClick={() => void checkConnection()}>{pending ? "Checking…" : "Check again"}</button>
        </div>
        <section aria-labelledby="service-heading" aria-busy={pending}>
          <h2 id="service-heading">Local API</h2>
          <p role="status">{pending ? "Checking API and demo project…" : health ? "API responding. Analytical features are awaiting implementation." : "API unavailable."}</p>
          {errors.length > 0 && <ul className="error" role="alert">{[...new Set(errors)].map((error) => <li key={error}>{error}</li>)}</ul>}
        </section>
        <section aria-labelledby="project-heading">
          <h2 id="project-heading">Demo project</h2>
          {project ? <dl>
            <div><dt>City</dt><dd>{project.data.city}</dd></div>
            <div><dt>Category</dt><dd>{project.data.category}</dd></div>
            <div><dt>Candidate sites</dt><dd>{project.data.sites.length}</dd></div>
            <div><dt>Existing branches</dt><dd>{project.data.stores.length}</dd></div>
            <div><dt>Source status</dt><dd>{project.data.source_status}</dd></div>
          </dl> : <p>{pending ? "Loading project…" : "Start the backend, then check again to load the labelled fixture."}</p>}
        </section>
        <p className="note">This starter checks connectivity. The team handoffs define the Explore &amp; Compare, Scenario &amp; Rescue, and Portfolio &amp; Report screens.</p>
      </main>
    </div>
  );
}
