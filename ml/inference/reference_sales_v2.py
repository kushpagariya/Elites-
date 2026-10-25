"""Explicit B.2 estimator; preserves the blocked B/B.1 entrypoint unchanged."""
import json
import hashlib
from pathlib import Path
import joblib
import numpy as np
from sklearn.neighbors import NearestNeighbors
from ml.training.reference_sales.features import FEATURES,feature_frame,FeatureValidationError

ART=Path(__file__).resolve().parents[1]/'artifacts/reference_sales_v2'

class ReferenceSalesEstimatorV2:
    def __init__(self,artifact_dir=ART):
        self.artifact_dir=Path(artifact_dir);self.manifest=json.loads((self.artifact_dir/'manifest.json').read_text())
        for n,h in self.manifest['required_sha256'].items():
            p=self.artifact_dir/n
            if p.resolve().parent!=self.artifact_dir.resolve() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('Artifact path/hash mismatch')
        self.schema=json.loads((self.artifact_dir/'feature_schema.json').read_text());self.support=json.loads((self.artifact_dir/'support.json').read_text())
        self.model=joblib.load(self.artifact_dir/self.manifest['selected_file'])
        if self.schema['schema_version']!='reference-sales-features-v2' or self.schema['feature_allowlist']!=list(FEATURES) or list(self.model.features)!=self.schema['capture_features']:raise ValueError('Artifact schema mismatch')
        if 'annual_wallet_inr' in self.model.features:raise ValueError('Wallet leakage into capture model')
        self.neighbours={fmt:NearestNeighbors(n_neighbors=1).fit(g['design']) for fmt,g in self.support['groups'].items()}

    def predict(self,row,*,schema_version='reference-sales-features-v2',allow_csv_strings=False,reference_bracket=None):
        if schema_version!=self.schema['schema_version']:raise FeatureValidationError('Schema version mismatch')
        x=feature_frame([row],allowed_extra=self.schema['canonical_input_columns'],allow_csv_strings=allow_csv_strings)
        raw=float(self.model.predict(x)[0]);wallet=float(x.annual_wallet_inr.iloc[0]);fmt=x.store_format.iloc[0]
        design=self.model.preprocessor.transform(x[list(self.model.features)])
        distance=float(self.neighbours[fmt].kneighbors(design)[0][0,0]);threshold=self.support['groups'][fmt]['loo_distance_p99']
        joint=distance<=threshold;warnings=[];marginal=[]
        for f,b in self.support['training_numeric_ranges'].items():
            if x[f].iloc[0]<b['min'] or x[f].iloc[0]>b['max']:marginal.append(f)
        if marginal:warnings.append('MARGINAL_RANGE:'+','.join(marginal))
        if not joint:warnings.append('UNSUPPORTED_CAPTURE_FEATURE_COMBINATION')
        numeric=np.isfinite(raw) and 0<=raw<=wallet
        feasible=None
        if reference_bracket is not None:
            if len(reference_bracket)!=2 or not all(np.isfinite(v) and v>=0 for v in reference_bracket) or reference_bracket[1]<reference_bracket[0]:raise FeatureValidationError('Invalid INR reference endpoint bracket')
            feasible=reference_bracket[0]<=raw<=reference_bracket[1]
            if not feasible:warnings.append('OUTSIDE_SUPPLIED_REFERENCE_ENDPOINT_BRACKET')
        if not numeric:warnings.append('INVALID_RAW_NO_CLIPPING')
        if not self.manifest['activation_passed']:warnings.append('SYNTHETIC_ACTIVATION_GATE_FAILED')
        if self.manifest['test_ood_ratio']>2:warnings.append('SHIFTED_MARKET_DEGRADATION_REVIEW')
        usable=numeric and joint and self.manifest['activation_passed'] and feasible is not False
        return dict(raw_reference_annual_sales_inr=raw if np.isfinite(raw) else None,reference_annual_sales_inr=raw if usable else None,
            wallet_upper_bound_inr=wallet,capture_fraction=float(self.model.share(x)[0]),prediction_units='INR/year',method_mode='model_simulated',
            model_artifact_id=self.manifest['model_artifact_id'],hard_schema_compatible=True,marginal_range_violations=marginal,
            joint_support_pass=bool(joint),joint_distance=distance,joint_threshold=threshold,
            feasibility_status='PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION' if feasible else 'REFERENCE_CONTEXT_NOT_SUPPLIED' if feasible is None else 'REFERENCE_BRACKET_REJECTED',
            warnings=warnings,prediction_adjustment=dict(applied=False,rule='NONE_NO_POSTHOC_CLIPPING'),
            wallet_response_guarantee='EXACT_PROPORTIONAL_SCALING_FOR_FIXED_CAPTURE_FEATURES',
            automatic_calibration_permitted=False,uncertainty='NO_REAL_OUTCOME_VALIDATION_OR_CALIBRATED_CONFIDENCE')
