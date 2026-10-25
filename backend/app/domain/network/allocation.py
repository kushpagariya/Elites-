"""Frozen gravity allocation and standalone reference calibration in INR/year."""
import numpy as np
from ..geospatial.features import distances
from ..validation import number

NETWORK_VERSION = 'gravity-network-1'


def attraction(cells, stores, *, tau=750., gamma=1.):
    number(tau, 'tau metres', minimum=1)
    number(gamma, 'gamma', minimum=0)
    sizes = np.array([number(s['store_size_sqm'], 'store area', minimum=1e-12) for s in stores])
    theta = np.array([number(s['theta'], 'theta', minimum=-30, maximum=30) for s in stores])
    return np.exp(theta)[None, :] * (sizes[None, :] / 100.)**gamma * np.exp(-distances(cells, stores) / tau)


def allocate(wallet, external, company, outside=1.):
    w, e, a = np.asarray(wallet, float), np.asarray(external, float), np.asarray(company, float)
    o = np.broadcast_to(np.asarray(outside, float), w.shape)
    if w.ndim != 1 or e.shape != w.shape or a.ndim != 2 or a.shape[0] != len(w):
        raise ValueError('Wallet/attraction shapes do not agree')
    if not all(np.isfinite(x).all() for x in (w, e, a, o)) or np.any(w < 0) or np.any(e < 0) or np.any(a < 0) or np.any(o <= 0):
        raise ValueError('Invalid wallet/attraction; outside must be strictly positive')
    denom = o + e + a.sum(axis=1)
    shares = a / denom[:, None]
    external_share, outside_share = e / denom, o / denom
    error = float(np.max(np.abs(shares.sum(axis=1) + external_share + outside_share - 1)))
    if error > 1e-6:
        raise ArithmeticError('Allocation failed wallet conservation')
    return dict(revenues_inr=w @ shares, shares=shares, external_inr=float(w @ external_share),
                outside_inr=float(w @ outside_share), conservation_error=error)


def calibrate(wallet, external, unit_attraction, target, outside=1., tolerance=1.):
    """Bounded bisection. Failed/unattainable targets retain requested/achieved.

    No own branches participate here. Zero target means explicit zero candidate
    attraction (theta undefined), rather than invented near-zero sales.
    """
    target = number(target, 'reference target', minimum=0)
    w, u, e = map(lambda x: np.asarray(x, float), (wallet, unit_attraction, external))
    if u.shape != w.shape or np.any(u < 0) or not np.isfinite(u).all():
        raise ValueError('Invalid calibration unit attraction')
    def revenue(theta):
        return float(allocate(w, e, (u * np.exp(theta))[:, None], outside)['revenues_inr'][0])
    low, high = -30., 30.
    lo, hi = revenue(low), revenue(high)
    if target == 0:
        return dict(theta=None, attraction=np.zeros_like(u), requested_inr=0., achieved_inr=0.,
                    status='CALIBRATED_ZERO_TARGET', iterations=0, endpoint_bounds_inr=[lo, hi])
    if target < lo or target > hi:
        theta = low if target < lo else high
        return dict(theta=theta, attraction=u * np.exp(theta), requested_inr=target,
                    achieved_inr=revenue(theta), status='UNATTAINABLE_REVIEW_REQUIRED',
                    iterations=0, endpoint_bounds_inr=[lo, hi])
    for iteration in range(1, 101):
        theta = (low + high) / 2
        achieved = revenue(theta)
        if abs(achieved - target) <= tolerance:
            break
        if achieved < target:
            low = theta
        else:
            high = theta
    return dict(theta=theta, attraction=u * np.exp(theta), requested_inr=target,
                achieved_inr=achieved, status='CALIBRATED' if abs(achieved-target) <= tolerance else 'ITERATION_LIMIT_REVIEW_REQUIRED',
                iterations=iteration, endpoint_bounds_inr=[lo, hi])


def network_cashflows(frozen, sites, branches, selected_ids, rents, discount_rate):
    """Reallocate the entire selected set; deduct each lost branch margin once."""
    from ..finance.cashflows import evaluate_cashflows
    index = {s['site_id']: i for i, s in enumerate(sites)}
    if len(set(selected_ids)) != len(selected_ids) or not set(selected_ids) <= set(index):
        raise ValueError('Invalid selected site IDs')
    indices = [index[s] for s in selected_ids]
    margins = np.array([s['gross_margin_fraction'] for s in sites])[indices]
    branch_margins = np.array([b['variable_contribution_margin'] for b in branches])
    branch_a = np.asarray(frozen['branch_attraction'], float)
    candidate_a = np.asarray(frozen['candidate_attraction_by_year'], float)
    external = np.asarray(frozen['external_attraction'], float)
    flows, sales, losses, branch_before, branch_after, errors = [], [], [], [], [], []
    for y, wallet in enumerate(frozen['wallet_by_year']):
        baseline = allocate(wallet, external, branch_a, frozen['outside'])
        after = allocate(wallet, external, np.column_stack([branch_a, candidate_a[y][:, indices]]), frozen['outside'])
        before_rev, after_rev = baseline['revenues_inr'], after['revenues_inr'][:len(branches)]
        lost = float((before_rev - after_rev) @ branch_margins)
        new_rev = after['revenues_inr'][len(branches):]
        costs = sum(12 * rents[s] + sites[index[s]]['annual_opex_inr'] for s in selected_ids)
        flows.append(float(new_rev @ margins - costs - lost))
        sales.append(new_rev.tolist()); losses.append(lost)
        branch_before.append(before_rev.tolist()); branch_after.append(after_rev.tolist())
        errors.append(after['conservation_error'])
    capex = sum(sites[index[s]]['capex_inr'] for s in selected_ids)
    finance = evaluate_cashflows(capex, flows, discount_rate)
    return dict(annual_cashflows_inr=flows, candidate_revenue_by_year_inr=sales,
                lost_existing_contribution_by_year_inr=losses,
                existing_revenue_before_by_year_inr=branch_before, existing_revenue_after_by_year_inr=branch_after,
                conservation_error=max(errors), npv_inr=finance.npv_inr,
                roi_fraction=finance.horizon_roi, payback_years=finance.payback_years)
