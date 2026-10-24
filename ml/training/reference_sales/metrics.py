"""Executed metrics; WAPE is undefined for a zero actual-target denominator."""
import numpy as np


def regression_metrics(actual,predicted):
    y=np.asarray(actual,dtype=float);p=np.asarray(predicted,dtype=float)
    if y.shape!=p.shape or y.ndim!=1 or not len(y) or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Nonempty matching finite metric vectors required')
    error=np.abs(y-p);denominator=float(np.abs(y).sum())
    return dict(n=len(y),MAE_inr=float(error.mean()),RMSE_inr=float(np.sqrt(np.mean((y-p)**2))),
        WAPE=float(error.sum()/denominator) if denominator else None,
        absolute_error_sum_inr=float(error.sum()),absolute_actual_sum_inr=denominator,
        WAPE_undefined_reason=None if denominator else 'ZERO_ABSOLUTE_ACTUAL_TARGET_SUM')
