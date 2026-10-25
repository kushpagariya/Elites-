"""Account-scoped view restoration; never re-run saved financial calculations."""
from ..repositories import store
from ..schemas import WorkspaceState
from . import analytics, catalogue
from .errors import ServiceError


def view(project_id, scenario_id=None):
    catalogue.project(project_id)
    value = (store.get('workspace_scenario', project_id, scenario_id) if scenario_id else
             store.get('workspace', project_id, 'current'))
    sid = scenario_id or (value or {}).get('scenario_id', 'baseline')
    catalogue.scenario(project_id, sid)
    if not value:
        value = WorkspaceState(scenario_id=sid).model_dump(mode='json')
        matches = [e for e in store.list_objects('evaluation', project_id) if e['scenario_id'] == sid]
        if matches:
            value['evaluation_id'] = max(matches, key=lambda e: (e['created_at_utc'], e['evaluation_id']))['evaluation_id']
    fresh = False
    if value['evaluation_id']:
        try:
            analytics.context_for(project_id, value['evaluation_id'])
            fresh = True
        except ServiceError:
            pass
    return {**value, 'analysis_current': fresh}


def save(project_id, body):
    project = catalogue.project(project_id)
    catalogue.scenario(project_id, body.scenario_id)
    if len(set(body.selected_site_ids)) != len(body.selected_site_ids) or set(body.selected_site_ids) - {s.site_id for s in project.sites}:
        raise ServiceError(422, 'INVALID_INPUT', 'Comparison accepts at most two distinct candidate locations.')
    if body.evaluation_id:
        evaluation = analytics.saved(project_id, 'evaluation', body.evaluation_id)
        if evaluation['scenario_id'] != body.scenario_id:
            raise ServiceError(409, 'CONTEXT_MISMATCH', 'The saved analysis belongs to a different scenario.')
    if body.portfolio_run_id:
        plan = analytics.saved(project_id, 'portfolio', body.portfolio_run_id)
        if plan['evaluation_id'] != body.evaluation_id:
            raise ServiceError(409, 'CONTEXT_MISMATCH', 'The saved plan belongs to a different analysis.')
    if body.comparison:
        pair = body.comparison
        for sid, eid in ((pair.before_scenario_id, pair.before_evaluation_id), (pair.after_scenario_id, pair.after_evaluation_id)):
            catalogue.scenario(project_id, sid)
            if analytics.saved(project_id, 'evaluation', eid)['scenario_id'] != sid:
                raise ServiceError(409, 'CONTEXT_MISMATCH', 'Before/after analysis does not match its saved scenario.')
        if pair.after_scenario_id != body.scenario_id or pair.after_evaluation_id != body.evaluation_id:
            raise ServiceError(409, 'CONTEXT_MISMATCH', 'Comparison result must be the displayed analysis.')
    value = body.model_dump(mode='json')
    store.save_workspace(project_id, value)
    return value
