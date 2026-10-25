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
    """Numerical rescue evidence; backend owns the agreed wire response."""
    check_context(project, context)
    index = {s['site_id']: i for i, s in enumerate(project['sites'])}
    if site_id not in index:
        raise ValueError('Unknown rescue site')
    frozen, rents = context['frozen_network'], context['rents']
    if lever == 'rent':
        if lower_bound not in (None, 0):
            raise ValueError('Rent rescue lower bound is zero')
        result = rent_rescue(lambda r: value(project, frozen, dict(rents, **{site_id: r}), [site_id])['npv_inr'],
                             project['discount_rate_fraction'], project['projection_years'], rents[site_id], upper_bound)
    elif lever == 'sales':
        i = index[site_id]
        def at_multiplier(multiplier):
            adjusted = deepcopy(frozen)
            matrices = np.asarray(frozen['candidate_attraction_by_year'], float).copy()
            for y, wallet in enumerate(frozen['wallet_by_year']):
                calibration = calibrate(wallet, frozen['external_attraction'], np.asarray(frozen['candidate_unit_attraction'])[:, i],
                                        frozen['target_by_year_inr'][y][i] * multiplier, frozen['outside'], tolerance=.001)
                if 'REVIEW_REQUIRED' in calibration['status']:
                    raise UnattainableRescue('Sales rescue outside attainable reference')
                matrices[y, :, i] = calibration['attraction']
            adjusted['candidate_attraction_by_year'] = matrices.tolist()
            return value(project, adjusted, rents, [site_id])['npv_inr']
        result = sales_rescue(at_multiplier, .5 if lower_bound is None else lower_bound, 3. if upper_bound is None else upper_bound)
    else:
        raise ValueError('Unknown rescue lever')
    result.update(site_id=site_id, lever=lever, scenario_id=context['scenario']['scenario_id'],
                  context_sha256=context['integrity_sha256'], clears_unrelated_failures=False)
    return result
