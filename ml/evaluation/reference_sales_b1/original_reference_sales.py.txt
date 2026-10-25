"""Reusable internal feature-dictionary adapter for Part B only."""
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import joblib

from ml.training.reference_sales.features import FEATURES, SCHEMA_VERSION, FeatureValidationError, feature_frame

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_DIR=ROOT/'ml/artifacts/reference_sales_v1'


class ModelUnavailableError(RuntimeError):
    pass


class ReferenceSalesEstimator:
    """Loads trusted local artifacts; callers supply prepared canonical features.

    This internal return is NOT SiteAnalysis or a public API schema. A raw
    Project/Site lacks catchment evidence and will raise a feature error.
    Missing/corrupt/unqualified artifacts raise an unavailable state unless the
    caller explicitly supplies an assumed capture fraction. Invalid source
    features are never repaired by switching to a fallback.
    """
    def __init__(self,artifact_dir=DEFAULT_ARTIFACT_DIR,*,assumption_capture_fraction=None):
        self.artifact_dir=Path(artifact_dir);self.model=None;self.manifest=None;self.schema=None;self.unavailable_reason=None
        if assumption_capture_fraction is not None:
            import math
            if isinstance(assumption_capture_fraction,bool) or not isinstance(assumption_capture_fraction,(int,float)) or not math.isfinite(assumption_capture_fraction) or not 0<=assumption_capture_fraction<=1:
                raise ValueError('Explicit fallback capture fraction must be finite and within [0,1]')
        self.fallback=assumption_capture_fraction
        try:
            self.manifest=json.loads((self.artifact_dir/'manifest.json').read_text(encoding='utf-8'))
            for name,expected in self.manifest['required_file_sha256'].items():
                file=self.artifact_dir/name
                if file.resolve().parent!=self.artifact_dir.resolve():raise ModelUnavailableError('Invalid artifact path')
                if hashlib.sha256(file.read_bytes()).hexdigest()!=expected:raise ModelUnavailableError('Artifact checksum mismatch: '+name)
            self.schema=json.loads((self.artifact_dir/'feature_schema.json').read_text(encoding='utf-8'))
            if self.schema['schema_version']!=SCHEMA_VERSION or self.schema['feature_allowlist']!=list(FEATURES):
                raise ModelUnavailableError('Saved feature schema is incompatible')
            if self.manifest['method_mode']!='model_simulated' or not self.manifest['activation_gate_passed']:
                raise ModelUnavailableError('Fitted artifact has not passed the simulated activation gate')
            self.model=joblib.load(self.artifact_dir/self.manifest['selected_model_file'])
            if list(self.model.features)!=list(FEATURES):raise ModelUnavailableError('Fitted feature order mismatch')
        except (OSError,ValueError,KeyError,ModelUnavailableError,ImportError,EOFError) as exc:
            self.unavailable_reason=type(exc).__name__+': '+str(exc)
            self.model=None
            if self.fallback is None:raise ModelUnavailableError(self.unavailable_reason) from exc

    def predict_many(self,rows:Sequence[Mapping],*,schema_version=SCHEMA_VERSION,allow_csv_strings=False):
        if schema_version!=SCHEMA_VERSION:raise FeatureValidationError('Caller schema version does not match trained schema')
        # Without an artifact, fallback accepts only the feature allowlist and
        # site_id context. It never infers a full canonical schema from inputs.
        allowed=self.schema['canonical_input_columns'] if self.schema else ['site_id']
        frame=feature_frame(rows,allowed_extra=allowed,allow_csv_strings=allow_csv_strings)
        if not len(frame):return []
        if self.model is None:values=frame['annual_wallet_inr'].to_numpy()*self.fallback
        else:values=self.model.predict(frame)
        results=[]
        for raw,(_,row),value in zip(rows,frame.iterrows(),values):
            diagnostics=[]
            if self.model is not None:
                for field,bounds in self.manifest['train_feature_ranges'].items():
                    if row[field]<bounds['min'] or row[field]>bounds['max']:diagnostics.append('OUTSIDE_TRAIN_RANGE:'+field)
                if self.manifest['ood_warning']:diagnostics.append('SHIFTED_MARKET_DEGRADATION_REQUIRES_REVIEW')
            else:diagnostics.append('MODEL_UNAVAILABLE:'+self.unavailable_reason)
            if row['competitor_count_1500m']==0:diagnostics.append('NO_MAPPED_COMPETITOR_NEAREST_DISTANCE_UNDEFINED')
            results.append(dict(reference_annual_sales_inr=float(value),
                method_mode='model_simulated' if self.model is not None else 'scenario_assumptions',
                model_artifact_id=self.manifest['model_artifact_id'] if self.model is not None else None,
                model_artifact_sha256=self.manifest['required_file_sha256'][self.manifest['selected_model_file']] if self.model is not None else None,
                feature_schema_version=SCHEMA_VERSION,target_definition='COMPETITORS_ONLY_REFERENCE_BEFORE_OWN_BRANCH_DISPLACEMENT',
                uncertainty_status='NOT_CALIBRATED_FOR_REAL_MARKETS',diagnostics=diagnostics,
                assumption_capture_fraction=self.fallback if self.model is None else None))
        return results

    def predict(self,row:Mapping,**kwargs):
        return self.predict_many([row],**kwargs)[0]
