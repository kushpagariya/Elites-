"""Verified I/O boundary for the delivered Bengaluru model and source snapshot."""
import copy
import csv
import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path
from ..repositories.store import fingerprint
from ..schemas import Project, Store
from .errors import ServiceError

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / 'data/bengaluru'
FEATURE_SNAPSHOT_ID = 'bengaluru-features-20261024-v1'
VALUATION_DATE = '2026-10-24'
LIMITATIONS = [
    'CatBoost was trained on synthetic sales targets; real store-sales accuracy is not validated.',
    'Shifted-market degradation requires human review; no automatic investment approval.',
    'Downside/base/upside are sensitivity cases, not calibrated prediction intervals.',
    'WorldPop 2020 and HCES 2023–24 spending use historical nominal prices; costs are assumed for 2026 without inflation adjustment.',
    'OSM coverage is partial; competitor attraction, existing branches and financial inputs are assumed.',
    '100 spending-cell centroids and straight-line catchments approximate geography, not travel times.',
    'Future metro opening dates and commercial effects are scenario assumptions; proximity uses a representative OSM geometry point, not a verified station.',
]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_bundle():
    directory = ROOT / 'ml/artifacts/reference_sales_v2'
    try:
        manifest_path = directory / 'manifest.json'
        manifest = read_json(manifest_path)
        approved = read_json(ROOT / 'ml/evaluation/decision_engine_v1/artifact_bundle_manifest.json')
        hashes = {}
        for name, expected in approved['files'].items():
            path = (directory / name).resolve()
            if not path.is_relative_to(directory.resolve()) or not path.is_file() or sha(path) != expected:
                raise ValueError('Artifact verification failed')
            hashes[name] = expected
        if manifest['model_artifact_id'] != approved['model_artifact_id'] or manifest['method_mode'] != 'model_simulated' or not manifest.get('activation_passed'):
            raise ValueError('Unapproved model manifest')
        card = dict(method_mode=manifest['method_mode'], model_artifact_id=manifest['model_artifact_id'],
                    estimator_version=manifest['model_artifact_id'], feature_schema='reference-sales-features-v2',
                    trained_model_available=True, metrics=None, limitations=LIMITATIONS)
        return dict(card=card, artifact_sha256=hashes[manifest['selected_file']],
                    card_sha256=fingerprint({'manifest': sha(manifest_path), 'files': hashes}))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logging.getLogger(__name__).exception('Verified model artifact check failed')
        raise ServiceError(503, 'MODEL_UNAVAILABLE', 'Location analysis is temporarily unavailable. Your saved work is still accessible. Please retry shortly.') from exc


def restore_packaged_model():
    """Restore only the approved bundle; never replace differing installed files."""
    from ml.decision_engine.package import ALLOWED, ARTIFACTS, install_bundle
    if any(not (ARTIFACTS / name).is_file() for name in ALLOWED):
        logging.getLogger(__name__).info('Restoring the approved model from its verified deployment bundle')
        install_bundle(destination=ARTIFACTS)
    return model_bundle()


def geographic_snapshot():
    """Mapped evidence is available even if fitted-model inference is unavailable."""
    try:
        pois = [{**r, 'latitude': float(r['latitude']), 'longitude': float(r['longitude'])}
                for r in csv_rows(DATA_ROOT / 'final/pois.csv')]
        cells = [{**r, **{k: float(r[k]) for k in ('latitude', 'longitude', 'annual_wallet_inr')}}
                 for r in csv_rows(DATA_ROOT / 'final/spending_cells.csv')]
        return dict(pois=pois, cells=cells, weights=dict(catchment_radius_m=1500.))
    except (OSError, ValueError, KeyError) as exc:
        logging.getLogger(__name__).exception('Mapped source snapshot could not be loaded')
        raise ServiceError(503, 'SOURCE_UNAVAILABLE', 'Neighbourhood data is temporarily unavailable. Please retry.') from exc


def engine_identity():
    paths = list((ROOT / 'backend/app/domain').rglob('*.py')) + list((ROOT / 'ml/inference').glob('*.py'))
    paths += [Path(__file__), ROOT / 'ml/decision_engine/run.py', ROOT / 'backend/app/services/presentation.py']
    return fingerprint({str(p.relative_to(ROOT)): sha(p) for p in sorted(paths) if p.is_file()})


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def project_data():
    try:
        sites = []
        for r in csv_rows(DATA_ROOT / 'revised_v2/site_features_enriched.csv'):
            s = {k: float(r[k]) for k in ('latitude', 'longitude', 'store_size_sqm', 'monthly_rent_inr', 'capex_inr', 'gross_margin_fraction')}
            sites.append(dict(s, site_id=r['site_id'], name=r['locality'], annual_opex_inr=float(r['annual_opex_excl_rent_inr'])))
        stores = [{k: r[k] if k in ('store_id', 'name') else float(r[k]) for k in Store.model_fields} for r in csv_rows(DATA_ROOT / 'final/existing_stores.csv')]
        a = {r['assumption_id']: r['value'] for r in csv_rows(DATA_ROOT / 'revised_v2/project_assumptions.csv')}
        return Project(project_id='demo', city='Bengaluru', category='grocery', budget_inr=float(a['budget_inr']),
                       discount_rate_fraction=float(a['discount_rate_fraction']), projection_years=int(a['projection_years']),
                       sites=sites, stores=stores, source_status='ASSUMED').model_dump(mode='json')
    except (OSError, ValueError, KeyError) as exc:
        raise ServiceError(503, 'SOURCE_UNAVAILABLE', 'The Bengaluru project dataset is missing or invalid.') from exc


def snapshot_hashes():
    paths = [DATA_ROOT / 'final' / n for n in ('spending_cells.csv', 'pois.csv', 'existing_stores.csv', 'daypart_weights.csv', 'poi_daypart_availability.csv')]
    paths += [DATA_ROOT / 'revised_v2' / n for n in ('site_features_enriched.csv', 'project_assumptions.csv')]
    paths += [DATA_ROOT / 'revised_v2/infrastructure.csv', DATA_ROOT / 'final/infrastructure_geometry.geojson']
    try:
        return {str(p.relative_to(ROOT)): sha(p) for p in paths}
    except OSError as exc:
        raise ServiceError(503, 'SOURCE_UNAVAILABLE', 'The frozen Bengaluru sources are unavailable.') from exc


def infrastructure_event():
    """Explicit Point proxy for the supplied engine's one-event contract."""
    row = next(r for r in csv_rows(DATA_ROOT / 'revised_v2/infrastructure.csv') if r['included_current_baseline'].lower() == 'false')
    features = read_json(DATA_ROOT / 'final/infrastructure_geometry.geojson')['features']
    points = [point for f in features if f['properties']['infra_project_id'] == row['infra_project_id']
              for point in f['geometry']['coordinates'] if f['geometry']['type'] == 'LineString']
    if not points:
        raise ServiceError(503, 'SOURCE_UNAVAILABLE', 'Future infrastructure has no supported source geometry.')
    # Select an actual OSM vertex nearest the mean; no invented coordinates.
    centre = [sum(p[i] for p in points) / len(points) for i in (0, 1)]
    point = min(points, key=lambda p: sum((p[i] - centre[i]) ** 2 for i in (0, 1)))
    return dict(infra_project_id=row['infra_project_id'], name=row['name'], status=row['status'].lower(),
                hypothetical_demo=True, geometry=dict(type='Point', coordinates=point), expected_open_date=None,
                assumed_demo_open_date=row['hypothetical_open_date'], source_id=row['source_id'], source_status='ASSUMED',
                assumed_effect_fraction=float(row['assumed_demand_effect_fraction']), delay_months=int(row['delay_months']),
                official_source_url=row['official_source_url'], geometry_note='Representative OSM vertex; assumed proximity proxy, not a verified station.')


@lru_cache(maxsize=2)
def _snapshot(source_hash, model_hash, code_hash):
    # Reuse the ML team's exact CSV mapping and inference path. This helper has
    # no write effects; its offline report runner is guarded by __main__.
    from ml.decision_engine.run import build_project
    try:
        project = build_project()
        inputs = project['inputs']
        event = infrastructure_event()
        inputs['infrastructure'] = [event]
        inputs['source_ids'] = sorted(set(inputs['source_ids'] + event['source_id'].split(';')))
        inputs['source_manifest'] = dict(feature_snapshot_id=FEATURE_SNAPSHOT_ID, source_ids=inputs['source_ids'])
        return inputs
    except (OSError, ValueError, KeyError, ImportError) as exc:
        logging.getLogger(__name__).exception('Fitted-model inference or source initialization failed')
        raise ServiceError(503, 'MODEL_UNAVAILABLE', 'The fitted model or its Bengaluru input snapshot could not be loaded.') from exc


def load_snapshot(feature_snapshot_id):
    if feature_snapshot_id != FEATURE_SNAPSHOT_ID:
        raise ServiceError(409, 'STALE_SNAPSHOT', 'This workspace uses the Bengaluru model snapshot. Refresh the page before evaluating.')
    hashes, bundle = snapshot_hashes(), model_bundle()
    identity = fingerprint(hashes)
    values = copy.deepcopy(_snapshot(identity, bundle['card_sha256'], engine_identity()))
    return {**values, 'snapshot_hash': identity, 'source_hashes': hashes}


def installed_snapshot():
    return load_snapshot(FEATURE_SNAPSHOT_ID)
