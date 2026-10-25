# Integration status

`full-integration` connects the frontend/backend baseline and latest supplied ML engine.

Current product refinements verified: 87 Python checks; 31 frontend behavior checks; TypeScript; production build; 11 actual Chrome desktop/mobile checkpoints; live frontend adapters for all infrastructure states, source geography, rescue/apply, exact portfolios, named PDF download/preview and sign-in restoration. Details and limits: [product verification](PRODUCT_READINESS_VERIFICATION.md).

Baseline financial values and rankings match the delivered engine exactly. Selected CatBoost SHA-256: `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`.

Browser acceptance and final checks are recorded in `FULL_INTEGRATION_VERIFICATION.md`. Read `README.md` for setup and `FULL_INTEGRATION.md` for architecture and account storage.

The model uses synthetic labels. The website retains historical source, financial and infrastructure assumptions. It does not claim real-sales accuracy, calibrated confidence or automatic investment approval. Numerical outputs are computed by the supplied engine; unsupported controls and placeholder scores were removed.
