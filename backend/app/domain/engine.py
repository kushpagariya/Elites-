"""Pure numerical orchestration. Backend owns loading and atomic persistence."""
from copy import deepcopy
from datetime import date
import numpy as np
from .validation import DomainUnavailable, digest, number, unique
from .geospatial.features import coordinates, daypart_profiles
from .network.allocation import attraction, calibrate, network_cashflows
from .scenario.timing import infrastructure_multipliers
from .failfast.rules import diagnose, rent_rescue, sales_rescue, UnattainableRescue
from .portfolio.search import enumerate_portfolios, paise

ENGINE_VERSION = 'storescout-domain-1'


def validate(project, scenario):
    if scenario.get('project_id') != project['project_id']:
        raise ValueError('Scenario belongs to another project')
    sites, branches = project['sites'], project['stores']
    if not sites:
        raise DomainUnavailable('At least one prepared candidate site is required')
    unique(sites, 'site_id', 10); unique(branches, 'store_id', 4)
    coordinates(sites); coordinates(branches)
    years = project['projection_years']
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 10:
        raise ValueError('Projection horizon must be 1..10 years')
    number(project['discount_rate_fraction'], 'discount rate', minimum=0, maximum=1)
    number(scenario['budget_inr'], 'scenario budget', minimum=0)
    for site in sites:
        for name in ('capex_inr', 'monthly_rent_inr', 'annual_opex_inr'):
            number(site[name], name, minimum=0)
        number(site['store_size_sqm'], 'store area', minimum=1e-12)
        number(site['gross_margin_fraction'], 'gross margin', minimum=0, maximum=1)
    for branch in branches:
        number(branch['variable_contribution_margin'], 'branch variable margin', minimum=0, maximum=1)
    assumptions = scenario['assumptions']
    number(assumptions.get('demand_multiplier', 1), 'demand multiplier', minimum=0, maximum=3)
    number(assumptions.get('rent_multiplier', 1), 'rent multiplier', minimum=0, maximum=3)
    overrides = assumptions.get('site_overrides', {})
    if not set(overrides) <= {s['site_id'] for s in sites}:
        raise ValueError('Unknown site override')
    for override in overrides.values():
        if set(override) - {'monthly_rent_inr', 'sales_multiplier'}:
            raise ValueError('Unsupported site override')
        if override.get('monthly_rent_inr') is not None:
            number(override['monthly_rent_inr'], 'override rent', minimum=0)
        if override.get('sales_multiplier') is not None:
            number(override['sales_multiplier'], 'override sales', minimum=0, maximum=3)
    inputs = project.get('inputs')
    if not inputs or not inputs.get('cells') or not inputs.get('reference_predictions'):
        raise DomainUnavailable('Prepared cells and actual fitted-model reference_predictions required')
    unique(inputs['cells'], 'cell_id', 2000); coordinates(inputs['cells'])
    if not inputs.get('source_ids') or not inputs.get('feature_snapshot_id'):
        raise DomainUnavailable('Source IDs and frozen feature snapshot ID required')
    date.fromisoformat(inputs['valuation_date'])
    if 'outside' not in inputs or 'competitors' not in inputs:
        raise DomainUnavailable('Explicit competitor reference and outside assumption required')
    number(inputs['outside'], 'outside attraction', minimum=1e-12)
    unique(inputs['competitors'], 'competitor_id'); coordinates(inputs['competitors'])
    if set(inputs['reference_predictions']) != {s['site_id'] for s in sites}:
        raise DomainUnavailable('Predictions must cover exactly the candidate IDs')
    return inputs


def rents_for(sites, assumptions):
    result = {}
    for site in sites:
        value = assumptions.get('site_overrides', {}).get(site['site_id'], {}).get('monthly_rent_inr')
        result[site['site_id']] = float(site['monthly_rent_inr'] if value is None else value) * assumptions.get('rent_multiplier', 1.)
    return result


def freeze(project, scenario, inputs):
    sites, cells = project['sites'], inputs['cells']
    assumptions, years = scenario['assumptions'], project['projection_years']
    wallet = np.array([number(c['annual_wallet_inr'], 'cell wallet', minimum=0) for c in cells])
    external = attraction(cells, inputs['competitors']).sum(axis=1)
    branch_a = attraction(cells, project['stores'])
    units = attraction(cells, [dict(s, theta=0.) for s in sites])
    infra, infra_evidence = infrastructure_multipliers(sites, inputs.get('infrastructure', []), assumptions, inputs['valuation_date'], years)
    wallet *= assumptions.get('demand_multiplier', 1.)
    candidate_a = np.zeros((years, len(cells), len(sites)))
    targets = np.zeros((years, len(sites)))
    calibrations, artifact_ids, modes = [], set(), set()
    for i, site in enumerate(sites):
        prediction = inputs['reference_predictions'][site['site_id']]
        target = prediction.get('reference_annual_sales_inr')
        if target is None or not prediction.get('joint_support_pass') or not prediction.get('hard_schema_compatible'):
            raise DomainUnavailable(f"{site['site_id']}: unsupported prediction; no financial estimate fabricated")
        if prediction.get('method_mode') not in ('model_simulated', 'model_real_evaluated') or not prediction.get('model_artifact_id'):
            raise DomainUnavailable('Actual fitted artifact provenance required; assumption targets cannot claim ML')
        number(target, 'reference sales', minimum=0)
        number(prediction.get('wallet_upper_bound_inr'), 'model wallet bound', minimum=target)
        artifact_ids.add(prediction['model_artifact_id']); modes.add(prediction['method_mode'])
        multiplier = assumptions.get('site_overrides', {}).get(site['site_id'], {}).get('sales_multiplier')
        multiplier = 1. if multiplier is None else multiplier
        for y in range(years):
            targets[y, i] = target * assumptions.get('demand_multiplier', 1.) * multiplier * infra[y, i]
            result = calibrate(wallet, external, units[:, i], targets[y, i], inputs['outside'], tolerance=.01)
            candidate_a[y, :, i] = result.pop('attraction')
            result.update(site_id=site['site_id'], year=y + 1); calibrations.append(result)
    if len(artifact_ids) != 1 or len(modes) != 1:
        raise DomainUnavailable('Mixed model artifacts/modes in one evaluation')
    frozen = dict(wallet_by_year=[wallet.tolist() for _ in range(years)], external_attraction=external.tolist(),
                  branch_attraction=branch_a.tolist(), candidate_unit_attraction=units.tolist(),
                  candidate_attraction_by_year=candidate_a.tolist(), target_by_year_inr=targets.tolist(),
                  outside=inputs['outside'], calibration=calibrations, infrastructure=infra_evidence)
    return frozen, next(iter(artifact_ids)), next(iter(modes))


def value(project, frozen, rents, ids):
    return network_cashflows(frozen, project['sites'], project['stores'], ids, rents, project['discount_rate_fraction'])


def seal_payload(context):
    return {k: context[k] for k in ('engine_version', 'project_hash', 'scenario', 'evaluation', 'frozen_network', 'rents')}


def prepare_evaluation(project, scenario):
    """Return public computed fields and private context for one atomic save."""
    inputs = validate(project, scenario)
    frozen, artifact_id, mode = freeze(project, scenario, inputs)
    sites = project['sites']; rents = rents_for(sites, scenario['assumptions'])
    low_frozen, high_frozen = deepcopy(frozen), deepcopy(frozen)
    low_frozen['wallet_by_year'] = (np.asarray(frozen['wallet_by_year']) * .8).tolist()
    high_frozen['wallet_by_year'] = (np.asarray(frozen['wallet_by_year']) * 1.2).tolist()
    analyses, details = [], {}
    for i, site in enumerate(sites):
        sid = site['site_id']
        base = value(project, frozen, rents, [sid])
        low = value(project, low_frozen, {k: v * 1.1 for k, v in rents.items()}, [sid])
        high = value(project, high_frozen, rents, [sid])
        flags = inputs.get('site_eligibility', {}).get(sid, {})
        hard, review = list(flags.get('hard_failures', [])), list(flags.get('review_reasons', []))
        if paise(site['capex_inr']) > paise(scenario['budget_inr']):
            hard.append('CAPEX_EXCEEDS_SCENARIO_BUDGET')
        bounds = inputs.get('geographic_bounds')
        if bounds and not (bounds[0] <= site['latitude'] <= bounds[2] and bounds[1] <= site['longitude'] <= bounds[3]):
            hard.append('OUTSIDE_DECLARED_GEOGRAPHIC_BOUNDS')
        if any(c['site_id'] == sid and 'REVIEW_REQUIRED' in c['status'] for c in frozen['calibration']):
            review.append('REFERENCE_TARGET_UNATTAINABLE')
        if not inputs.get('poi_coverage_supported', False):
            review.append('POI_COVERAGE_UNKNOWN')
        warnings = list(inputs['reference_predictions'][sid].get('warnings', [])) + list(inputs.get('evidence_warnings', []))
        if mode == 'model_simulated':
            warnings.append('SYNTHETIC_MODEL_NO_REAL_OUTCOME_VALIDATION')
        diagnosis, rules = diagnose(base['npv_inr'], low['npv_inr'], hard_reasons=hard, review_reasons=review, warnings=sorted(set(warnings)))
        rent_result = rent_rescue(lambda r: value(project, frozen, dict(rents, **{sid: r}), [sid])['npv_inr'],
                                  project['discount_rate_fraction'], project['projection_years'], rents[sid])
        diagnosis['max_viable_monthly_rent_inr'] = rent_result['threshold']
        revenue, lost = base['candidate_revenue_by_year_inr'][0][0], base['lost_existing_contribution_by_year_inr'][0]
        drivers = [f'Year-1 allocated sales INR {revenue:.2f}; standalone target INR {frozen["target_by_year_inr"][0][i]:.2f}',
                   f'Year-1 lost existing variable contribution INR {lost:.2f}, deducted once',
                   f'Annual rent INR {12*rents[sid]:.2f}, other OPEX INR {site["annual_opex_inr"]:.2f}, CAPEX INR {site["capex_inr"]:.2f}',
                   f'Nonprobabilistic downside/base/upside NPV INR {low["npv_inr"]:.2f}/{base["npv_inr"]:.2f}/{high["npv_inr"]:.2f}']
        analyses.append(dict(site_id=sid, annual_revenue_inr=revenue, lost_existing_contribution_inr=lost,
                             annual_cashflows_inr=base['annual_cashflows_inr'], npv_inr=base['npv_inr'],
                             roi_fraction=base['roi_fraction'], payback_years=base['payback_years'], failfast=diagnosis,
                             drivers=drivers, source_ids=sorted(set(inputs['source_ids']))))
        details[sid] = dict(base=base, downside=low, upside=high, rules=rules, rent_rescue=rent_result,
                            calibration=[c for c in frozen['calibration'] if c['site_id'] == sid])
    costs = {s['site_id']: s['capex_inr'] for s in sites}
    ranked = sorted((a for a in analyses if a['failfast']['status'] in ('VIABLE', 'AT_RISK')),
                    key=lambda a: (-a['npv_inr'], costs[a['site_id']], a['site_id']))
    evaluation = dict(method_mode=mode, model_artifact_id=artifact_id, site_analyses=analyses, rankings=[a['site_id'] for a in ranked])
    context = dict(engine_version=ENGINE_VERSION, project_hash=digest(project), scenario=deepcopy(scenario),
                   evaluation=deepcopy(evaluation), frozen_network=frozen, rents=rents)
    context['integrity_sha256'] = digest(seal_payload(context))
    profiles = daypart_profiles(sites, inputs.get('pois', []), inputs['weights'], availability=inputs.get('availability'),
                               coverage_supported=inputs.get('poi_coverage_supported', False))
    diagnostics = dict(engine_version=ENGINE_VERSION, feature_snapshot_id=inputs['feature_snapshot_id'],
                       valuation_date=inputs['valuation_date'], source_ids=inputs['source_ids'],
                       assumption_ids=inputs.get('assumption_ids', []), site_details=details, dayparts=profiles,
                       infrastructure=frozen['infrastructure'], confidence='SENSITIVITY_CASES_NOT_FORECAST_INTERVALS')
    return dict(evaluation=evaluation, context=context, diagnostics=diagnostics)


def run_evaluation(project, scenario):
    return prepare_evaluation(project, scenario)['evaluation']


def check_context(project, context):
    required = {'engine_version', 'project_hash', 'scenario', 'evaluation', 'frozen_network', 'rents', 'integrity_sha256'}
    if not required <= set(context):
        raise DomainUnavailable('Saved frozen-network context required; singleton analyses insufficient')
    if context['engine_version'] != ENGINE_VERSION or context['project_hash'] != digest(project):
        raise ValueError('Stale/cross-project analytical context')
    if context['integrity_sha256'] != digest(seal_payload(context)):
        raise ValueError('Context integrity mismatch; scenario/network/results changed')
    if context['scenario']['project_id'] != project['project_id']:
        raise ValueError('Cross-project scenario')


def run_portfolio(project, evaluation, max_stores, acknowledged_risk_site_ids):
    check_context(project, evaluation)
    analyses = evaluation['evaluation']['site_analyses']
    risk = {a['site_id'] for a in analyses if a['failfast']['status'] == 'AT_RISK'}
    acknowledgements = set(acknowledged_risk_site_ids)
    if len(acknowledgements) != len(acknowledged_risk_site_ids) or not acknowledgements <= risk:
        raise ValueError('Acknowledgements must name AT_RISK sites in this exact evaluation')
    eligible = [a['site_id'] for a in analyses if a['failfast']['status'] == 'VIABLE' or a['site_id'] in acknowledgements]
    return enumerate_portfolios(project['sites'], eligible, evaluation['scenario']['budget_inr'], max_stores,
                                lambda ids: value(project, evaluation['frozen_network'], evaluation['rents'], ids)['npv_inr'])


def calculate_rescue(project, context, site_id, lever='rent', *, lower_bound=None, upper_bound=None):
    """Return canonical SiteOverride coordinates, verified on a fresh copy.

    Rent bounds are base INR/month, before the global rent multiplier. Sales
    search bounds retain their original *relative-to-current-target* meaning;
    the returned threshold/override is an absolute baseline sales multiplier.
    No identity is allocated and no scenario, model or frozen context is edited.
    """
    check_context(project, context)
    index = {s['site_id']: i for i, s in enumerate(project['sites'])}
    if site_id not in index:
        raise ValueError('Unknown rescue site')
    frozen, rents = context['frozen_network'], context['rents']
    scenario = context['scenario']
    assumptions = scenario['assumptions']
    current_override = assumptions.get('site_overrides', {}).get(site_id, {})
    source_analysis = next(a for a in context['evaluation']['site_analyses'] if a['site_id'] == site_id)
    hard_block = any(r.startswith('HARD:') for r in source_analysis['failfast']['failed_rule_ids'])
    canonical_value = None
    if lever == 'rent':
        if lower_bound not in (None, 0):
            raise ValueError('Rent rescue lower bound is zero')
        multiplier = number(assumptions.get('rent_multiplier', 1.), 'global rent multiplier', minimum=0, maximum=3)
        base_rent = current_override.get('monthly_rent_inr')
        if base_rent is None:
            base_rent = project['sites'][index[site_id]]['monthly_rent_inr']
        upper = 2 * base_rent if upper_bound is None else number(upper_bound, 'base rent upper bound', minimum=0)
        result = rent_rescue(lambda r: value(project, frozen, dict(rents, **{site_id: r}), [site_id])['npv_inr'],
                             project['discount_rate_fraction'], project['projection_years'], rents[site_id], upper * multiplier)
        effective_threshold = result['threshold']
        base_threshold = effective_threshold / multiplier if multiplier and effective_threshold is not None else None
        result.update(current_base_monthly_rent_inr=base_rent, current_effective_monthly_rent_inr=rents[site_id],
                      global_rent_multiplier=multiplier,
                      max_viable_effective_monthly_rent_inr=effective_threshold,
                      max_viable_base_monthly_rent_inr=base_threshold,
                      solver_effective_threshold_inr=effective_threshold,
                      configured_base_rent_bounds_inr=[0., upper],
                      solver_status=result['status'],
                      financial_status='SOLVED' if effective_threshold is not None else result['status'])
        result['threshold'] = None
        if multiplier == 0:
            result.update(status='NOT_RECOVERABLE_WITHIN_BOUNDS',
                          reason='ZERO_GLOBAL_RENT_MULTIPLIER_NO_FINITE_BASE_RENT_INVERSE',
                          application_status='BLOCKED_ZERO_RENT_MULTIPLIER')
        elif base_threshold is not None:
            # If the requested upper bound is below the economic cap, that
            # bound is the largest permitted viable rent, not a zero-NPV root.
            canonical_value = min(base_threshold, upper)
            result['bound_limits_affordability_threshold'] = base_threshold > upper
            if base_threshold > upper:
                result['reason'] = 'VIABLE_AT_CONFIGURED_UPPER_RENT_BOUND'
    elif lever == 'sales':
        i = index[site_id]
        current_absolute = current_override.get('sales_multiplier')
        current_absolute = 1. if current_absolute is None else current_absolute
        lower = .5 if lower_bound is None else number(lower_bound, 'relative sales lower bound', minimum=.5, maximum=3)
        upper = 3. if upper_bound is None else number(upper_bound, 'relative sales upper bound', minimum=.5, maximum=3)
        if lower > upper:
            raise ValueError('Sales rescue lower bound exceeds upper bound')
        result = dict(status='NOT_RECOVERABLE_WITHIN_BOUNDS', threshold=None,
                      current_absolute_sales_multiplier=current_absolute,
                      configured_relative_sales_bounds=[lower, upper],
                      relative_rescue_multiplier=None, new_absolute_sales_multiplier=None)
        if current_absolute == 0:
            result.update(reason='ZERO_CURRENT_SALES_MULTIPLIER_RELATIVE_SEARCH_HAS_NO_EFFECT',
                          application_status='BLOCKED_ZERO_CURRENT_SALES_MULTIPLIER')
        else:
            # Intersect the configured relative range with canonical abs<=3
            # and each year's attainable [-30,30] reference interval. This
            # also detects a narrow feasible interior between coarse probes.
            feasible_lower, feasible_upper = lower, min(upper, 3. / current_absolute)
            for y, wallet in enumerate(frozen['wallet_by_year']):
                target = frozen['target_by_year_inr'][y][i]
                if target > 0:
                    endpoints = calibrate(wallet, frozen['external_attraction'],
                                          np.asarray(frozen['candidate_unit_attraction'])[:, i], 0., frozen['outside'])
                    lo, hi = endpoints['endpoint_bounds_inr']
                    feasible_lower = max(feasible_lower, lo / target)
                    feasible_upper = min(feasible_upper, hi / target)
            result['effective_relative_sales_bounds'] = [feasible_lower, feasible_upper] if feasible_lower <= feasible_upper else None
            result['effective_absolute_sales_bounds'] = [feasible_lower * current_absolute, feasible_upper * current_absolute] if feasible_lower <= feasible_upper else None
            if feasible_lower > feasible_upper:
                result.update(reason='NO_ATTAINABLE_TARGET_WITHIN_CONFIGURED_AND_CANONICAL_BOUNDS',
                              application_status='BLOCKED_REFERENCE_OR_CANONICAL_BOUNDS')
            else:
                infra, _ = infrastructure_multipliers(project['sites'], project['inputs'].get('infrastructure', []),
                                                      assumptions, project['inputs']['valuation_date'], project['projection_years'])
                predicted_target = project['inputs']['reference_predictions'][site_id]['reference_annual_sales_inr']

                def at_multiplier(relative):
                    adjusted = deepcopy(frozen)
                    matrices = np.asarray(frozen['candidate_attraction_by_year'], float).copy()
                    absolute = current_absolute * relative
                    for y, wallet in enumerate(frozen['wallet_by_year']):
                        # Same multiplication order and calibration tolerance
                        # as freeze() when the absolute override is applied.
                        target = predicted_target * assumptions.get('demand_multiplier', 1.) * absolute * infra[y, i]
                        calibration = calibrate(wallet, frozen['external_attraction'], np.asarray(frozen['candidate_unit_attraction'])[:, i],
                                                target, frozen['outside'], tolerance=.01)
                        if calibration['status'] == 'UNATTAINABLE_REVIEW_REQUIRED':
                            raise UnattainableRescue('Target outside attainable reference endpoints')
                        if calibration['status'] == 'ITERATION_LIMIT_REVIEW_REQUIRED':
                            raise ArithmeticError('Reference calibration iteration limit')
                        matrices[y, :, i] = calibration['attraction']
                    adjusted['candidate_attraction_by_year'] = matrices.tolist()
                    return value(project, adjusted, rents, [site_id])['npv_inr']

                solved = sales_rescue(at_multiplier, feasible_lower, feasible_upper)
                relative = solved['threshold']
                result.update(solved, financial_status=solved['status'], solver_relative_threshold=relative,
                              relative_rescue_multiplier=relative,
                              new_absolute_sales_multiplier=current_absolute * relative if relative is not None else None)
                result['threshold'] = None
                if relative is not None:
                    canonical_value = current_absolute * relative
    else:
        raise ValueError('Unknown rescue lever')
    result.update(site_id=site_id, lever=lever, scenario_id=context['scenario']['scenario_id'],
                  context_sha256=context['integrity_sha256'], clears_unrelated_failures=False,
                  rescue_contract_version='canonical-site-override-1',
                  threshold_coordinates='CANONICAL_SITE_OVERRIDE', actionable_site_override=None,
                  applied_verification=None)
    if hard_block:
        result.update(status='NOT_RECOVERABLE_WITHIN_BOUNDS', reason='HARD_ELIGIBILITY_FAILURE_REMAINS',
                      application_status='BLOCKED_HARD_ELIGIBILITY', threshold=None)
    elif canonical_value is not None:
        key = 'monthly_rent_inr' if lever == 'rent' else 'sales_multiplier'
        changed = deepcopy(scenario)
        changed['assumptions'].setdefault('site_overrides', {}).setdefault(site_id, {})[key] = canonical_value
        verified = prepare_evaluation(project, changed)
        analysis = next(a for a in verified['evaluation']['site_analyses'] if a['site_id'] == site_id)
        result['solver_verified_npv_inr'] = result.get('verified_npv_inr')
        result['verified_npv_inr'] = analysis['npv_inr']
        result['applied_verification'] = dict(scenario_input_sha256=digest(changed), persisted=False,
            source_scenario_id=scenario['scenario_id'], new_scenario_id_required_from_backend=True,
            npv_inr=analysis['npv_inr'], failfast=analysis['failfast'],
            annual_revenue_inr=analysis['annual_revenue_inr'],
            lost_existing_contribution_inr=analysis['lost_existing_contribution_inr'],
            annual_cashflows_inr=analysis['annual_cashflows_inr'], method_mode=verified['evaluation']['method_mode'],
            model_artifact_id=verified['evaluation']['model_artifact_id'])
        if analysis['failfast']['status'] in ('REJECTED', 'REVIEW_REQUIRED') or analysis['npv_inr'] < 0:
            result.update(status='NOT_RECOVERABLE_WITHIN_BOUNDS', reason='APPLIED_SCENARIO_NOT_ELIGIBLE_OR_NOT_FINANCIALLY_VIABLE',
                          application_status='BLOCKED_APPLIED_VERIFICATION')
        else:
            result.update(status='SOLVED', threshold=canonical_value, actionable_site_override={key: canonical_value},
                          application_status='VERIFIED_FRESH_SCENARIO_COPY',
                          requires_risk_acknowledgement=analysis['failfast']['status'] == 'AT_RISK')
    else:
        result.setdefault('application_status', 'BLOCKED_NO_VERIFIED_FINANCIAL_SOLUTION')
    return result
