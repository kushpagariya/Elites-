"""Exact capped enumeration with integer paise and a truthful cutoff."""
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
from time import perf_counter
from ..validation import number


def paise(value):
    number(value, 'INR amount', minimum=0)
    return int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def enumerate_portfolios(sites, eligible_ids, budget, max_stores, value, *, deadline_seconds=5., clock=perf_counter):
    if isinstance(max_stores, bool) or not isinstance(max_stores, int) or not 0 <= max_stores <= 10:
        raise ValueError('max_stores must be an integer in 0..10')
    if len(sites) > 10 or len(set(eligible_ids)) != len(eligible_ids):
        raise ValueError('Invalid portfolio candidate set')
    number(deadline_seconds, 'deadline seconds', minimum=0, maximum=5)
    by_id = {s['site_id']: s for s in sites}
    if not set(eligible_ids) <= set(by_id):
        raise ValueError('Unknown eligible site')
    ids = sorted(eligible_ids)
    subsets = [c for k in range(min(max_stores, len(ids)) + 1) for c in combinations(ids, k)]
    costs = {i: paise(by_id[i]['capex_inr']) for i in ids}
    limit = paise(budget)
    start = clock()
    best, best_cost, best_value = (), 0, 0.
    # The exact empty action needs no allocation and is always a valid incumbent.
    evaluated = 1
    for subset in subsets[1:]:
        if clock() - start >= deadline_seconds:
            break
        cost = sum(costs[i] for i in subset)
        if cost <= limit:
            result = number(value(list(subset)), 'portfolio NPV')
            if (-result, cost, len(subset), subset) < (-best_value, best_cost, len(best), best):
                best, best_cost, best_value = subset, cost, result
        evaluated += 1
    if best_cost > limit or len(best) > max_stores or not set(best) <= set(ids):
        raise ArithmeticError('Portfolio incumbent failed feasibility recheck')
    return dict(selected_site_ids=list(best), budget_used_inr=best_cost / 100,
                budget_unused_inr=(limit - best_cost) / 100, full_network_npv_inr=best_value,
                status='FULL_NETWORK_EXACT' if evaluated == len(subsets) else 'FEASIBLE_PARTIAL',
                evaluated_subsets=evaluated, total_subsets=len(subsets))
