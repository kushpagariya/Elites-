"""Map delivered engine evidence into the wire schema; never revalue a decision."""
from math import cos, sin, pi, radians
from . import sources


def evaluation(prepared, project, scenario, source_hash):
    result = prepared['evaluation']
    diagnostics = prepared['diagnostics']
    # Explain the delivered opportunity profile using the same domain function,
    # restricted to one real POI category at a time. No financial revaluation.
    from ..domain.geospatial.features import daypart_profiles
    inputs = project['inputs']
    contributions = {
        category: daypart_profiles(project['sites'],
            [p for p in inputs['pois'] if p['category'] == category], inputs['weights'],
            availability=inputs['availability'], coverage_supported=inputs['poi_coverage_supported'])
        for category in inputs['weights']['category_weights']
    }
    for index, row in enumerate(result['site_analyses']):
        sid = row['site_id']
        detail = diagnostics['site_details'][sid]
        base = detail['base']
        row['operating_profit_inr'] = base['annual_cashflows_inr'][0] + base['lost_existing_contribution_by_year_inr'][0]
        # Display the delivered before/after allocation; this decomposition
        # does not feed back into valuation or deduct contribution again.
        row['branch_impacts'] = [dict(store_id=branch['store_id'], baseline_revenue_inr=before,
            after_revenue_inr=after, lost_contribution_inr=(before-after)*branch['variable_contribution_margin'])
            for branch, before, after in zip(project['stores'], base['existing_revenue_before_by_year_inr'][0], base['existing_revenue_after_by_year_inr'][0])]
        row['sensitivity'] = {}
        for name, key in (('low', 'downside'), ('base', 'base'), ('high', 'upside')):
            case = detail[key]
            row['sensitivity'][name] = dict(annual_revenue_inr=case['candidate_revenue_by_year_inr'][0][0],
                operating_profit_inr=case['annual_cashflows_inr'][0] + case['lost_existing_contribution_by_year_inr'][0],
                lost_existing_contribution_inr=case['lost_existing_contribution_by_year_inr'][0],
                npv_inr=case['npv_inr'], roi_fraction=case['roi_fraction'], payback_years=case['payback_years'])
        profile = diagnostics['dayparts'][sid]
        row['dayparts'] = [dict(time_bin=period, opportunity_index=share * 100 if share is not None else None,
            raw_opportunity=profile['raw'][period], support_count=profile['support_count'],
            categories=[dict(category=category, count=values[sid]['support_count'],
                            weighted_opportunity=values[sid]['raw'][period])
                        for category, values in contributions.items()
                        if values[sid]['raw'][period] is not None and values[sid]['support_count'] > 0],
            source_ids=profile['source_ids'], source_status='ASSUMED', reliability=profile['coverage_status'],
            observed_at=None, reason=profile['interpretation'] + '. ' + profile['coverage_caveat'])
            for period, share in profile['weekly_exposure_share'].items()]
        row['infrastructure_exposure'] = [dict(event_id=e['event_id'], distance_m=None,
            exposure_fraction=e['exposure'][index], opening_date=e['opening_date'], active_fractions=e['active_fractions'],
            assumed_effect_fraction=e['effect_fraction'], hypothetical=e['hypothetical'])
            for e in diagnostics['infrastructure'] if 'exposure' in e]
        c = detail['calibration'][0]
        row['calibration'] = dict(target_revenue_inr=c['requested_inr'], achieved_reference_revenue_inr=c['achieved_inr'], within_tolerance=c['status'] in ('CALIBRATED', 'CALIBRATED_ZERO_TARGET'))
        site = project['sites'][index]
        override = scenario['assumptions']['site_overrides'].get(sid, {})
        row['effective_inputs'] = dict(monthly_rent_inr=prepared['context']['rents'][sid], annual_opex_inr=site['annual_opex_inr'],
            gross_margin_fraction=site['gross_margin_fraction'], sales_multiplier=1. if override.get('sales_multiplier') is None else override['sales_multiplier'], competition_multiplier=1.)
    result['evidence'] = dict(feature_snapshot_id=sources.FEATURE_SNAPSHOT_ID, source_snapshot_id=source_hash,
        finance_version='cashflows-1', rule_version='storescout-domain-1', weight_version='weights-demo-1',
        estimator_version=result['model_artifact_id'], valuation_date=sources.VALUATION_DATE,
        limitations=sources.LIMITATIONS, assumed_parameters=dict(
            outside_attraction=1., competitor_area_sqm=100., competitor_theta=0., distance_decay_m=750.,
            sensitivity='Deterministic downside/base/upside stress cases',
            calibration_permission='Demonstration only; model does not permit automatic investment calibration'))
    return result


def geographic(context, evaluation_id):
    inputs, project = context['project']['inputs'], context['project']
    radius = inputs['weights']['catchment_radius_m']
    catchments = []
    for site in project['sites']:
        # Geometry only: an explicitly approximate straight-line circle.
        lat, lng = site['latitude'], site['longitude']
        coords = [[lng + radius * cos(2*pi*i/64)/(111320*cos(radians(lat))), lat + radius*sin(2*pi*i/64)/111320] for i in range(65)]
        catchments.append(dict(site_id=site['site_id'], geometry=dict(type='Polygon', coordinates=[coords])))
    pois = [{k: p[k] for k in ('poi_id', 'category', 'latitude', 'longitude', 'source_id')} | dict(name=p.get('name') or None, opening_hours=p.get('opening_hours') or None, source_status='REAL') for p in inputs['pois']]
    cells = [{k: c[k] for k in ('cell_id', 'latitude', 'longitude', 'annual_wallet_inr', 'source_id')} | dict(source_status='ASSUMED') for c in inputs['cells']]
    return dict(evaluation_id=evaluation_id, catchment_radius_m=radius, pois=pois, cells=cells,
                catchments=catchments, roads=[], competitors=[], limitations=[
                    'OSM mapped records are real; opening hours may be assumed and coverage is partial.',
                    'Competitors are included in the POI layer and in allocation with assumed equal attraction.',
                    'Historical population/spending proxies; circular catchments are not travel-time isochrones.'])
