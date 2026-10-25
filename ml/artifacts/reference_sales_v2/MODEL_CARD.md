# Reference-sales v2 model card

PART_B_READY_WITH_WARNINGS

Artifact: reference-sales-sim-v2-438774e0a585; selected catboost by validation only.

Mode: model_simulated. No empirical retail-sales accuracy or calibrated intervals. Uncapped conserved synthetic targets; 19 trained capture features exclude wallet, guaranteeing proportional wallet-only scaling. All ten unchanged Bengaluru rows supported under frozen empirical rules and preliminary assumed reference endpoints. OOD warning and no daypart-ablation advantage remain. No automatic calibration/investment permission.

Complete model/evaluation/source/assumption/selection/test details: PART_B2_CORRECTION_REPORT.md; metrics.json, ablation.json, source_evidence.json, selection_lock.json and test_results.json under ml/evaluation/reference_sales_v2/. Original versions remain unchanged.
