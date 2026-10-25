"""Offline Bengaluru -> real fitted inference -> domain engine -> review evidence.

Run: python -m ml.decision_engine.run
Only ml/evaluation/decision_engine_v1 is written. No source/fixture edits.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
from copy import deepcopy

from backend.app.domain.pipeline import prepare_evaluation, run_portfolio, calculate_rescue
from backend.app.domain.validation import digest
from backend.app.domain.geospatial.features import TIME_BINS
from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
from ml.training.reference_sales.features import FEATURES

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'ml/evaluation/decision_engine_v1'
FINAL = ROOT / 'data/bengaluru/final'
REVISED = ROOT / 'data/bengaluru/revised_v2'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False), encoding='utf-8')


def build_project():
    """Explicit CSV mappings; original 50/70-column views remain untouched."""
    features = rows(REVISED / 'site_features_enriched.csv')
    estimator = ReferenceSalesEstimatorV2()
    predictions, sites = {}, []
    for row in features:
        model_row = {f: row[f] for f in FEATURES}
        predictions[row['site_id']] = estimator.predict(model_row, allow_csv_strings=True)
        site = {k: float(row[k]) for k in ('latitude', 'longitude', 'store_size_sqm', 'monthly_rent_inr', 'capex_inr', 'gross_margin_fraction')}
        site.update(site_id=row['site_id'], name=row['locality'], annual_opex_inr=float(row['annual_opex_excl_rent_inr']))
        sites.append(site)
    cells = [{**r, **{k: float(r[k]) for k in ('latitude', 'longitude', 'annual_wallet_inr')}} for r in rows(FINAL / 'spending_cells.csv')]
    pois = [{**r, 'latitude': float(r['latitude']), 'longitude': float(r['longitude'])} for r in rows(FINAL / 'pois.csv')]
    branches = [{**r, **{k: float(r[k]) for k in ('latitude', 'longitude', 'store_size_sqm', 'theta', 'variable_contribution_margin')}} for r in rows(FINAL / 'existing_stores.csv')]
    competitors = [dict(competitor_id=p['poi_id'], latitude=p['latitude'], longitude=p['longitude'],
                        store_size_sqm=100., theta=0., source_status='OSM_RECORD_WITH_ASSUMED_EQUAL_UNIT_ATTRACTION')
                   for p in pois if p['category'] == 'competitor']
    matrix = {}
    for r in rows(FINAL / 'daypart_weights.csv'):
        matrix.setdefault(r['category'], {})[r['time_bin']] = float(r['category_weight'])
    weights = dict(time_bins=list(TIME_BINS), category_weights=matrix, decay_scale_m=750., catchment_radius_m=1500.,
                   weight_version='weights-demo-1', unknown_hours_assumption=dict(availability_fraction=.5, evidence_weight=.5))
    availability = [{**r, 'availability_fraction': float(r['availability_fraction']), 'evidence_weight': float(r['evidence_weight'])}
                    for r in rows(FINAL / 'poi_daypart_availability.csv')]
    assumptions = {r['assumption_id']: r['value'] for r in rows(REVISED / 'project_assumptions.csv')}
    project = dict(project_id='bengaluru-offline-v1', city='Bengaluru', category='grocery',
                   budget_inr=float(assumptions['budget_inr']), discount_rate_fraction=float(assumptions['discount_rate_fraction']),
                   projection_years=int(assumptions['projection_years']), sites=sites, stores=branches, source_status='ASSUMED')
    project['inputs'] = dict(cells=cells, pois=pois, competitors=competitors, reference_predictions=predictions,
        weights=weights, availability=availability, outside=1., valuation_date='2026-10-24',
        poi_coverage_supported=True, feature_snapshot_id='bengaluru-features-20261024-v1',
        geographic_bounds=[12.815, 77.600, 12.940, 77.725],
        source_ids=['worldpop-2020', 'hces-2023-24', 'osm-pois', 'approved-weights', 'assumptions', 'package-config'],
        assumption_ids=['equal-external-mass-100sqm-theta0', 'gamma1-tau750-outside1', 'cell-centroid-allocation',
                        'synthetic-existing-branches', 'synthetic-financial-inputs', 'no-inflation-adjustment'],
        infrastructure=[], evidence_warnings=['HISTORICAL_MODELLED_POPULATION_2020', 'HCES_STATE_URBAN_SPENDING_2023_24',
                                             'NOMINAL_WALLET_2024_VS_SYNTHETIC_COSTS_2026', 'OSM_PARTIAL_COVERAGE',
                                             '100_CELL_CENTROID_APPROXIMATION', 'ASSUMED_EQUAL_COMPETITOR_ATTRACTION'])
    return project


def baseline_scenario(project):
    return dict(scenario_id='baseline-offline', project_id=project['project_id'], base_scenario_id=None,
                name='Offline baseline; synthetic business inputs', budget_inr=project['budget_inr'],
                assumptions=dict(demand_multiplier=1., rent_multiplier=1., site_overrides={},
                                 infrastructure_state='current', infrastructure_effect_fraction=0., opening_date=None, delay_months=24))


def protected_hashes():
    paths = []
    for directory in ['data/bengaluru', 'ml/bengaluru', 'ml/artifacts', 'ml/training/reference_sales', 'ml/training/reference_sales_v2',
                      'ml/training/data', 'ml/evaluation/reference_sales_v1', 'ml/evaluation/reference_sales_b1',
                      'ml/evaluation/reference_sales_v2']:
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in (ROOT/'ml/inference').glob('*.py'))
    paths.extend(ROOT/p for p in ['PART_B_COMPLETION_REPORT.md','PART_B1_HARDENING_REPORT.md','PART_B2_CORRECTION_REPORT.md'])
    return {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in sorted(set(paths))}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    if branch != 'ML':
        raise RuntimeError('Expected existing ML branch; no branch changes performed')
    preservation = protected_hashes()
    project = build_project(); scenario = baseline_scenario(project)
    start = perf_counter(); baseline = prepare_evaluation(project, scenario); elapsed = perf_counter()-start
    save(OUTPUT/'prepared_project.json', project)
    save(OUTPUT/'baseline.json', baseline)
    # Risk acknowledgements are NEVER implicit in the default recommendation.
    default = run_portfolio(project, baseline['context'], 2, [])
    risks = [a['site_id'] for a in baseline['evaluation']['site_analyses'] if a['failfast']['status']=='AT_RISK']
    start = perf_counter(); acknowledged = run_portfolio(project, baseline['context'], 10, risks); search_time=perf_counter()-start
    save(OUTPUT/'portfolios.json', dict(default_unacknowledged=default,
        illustrative_acknowledged_risk_policy=acknowledged, illustrative_acknowledgements=risks,
        policy_note='Acknowledged case is an explicit offline demonstration policy, not human investment approval',
        default_automatic_approval=False, portfolio_seconds=search_time))
    rescues = {s['site_id']: {lever: calculate_rescue(project, baseline['context'], s['site_id'], lever) for lever in ('rent', 'sales')}
               for s in project['sites']}
    save(OUTPUT/'rescues.json', rescues)
    # A separate hypothetical event exercises timing; no real operational metro
    # is falsely promoted to a future opening. Exact point/date/effect are assumptions.
    hypothetical = dict(infra_project_id='hypothetical-offline-connector', status='proposed', hypothetical_demo=True,
                        geometry=dict(type='Point', coordinates=[77.6472, 12.8808]), assumed_demo_open_date='2028-04-01',
                        source_id='explicit-offline-scenario-assumption')
    event_project = deepcopy(project); event_project['inputs']['infrastructure']=[hypothetical]
    states = {}
    for state in ('current', 'opens', 'delayed'):
        modified = deepcopy(scenario); modified['scenario_id']=f'hypothetical-{state}'
        modified['assumptions'].update(infrastructure_state=state, infrastructure_effect_fraction=.15)
        states[state] = prepare_evaluation(event_project, modified)
    save(OUTPUT/'hypothetical_infrastructure.json', dict(hypothetical_event=hypothetical, assumed_effect=.15, states=states))
    # Sensitivity/what-if evaluations retain the exact same source/features and
    # prediction records. No file is overwritten or missing routing imputed.
    changes = {}
    for name, key, factor in [('rent_plus_20pct', 'rent_multiplier', 1.2), ('demand_minus_20pct', 'demand_multiplier', .8)]:
        modified = deepcopy(scenario); modified['scenario_id']=name; modified['assumptions'][key]=factor
        changes[name] = prepare_evaluation(project, modified)['evaluation']
    save(OUTPUT/'scenario_comparisons.json', changes)
    lineages = [
        dict(output='reference_targets', source='revised_v2/site_features_enriched.csv + reference_sales_v2 saved artifact',
             transformation='Exact 20-feature allowlist, saved preprocessing and fitted capture times wallet; no own-branch features', kind='SYNTHETIC_MODEL_INFERENCE'),
        dict(output='daypart_profiles', source='final/pois.csv + poi_daypart_availability.csv + daypart_weights.csv',
             transformation='Geodesic 1500m selection, 750m decay, availability*evidence*category weight; weekly shares multiply [25,20,25,50,24,24] hours', kind='DERIVED_PROXY_WITH_ASSUMPTIONS'),
        dict(output='network_revenues', source='final/spending_cells.csv + pois.csv(category=competitor) + existing_stores.csv',
             transformation='100 source cell centroids; equal external mass area100/theta0; bounded calibration [-30,30]; full-set shares; no sales labels', kind='DERIVED_WITH_SYNTHETIC_BRANCHES_AND_ASSUMPTIONS'),
        dict(output='finance_rescue_rank_portfolio', source='revised_v2/site_features_enriched.csv + project_assumptions.csv + network revenues',
             transformation='OPEX renamed from annual_opex_excl_rent_inr; displacement contribution once; end-year discounting; inverse same-engine rescue; exact budget/count enumeration in paise', kind='DERIVED_FROM_SYNTHETIC_COSTS'),
        dict(output='hypothetical_scenarios', source='Explicit offline event point 12.8808,77.6472 / 2028-04-01 / +15% effect',
             transformation='ASSUMED distance exposure*dated active fraction on target once per year, delayed24months; no model feature reinference', kind='HYPOTHETICAL_NOT_OBSERVED')]
    save(OUTPUT/'field_lineage.json', lineages)
    changed=[p for p,h in preservation.items() if sha(ROOT/p)!=h]
    if changed or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=head:
        raise RuntimeError(f'Preservation failed: {changed}')
    summary = dict(engine_version='storescout-domain-1', head=head, branch=branch, evaluation_seconds=elapsed,
        portfolio_seconds=search_time, candidates=len(project['sites']), cells=len(project['inputs']['cells']),
        external_competitors=len(project['inputs']['competitors']), branches=len(project['stores']),
        model_artifact_id=baseline['evaluation']['model_artifact_id'], method_mode=baseline['evaluation']['method_mode'],
        status_counts={s:sum(a['failfast']['status']==s for a in baseline['evaluation']['site_analyses']) for s in ('VIABLE','AT_RISK','REJECTED','REVIEW_REQUIRED')},
        protected_files=len(preservation), protected_files_unchanged=True, preserved_sha256=preservation,
        max_conservation_error=max(d['base']['conservation_error'] for d in baseline['diagnostics']['site_details'].values()),
        notes=['Domain completed; API/UI/persistence integration remains backend/frontend-owned', 'No empirical accuracy or investment approval claimed',
               'Historical B2 tests that require pipeline stubs are obsolete after authorized domain implementation; preserved unchanged'])
    save(OUTPUT/'run_summary.json', summary)
    save(OUTPUT/'checksums.json', {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in OUTPUT.glob('*.json') if p.name!='checksums.json'})
    print(json.dumps({k:v for k,v in summary.items() if k!='preserved_sha256'}, indent=2))


if __name__ == '__main__':
    main()
