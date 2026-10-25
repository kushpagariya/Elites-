"""B.1 evidence guards; no fitting, clipping, allocation or model replacement."""
import hashlib
import json
from numbers import Real
from pathlib import Path
import numpy as np
from scipy.special import expit
from ml.training.reference_sales.features import FeatureValidationError

POLICY_DIR=Path(__file__).resolve().parents[1]/'artifacts/reference_sales_b1'


def load_policy(model_sha):
    manifest=json.loads((POLICY_DIR/'manifest.json').read_text(encoding='utf-8'))
    data=(POLICY_DIR/'support_policy.json').read_bytes()
    if hashlib.sha256(data).hexdigest()!=manifest['support_policy_sha256'] or model_sha!=manifest['base_model_sha256']:
        raise ValueError('B.1 support policy checksum/base-model mismatch')
    policy=json.loads(data)
    if policy['base_model_sha256']!=model_sha:raise ValueError('Policy references another model')
    policy['hardening_policy_id']=manifest['hardening_policy_id']
    return policy


def raw_predictions(model,frame):
    """Expose the saved output head BEFORE legacy np.clip, without refitting."""
    if model.name=='median':return model.estimator.predict(np.zeros((len(frame),1)))
    return expit(model.estimator.predict(model.transformer.transform(frame)))*frame['annual_wallet_inr'].to_numpy(float)


def ridge_wallet_elasticity(model,frame):
    if model is None or model.name!='ridge':return None
    names=list(model.transformer.get_feature_names_out())
    index=names.index('numeric__annual_wallet_inr')
    scaler=model.transformer.named_transformers_['numeric'].named_steps['scale']
    effective=float(model.estimator.coef_[index]/scaler.scale_[index])
    z=model.estimator.predict(model.transformer.transform(frame))
    w=frame['annual_wallet_inr'].to_numpy(float)
    # R=W*sigmoid(a+b*log1p(W)); elasticity=(W/R)*dR/dW.
    return 1+(1-expit(z))*effective*w/(1+w)


def joint_support_score(model,frame,policy):
    design=model.transformer.transform(frame)
    delta=design-np.asarray(policy['design_mean'])
    return np.einsum('ij,jk,ik->i',delta,np.asarray(policy['design_covariance_pinv']),delta)


def annotate(result,raw,wallet,*,elasticity=None,score=None,policy=None,reference_bound=None):
    if reference_bound is not None:
        if isinstance(reference_bound,(bool,np.bool_)) or not isinstance(reference_bound,Real) or not np.isfinite(reference_bound) or reference_bound<0:
            raise FeatureValidationError('Reference wallet bound must be finite, nonnegative INR/year')
        reference_bound=float(reference_bound)
    finite=bool(np.isfinite(raw));valid=finite and 0<=raw<=wallet
    reasons=[]
    if not valid:reasons.append('INVALID_RAW_PREDICTION_NO_CLIPPING')
    if reference_bound is not None and finite and raw>reference_bound:
        valid=False;reasons.append('EXCEEDS_SUPPLIED_REFERENCE_WALLET_BOUND_NO_CLIPPING')
    if elasticity is not None and elasticity < -1e-10:
        result['diagnostics'].append('NEGATIVE_LOCAL_WALLET_RESPONSE_REQUIRES_REVIEW')
    if policy and score is not None and score>policy['training_squared_distance_p99']:
        result['diagnostics'].append('OUTSIDE_TRAIN_JOINT_SUPPORT_EMPIRICAL_REVIEW')
    if policy:
        result['diagnostics'].extend('INTEGRATION_BLOCK:'+r for r in policy.get('integration_block_reasons',[]))
    result['diagnostics'].extend(reasons)
    result.update(raw_reference_annual_sales_inr=float(raw) if finite else None,
        raw_prediction_status='FINITE' if finite else str(raw),reference_annual_sales_inr=float(raw) if valid else None,
        prediction_units='INR/year',wallet_units='INR/year addressable category spending',
        wallet_price_basis='INHERITED_FROM_INPUT_WALLET_NO_CONVERSION',
        addressable_wallet_inr=float(wallet),capture_fraction=float(raw/wallet) if finite and wallet else None,
        numerical_and_wallet_bounds_valid=valid,prediction_adjustment=dict(applied=False,rule='NONE_VALUES_NEVER_CLIPPED_OR_REPAIRED'),
        reference_wallet_bound_inr=reference_bound,
        reference_allocation_feasibility='UNVERIFIED_REQUIRES_ALIGNED_CELLS_EXTERNAL_OUTSIDE_AND_THETA_BRACKET' if valid else 'FAILED_NECESSARY_BOUND',
        integration_status=('INTEGRATION_BLOCKED' if policy and policy.get('integration_block_reasons') else 'REVIEW_REQUIRED') if valid else 'UNAVAILABLE',usable_for_automatic_integration=False,
        wallet_local_elasticity=float(elasticity) if elasticity is not None else None,
        empirical_joint_support_squared_distance=float(score) if score is not None else None,
        support_warning_interpretation='EMPIRICAL_TRAINING_SUPPORT_NOT_CALIBRATED_PROBABILITY_OR_CONFIDENCE',
        hardening_policy_id=policy['hardening_policy_id'] if policy else None)
    return result
