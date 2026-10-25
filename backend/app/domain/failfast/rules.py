"""Explicit rule precedence and inverse economics on the same numerical engine."""
import numpy as np
from ..validation import number


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
    """Find a feasible interval before sampled-monotonic root search.

    An unattainable reference point is not a numerical error and does not prove
    the remaining interval infeasible. The caller can first intersect these
    bounds with its analytically attainable reference interval. At most 17 grid
    points, 120 frontier refinements and 100 root iterations are evaluated.
    """
    lower = number(lower, 'sales rescue lower bound', minimum=.5, maximum=3.)
    upper = number(upper, 'sales rescue upper bound', minimum=.5, maximum=3.)
    if lower > upper:
        raise ValueError('Sales rescue must stay within 0.5..3.0')
    values, infeasible = {}, {}

    def evaluate(x):
        if x in values:
            return values[x]
        try:
            value = number(evaluate_at_multiplier(x), 'rescue objective NPV')
        except UnattainableRescue as exc:
            infeasible[x] = str(exc)
            value = None
        values[x] = value
        return value

    def result(status, reason, **extra):
        samples = [[x, v] for x, v in sorted(values.items()) if v is not None]
        return dict(status=status, reason=reason, threshold=None, samples=samples,
                    bounds=[lower, upper],
                    feasible_bounds=[samples[0][0], samples[-1][0]] if samples else None,
                    infeasible_samples=[[x, why] for x, why in sorted(infeasible.items())],
                    monotonicity='GRID_CHECK_ONLY_NOT_GLOBAL_PROOF', **extra)

    try:
        for x in np.linspace(lower, upper, 17):
            evaluate(float(x))
        feasible = sorted(x for x, v in values.items() if v is not None)
        if not feasible:
            return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'NO_VERIFIED_FEASIBLE_POINT')
        first, last = feasible[0], feasible[-1]
        if any(first < x < last for x in infeasible):
            return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'DISCONNECTED_FEASIBILITY_INTERVAL')
        # Refine both physical frontiers, including a lower endpoint that the
        # old implementation treated as proof of no recovery.
        for left_side in (True, False):
            failures = [x for x in infeasible if x < first] if left_side else [x for x in infeasible if x > last]
            if not failures:
                continue
            bad = max(failures) if left_side else min(failures)
            good = first if left_side else last
            for _ in range(60):
                middle = (bad + good) / 2
                if middle in (bad, good):
                    break
                if evaluate(middle) is None:
                    bad = middle
                else:
                    good = middle
        samples = [[x, v] for x, v in sorted(values.items()) if v is not None]
        if any(value < max(v for _, v in samples[:i]) - 1 for i, (_, value) in enumerate(samples) if i):
            return result('NON_MONOTONIC', 'SAMPLED_NPV_DECREASE')
        if samples[-1][1] < 0:
            return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'NO_RECOVERY_IN_VERIFIED_FEASIBLE_INTERVAL')
        if samples[0][1] >= 0:
            answer = result('SOLVED', 'ALREADY_VIABLE_AT_FEASIBLE_LOWER_BOUND',
                            verified_npv_inr=samples[0][1])
            answer['threshold'] = samples[0][0]
            return answer
        high = next(x for x, value in samples if value >= 0)
        low = max(x for x, value in samples if x < high and value < 0)
        for _ in range(100):
            middle = (low + high) / 2
            value = evaluate(middle)
            if value is None:
                return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'INFEASIBLE_POINT_INSIDE_ROOT_BRACKET')
            if 0 <= value <= 1:
                answer = result('SOLVED', 'VERIFIED_ZERO_NPV_THRESHOLD', verified_npv_inr=value,
                                below_npv_inr=evaluate(low), above_npv_inr=evaluate(high))
                answer['threshold'] = middle
                return answer
            if value < 0:
                low = middle
            else:
                high = middle
        return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'RESIDUAL_EXCEEDS_INR_1')
    except (ValueError, ArithmeticError) as exc:
        return result('NOT_RECOVERABLE_WITHIN_BOUNDS', 'NUMERICAL_EVALUATION_FAILURE',
                      numerical_error=f'{type(exc).__name__}: {exc}')


class UnattainableRescue(ValueError):
    """Requested sales target cannot be calibrated in the fixed reference."""
