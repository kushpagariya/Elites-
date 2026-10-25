"""Explicit rule precedence and inverse economics on the same numerical engine."""
import numpy as np


def diagnose(npv, downside_npv, *, hard_reasons=(), review_reasons=(), warnings=()):
    rules = []
    for prefix, reasons in [('HARD', hard_reasons), ('REVIEW', review_reasons), ('EVIDENCE', warnings)]:
        for reason in reasons:
            rules.append(dict(rule_id=f'{prefix}:{reason}', passed=False, reason=reason))
    rules.extend([dict(rule_id='BASE_NPV', passed=npv >= 0, reason=f'Base incremental NPV INR {npv:.2f}'),
                  dict(rule_id='DOWNSIDE_NPV', passed=downside_npv >= 0, reason=f'Downside incremental NPV INR {downside_npv:.2f}')])
    status = ('REJECTED' if hard_reasons else 'REVIEW_REQUIRED' if review_reasons else
              'REJECTED' if npv < 0 else 'AT_RISK' if downside_npv < 0 or warnings else 'VIABLE')
    public = dict(status=status, failed_rule_ids=[r['rule_id'] for r in rules if not r['passed']],
                  reasons=[r['reason'] for r in rules if not r['passed']],
                  max_viable_monthly_rent_inr=None, required_sales_multiplier=None, rescue_status='NOT_REQUESTED')
    return public, rules


def rent_rescue(evaluate_at_rent, discount_rate, years, current_rent, upper_bound=None):
    """Closed form plus numerical verification; no mutation of the scenario."""
    upper = 2 * current_rent if upper_bound is None else upper_bound
    if not np.isfinite(upper) or upper < 0:
        raise ValueError('Invalid rent rescue bound')
    zero = evaluate_at_rent(0.)
    factor = 12 * sum((1 + discount_rate)**(-y) for y in range(1, years + 1))
    if zero < 0:
        return dict(status='NOT_RECOVERABLE_WITHIN_BOUNDS', threshold=None, reason='NEGATIVE_ZERO_RENT_NPV')
    threshold = zero / factor
    residual = evaluate_at_rent(threshold)
    if abs(residual) > 1:
        raise ArithmeticError('Rent threshold did not verify within INR 1')
    # Keep the numerically feasible side so applying a solved rescue cannot
    # become economically rejected solely through floating-point cancellation.
    algebraic_threshold = threshold
    if residual < 0 and threshold > 0:
        threshold = max(0., threshold - 1e-6)
        residual = evaluate_at_rent(threshold)
    already_viable = evaluate_at_rent(current_rent) >= 0
    return dict(status='SOLVED' if threshold <= upper or already_viable else 'NOT_RECOVERABLE_WITHIN_BOUNDS',
                threshold=threshold, verified_npv_inr=residual, bounds=[0., upper],
                algebraic_threshold=algebraic_threshold, threshold_within_bounds=threshold <= upper,
                reason='CURRENT_RENT_ALREADY_FINANCIALLY_VIABLE' if already_viable else 'ZERO_NPV_THRESHOLD',
                below_npv_inr=evaluate_at_rent(max(0., threshold - 1.)),
                above_npv_inr=evaluate_at_rent(threshold + 1.))


def sales_rescue(evaluate_at_multiplier, lower=.5, upper=3.):
    """Sample monotonicity then bisect; report infeasibility, never clip a target."""
    if not np.isfinite([lower, upper]).all() or not 0.5 <= lower <= upper <= 3.:
        raise ValueError('Sales rescue must stay within 0.5..3.0')
    samples = []
    for x in np.linspace(lower, upper, 17):
        try:
            value = float(evaluate_at_multiplier(float(x)))
        except UnattainableRescue:
            # A root can lie between the last grid point and the physical
            # feasibility frontier. Locate that frontier before ruling out a
            # rescue; never silently clip the requested reference target.
            if samples:
                feasible_x, feasible_value = samples[-1]
                infeasible_x = float(x)
                for _ in range(60):
                    middle = (feasible_x + infeasible_x) / 2
                    if middle in (feasible_x, infeasible_x):
                        break
                    try:
                        candidate_value = float(evaluate_at_multiplier(middle))
                        if not np.isfinite(candidate_value):
                            raise ValueError('Nonfinite rescue cash flow')
                        feasible_x, feasible_value = middle, candidate_value
                    except UnattainableRescue:
                        infeasible_x = middle
                if feasible_x > samples[-1][0]:
                    samples.append([feasible_x, feasible_value])
            break
        if not np.isfinite(value):
            raise ValueError('Nonfinite rescue cash flow')
        samples.append([float(x), value])
    # Compare with every previous maximum: a slow cumulative decline must not
    # evade detection merely because each grid step is smaller than INR 1.
    if any(value < max(v for _, v in samples[:i]) - 1 for i, (_, value) in enumerate(samples) if i):
        return dict(status='NON_MONOTONIC', threshold=None, samples=samples)
    if not samples or samples[-1][1] < 0:
        return dict(status='NOT_RECOVERABLE_WITHIN_BOUNDS', threshold=None, samples=samples,
                    reason='NO_VERIFIED_RECOVERY_IN_ATTAINABLE_TESTED_BOUNDS')
    if samples[0][1] >= 0:
        return dict(status='SOLVED', threshold=lower, verified_npv_inr=samples[0][1], samples=samples,
                    reason='ALREADY_VIABLE_AT_LOWER_BOUND')
    low = samples[0][0]
    high = next(x for x, value in samples if value >= 0)
    for _ in range(100):
        middle = (low + high) / 2
        value = float(evaluate_at_multiplier(middle))
        if 0 <= value <= 1:
            return dict(status='SOLVED', threshold=middle, verified_npv_inr=value, samples=samples,
                        below_npv_inr=evaluate_at_multiplier(low), above_npv_inr=evaluate_at_multiplier(high),
                        monotonicity='GRID_CHECK_ONLY_NOT_GLOBAL_PROOF')
        if value < 0:
            low = middle
        else:
            high = middle
    return dict(status='NOT_RECOVERABLE_WITHIN_BOUNDS', threshold=None, samples=samples,
                reason='RESIDUAL_EXCEEDS_INR_1')


class UnattainableRescue(ValueError):
    """Requested sales target cannot be calibrated in the fixed reference."""
