# StoreScout frontend scaffold

This Next.js App Router/TypeScript starter currently checks backend health and loads the labelled demo project. Product analytics and the three workflow screens remain implementation work; follow `../docs/handoffs/FRONTEND.md`.

```powershell
Copy-Item .env.example .env.local
pnpm install
pnpm dev
```

Use Node 22+. Local browser URL: `http://127.0.0.1:3000`. Start the backend separately as described in the repository README. `NEXT_PUBLIC_API_BASE_URL` includes `/api/v1` and defaults to `http://127.0.0.1:8000/api/v1`.

`pnpm typecheck` checks TypeScript; `pnpm build` builds the app. Registry access may be needed on the first installation. The generated pnpm lockfile is committed. Installation, TypeScript and a production build passed during scaffold verification; analytics remain unimplemented.

Next 16.4.3 and React 19.3.1 were checked against the official [Next registry](https://registry.npmjs.org/next/latest) and [React registry](https://registry.npmjs.org/react/latest) on 24 October 2026. Other dependencies use compatible ranges and need resolution by the package manager; no latest-version claim is made for them.

`src/lib/types.ts` mirrors implemented health/demo payloads and the planned scenario/evaluation/portfolio schemas in `backend/app/schemas.py`. Types do not establish that analytical routes work: those routes still return 501. Generate or update analytical types from backend OpenAPI after the team agrees `docs/CONTRACT.md`. The client keeps errors explicit.
