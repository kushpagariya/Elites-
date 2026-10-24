# Team implementation rules

Read docs/PRD.md, ARCHITECTURE.md, CONTRACT.md, FOUR_HOUR_PLAN.md and your docs/handoffs prompt before editing.

- Frontend owns frontend/. Logic owns backend/app/domain/, ml/ and tests/unit/. Backend owns app transport, schemas, repositories, services, contracts, shared fixtures and root configuration. Backend is the integration owner.
- One editor for shared schemas/fixtures/root config. Agree a contract change before producer/consumer work; backend regenerates OpenAPI and updates TypeScript consumers in the same integration increment.
- Use one baseline per handoff. Integrate small increments every 30-45 minutes. Do not overwrite another owner's files or force-push main. Teammates normally use task branches; integration owner merges to main. The initial setup itself was requested on main.
- Do not implement P1/P2 before the H4 path is connected. Preserve mandatory F01-F08 in the complete build. H4 is an initial prototype, not full PRD acceptance.
- Keep domain logic independent of HTTP/SQLite. Frontend never computes financial outputs. Backend never duplicates the financial or allocation engine.
- Tag synthetic inputs and assumption mode. Preserve INR/decimal units and scenario/evaluation identity. No hardcoded rankings or fake model predictions.
- Return an explicit unavailable/error state until a real computation is connected. Passing health checks is not proof of analytics.
- Before reporting done, run relevant checks and give files, commit, exact results, remaining stubs and next dependency. Never fabricate benchmark or model results.
- Do not add document release badges; technical contract/data/model identifiers are still required for reproducibility.
