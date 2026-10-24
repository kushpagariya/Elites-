# Demand model work area

Owned by the logic/ML person. Required subfolders: `training/`, `evaluation/`,
`artifacts/`. Commit the generator, seed, fitted local artifact, feature schema,
artifact SHA-256 and measured model card. This starter contains no fitted model.

By H4, fit and use an actual regularised linear baseline locally; CatBoost follows
if it improves supported held-out performance. No hardcoded predictions or
assumption-only output may be presented as trained inference.

The PRD target is competitors-only reference annual sales, before own-company
branches. Generate at least 100 markets x 20 potential stores, with bounded cell
wallets, external competitors, heterogeneous gravity parameters and observation
noise. Exclude the showcase sites. Freeze market-grouped 60/20/20 partitions;
fit preprocessing on training only. Generate 20 separate shifted markets for OOD
evaluation and never use them for tuning. Exclude own-branch features, site IDs,
desired ranks and post-opening outcomes.

Record median, fitted linear and CatBoost comparisons; MAE/RMSE/WAPE, counts,
latency, segments, DaypartDNA ablation and shifted-market errors. WAPE is undefined
when actual-sales denominator is zero. Activation requires >=10% relative test
WAPE gain over median; failure stays visible and blocks the AI-ready claim.
OOD WAPE >2x regular test WAPE warns and requires review for matching regimes.

Synthetic results demonstrate learning under the generator. They do not validate
real-market forecasts. Mode is `model_simulated`; missing artifact switches to
visible `scenario_assumptions` and fails the model gate. No inference-time network
access, external LLM or paid dataset is required.
