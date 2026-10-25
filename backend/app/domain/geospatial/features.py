"""WGS84 geodesic geometry and explicitly supported POI opportunity proxies."""
import numpy as np
from ..validation import number, unique

TIME_BINS = ('weekday_morning', 'weekday_lunch', 'weekday_evening',
             'weekday_night', 'weekend_day', 'weekend_evening')
WEEKLY_HOURS = np.array([25., 20., 25., 50., 24., 24.])
CATEGORIES = ('office', 'school', 'hospital', 'transit', 'shopping', 'leisure')


def coordinates(rows):
    return np.array([[number(r['latitude'], 'latitude', minimum=-90, maximum=90),
                      number(r['longitude'], 'longitude', minimum=-180, maximum=180)]
                     for r in rows], dtype=float).reshape(-1, 2)


def distances(left, right):
    """Pairwise great-circle metres; never interpret decimal degrees as metres."""
    a, b = np.deg2rad(coordinates(left)), np.deg2rad(coordinates(right))
    lat = b[None, :, 0] - a[:, None, 0]
    lon = b[None, :, 1] - a[:, None, 1]
    h = np.sin(lat / 2)**2 + np.cos(a[:, None, 0]) * np.cos(b[None, :, 0]) * np.sin(lon / 2)**2
    return 2 * 6371000. * np.arcsin(np.sqrt(np.minimum(h, 1.)))


def daypart_profiles(sites, pois, weights, *, availability=None, coverage_supported=False):
    """Raw per nominal hour and duration-weighted weekly shares are distinct.

    Unknown hours require a declared neutral assumption. Availability records
    override it; no parser guesses unsupported OSM opening-hours expressions.
    Supported empty coverage yields six zeroes; unknown coverage yields nulls.
    """
    unique(sites, 'site_id', 10)
    unique(pois, 'poi_id')
    radius = number(weights['catchment_radius_m'], 'catchment radius', minimum=0)
    decay = number(weights['decay_scale_m'], 'daypart decay', minimum=1)
    matrix = weights['category_weights']
    if tuple(weights['time_bins']) != TIME_BINS:
        raise ValueError('Six canonical Asia/Kolkata time bins required')
    lookup = {}
    for row in availability or []:
        key = row['poi_id'], row['time_bin']
        if key in lookup or key[1] not in TIME_BINS:
            raise ValueError('Duplicate or unknown POI availability bin')
        lookup[key] = row
    default = weights.get('unknown_hours_assumption')
    d = distances(sites, pois)
    results = {}
    for i, site in enumerate(sites):
        raw = np.zeros(6)
        support, assumed, source_ids = set(), set(), set()
        for j, poi in enumerate(pois):
            if d[i, j] > radius or poi['category'] not in matrix:
                continue
            support.add(poi['poi_id'])
            source_ids.update(poi.get('source_id', '').split(';'))
            for k, bin_name in enumerate(TIME_BINS):
                record = lookup.get((poi['poi_id'], bin_name))
                if record is None:
                    if default is None:
                        raise ValueError('Unknown hours require an explicit neutral availability assumption')
                    record = default
                    assumed.add(poi['poi_id'])
                elif str(record.get('availability_status', '')).startswith('ASSUMED'):
                    assumed.add(poi['poi_id'])
                availability_value = number(record['availability_fraction'], 'availability', minimum=0, maximum=1)
                evidence = number(record['evidence_weight'], 'evidence weight', minimum=0, maximum=1)
                weight = number(matrix[poi['category']][bin_name], 'category weight', minimum=0)
                raw[k] += weight * np.exp(-d[i, j] / decay) * availability_value * evidence
        weekly = raw * WEEKLY_HOURS
        total = float(weekly.sum())
        known = bool(coverage_supported)
        results[site['site_id']] = dict(
            raw=dict(zip(TIME_BINS, raw.tolist())) if known else dict.fromkeys(TIME_BINS),
            weekly_exposure_share=dict(zip(TIME_BINS, (weekly / total).tolist())) if known and total else dict.fromkeys(TIME_BINS, 0. if known else None),
            coverage_status='SUPPORTED_MAPPED_COVERAGE' if known else 'UNKNOWN_COVERAGE',
            support_count=len(support), assumed_hours_count=len(assumed),
            source_ids=sorted(source_ids - {''}), weight_version=weights['weight_version'],
            timezone='Asia/Kolkata', weekly_bin_hours=WEEKLY_HOURS.tolist(),
            interpretation='POI-derived opportunity; not measured visits or footfall',
            coverage_caveat='Mapped coverage is partial and does not establish absence of unmapped POIs')
    return results
