"""Public product preview computed from the shared source snapshot, never accounts."""
from copy import deepcopy
from functools import lru_cache
from . import catalogue, gateway, sources, presentation


@lru_cache(maxsize=2)
def preview(snapshot_hash, model_hash, engine_hash):
    project = sources.project_data()
    project['inputs'] = sources.installed_snapshot()
    scenario = catalogue.scenario('demo', 'baseline')
    prepared = gateway.invoke('prepare_evaluation', deepcopy(project), deepcopy(scenario))
    public = presentation.evaluation(prepared, project, scenario, snapshot_hash)
    event = project['inputs']['infrastructure'][0]
    analyses = {'current': {a['site_id']: a for a in public['site_analyses']}}
    for state in ('current', 'opens', 'delayed'):
        if state == 'current':
            continue
        else:
            changed = deepcopy(scenario)
            changed['assumptions'].update(infrastructure_state=state, infrastructure_effect_fraction=event['assumed_effect_fraction'], delay_months=event['delay_months'])
            evaluation = gateway.invoke('prepare_evaluation', deepcopy(project), changed)['evaluation']
            analyses[state] = {a['site_id']: a for a in evaluation['site_analyses']}
    # Focus this feature preview on the largest computed infrastructure change,
    # rather than implying the most profitable site is the most affected.
    sid = max(analyses['current'], key=lambda sid: abs(analyses['opens'][sid]['npv_inr']-analyses['current'][sid]['npv_inr']))
    site = next(s for s in project['sites'] if s['site_id'] == sid)
    baseline = analyses['current'][sid]
    scenarios = [dict(state=state, npv_inr=result[sid]['npv_inr'], annual_revenue_inr=result[sid]['annual_revenue_inr'],
                      delta_npv_inr=result[sid]['npv_inr']-baseline['npv_inr']) for state, result in analyses.items()]
    return dict(city=project['city'], site_id=sid, site_name=site['name'], method_mode=public['method_mode'],
                model_artifact_id=public['model_artifact_id'], dayparts=baseline['dayparts'], infrastructure=event,
                scenarios=scenarios, projection_years=project['projection_years'], limitations=sources.LIMITATIONS,
                feature_snapshot_id=sources.FEATURE_SNAPSHOT_ID)


def load():
    snapshot = sources.installed_snapshot()
    bundle = sources.model_bundle()
    return preview(snapshot['snapshot_hash'], bundle['card_sha256'], sources.engine_identity())
