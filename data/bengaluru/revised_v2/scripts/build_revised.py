"""Offline v2 data correction. Reads frozen v1; writes inside revised_v2 only.

No predictive fitting, allocation, financial evaluation or ranking is performed.
"""
from __future__ import annotations
import csv
import datetime as dt
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
from pyproj import Geod
from pypdf import PdfReader

V2 = Path(__file__).resolve().parents[1]
ROOT = V2.parents[2]
BASE = V2.parent
FROZEN = BASE / 'final'
REVISION = 'bengaluru-integrity-v2'
ASOF = '2026-10-24'
TZ = 'Asia/Kolkata'
MANIFEST_V2 = 'bengaluru-sources-20261024-v2'
G = Geod(ellps='WGS84')
BINS = {
    'weekday_morning': (6, 11, 5), 'weekday_lunch': (11, 15, 5),
    'weekday_evening': (15, 20, 5), 'weekday_night': (20, 30, 5),
    'weekend_day': (6, 18, 2), 'weekend_evening': (18, 30, 2),
}
EXTRA = [b + '_weekly_exposure_share' for b in BINS] + [
    'daypart_poi_support_count', 'daypart_recorded_hours_support_count',
    'daypart_assumed_hours_support_count', 'daypart_recorded_hours_fraction',
    'mapped_supermarket_count_1500m', 'mapped_convenience_count_1500m',
    'mapped_grocery_count_1500m', 'operational_metro_station_count_1500m',
    'ward_2011_id', 'ward_2025_id', 'metro_sep2025_weekday_observation_hours',
    'metro_sep2025_weekday_observed_days', 'metro_sep2025_weekend_observation_hours',
    'metro_sep2025_weekend_observed_days',
]
TABLES = {}

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_json(name, value):
    (V2 / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def write(name, rows, columns=None):
    rows = list(rows)
    columns = columns or list(rows[0])
    with (V2 / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='raise')
        w.writeheader()
        w.writerows(rows)
    TABLES[name.removesuffix('.csv')] = rows
    return rows

def dist(a, b):
    return G.inv(float(a['longitude']), float(a['latitude']), float(b['longitude']), float(b['latitude']))[2]

def preserved_baseline():
    saved = load(V2 / 'baseline_hashes.json')
    errors = [p for p, value in saved['files'].items() if not (ROOT / p).exists() or sha(ROOT / p) != value]
    if errors:
        raise ValueError('Frozen baseline changed: ' + str(errors))
    return saved

def parse_hces_statement3u(text):
    """Parse numbered records across wrapped lines, retaining source item IDs."""
    stop = re.split(r'\n\s*\*excludes', text, maxsplit=1)[0]
    records = re.findall(r'(?ms)^\s*(\d{1,2})\.\s+(.*?)(?=^\s*\d{1,2}\.\s+|\Z)', stop)
    result = {}
    for sid, body in records:
        if int(sid) in result:
            raise ValueError('Duplicate HCES item ' + sid)
        values = list(re.finditer(r'(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}(?!\d)', body))
        if not values:
            raise ValueError('No numeric Karnataka value for HCES item ' + sid)
        label = re.sub(r'\s+', ' ', body[:values[0].start()]).strip(' -')
        result[int(sid)] = (label, Decimal(values[-1].group().replace(',', '')))
    if set(result) != set(range(1, 33)):
        raise ValueError('Incomplete or duplicate HCES extraction: ' + str(sorted(result)))
    return result

def correct_expenditure():
    pdf = BASE / 'raw/hces_2023_24_full.pdf'
    text = PdfReader(pdf).pages[89].extract_text()
    parsed = parse_hces_statement3u(text)
    old = {int(r['item_id']): r for r in read(FROZEN / 'expenditure_inputs.csv')}
    for key, row in old.items():
        if parsed[key][1] != Decimal(row['monthly_per_capita_inr']):
            raise ValueError('HCES extraction disagrees with unchanged baseline item ' + str(key))
    rows = []
    for key in range(1, 33):
        if key in old:
            rows.append(dict(old[key]))
        else:
            row = dict(old[23])
            row.update(item_id=key, item_category='consumer services excluding conveyance', monthly_per_capita_inr=str(parsed[key][1]))
            rows.append(row)
    grocery = sum(parsed[i][1] for i in range(1, 14)) + Decimal('0.5') * parsed[14][1] + parsed[18][1] + parsed[19][1]
    assert grocery == Decimal('2974.915') and parsed[24][1] == Decimal('404.46')
    write('expenditure_inputs.csv', rows)
    save_json('expenditure_processing.json', dict(source_path=pdf.relative_to(ROOT).as_posix(), source_sha256=sha(pdf),
        source_id='hces-2023-24', locator='PDF page 90 / printed S11 / Statement 3U / column 14 Karnataka Urban',
        reference_period='2023-08-01/2024-07-31', currency='INR', price_basis='Nominal 2023-24 survey prices; no inflation adjustment',
        item24_method='Numbered-record parser joins continuation lines before selecting the final numeric column',
        grocery_monthly_per_capita_inr=str(grocery), baseline_grocery_calculation_unchanged=True, original_31_records_unchanged=True))

def correct_sources():
    evidence_path = V2 / 'source_verification/verification_log.json'
    evidence = load(evidence_path) if evidence_path.exists() else []
    verified = [r for r in evidence if r.get('verified_release_date') == '2025-01-30' and r.get('date_and_release_statement_verified')]
    release = '2025-01-30' if verified else None
    rows = []
    for old in read(FROZEN / 'source_manifest.csv'):
        r = dict(old)
        r.update(source_manifest_id=MANIFEST_V2, baseline_source_manifest_id=old['source_manifest_id'], provenance_revision_id=REVISION,
            legacy_release_date=old['release_date'] or None, release_date_status='UNVERIFIED' if not old['release_date'] else 'INHERITED_RECORDED_DATE',
            release_evidence_source_ids=None, reference_year=None, boundary_vintage=None, reference_period_kind='SOURCE_OBSERVATION_OR_EVENT',
            original_acquisition_record='source_acquisitions.csv; unchanged original URL/timestamp/hash', metadata_correction=None)
        sid = r['source_id']
        if sid in ['worldpop-2020', 'census-2011', 'wards-2012', 'wards-2025']:
            r['observation_start_date'] = r['observation_end_date'] = None
            r['reference_year'] = {'worldpop-2020': 2020, 'census-2011': 2011, 'wards-2012': 2012, 'wards-2025': 2025}[sid]
            r['reference_period_kind'] = 'MODEL_REFERENCE_YEAR' if sid == 'worldpop-2020' else 'CENSUS_REFERENCE_YEAR' if sid == 'census-2011' else 'BOUNDARY_VINTAGE'
            r['boundary_vintage'] = '2012' if sid == 'wards-2012' else '2025-12' if sid == 'wards-2025' else None
            r['metadata_correction'] = 'Calendar bounds were reference-year placeholders, not verified exact observation dates. Exact release remains unknown.'
        if sid == 'hces-2023-24':
            r.update(release_date=release, release_date_status='VERIFIED_OFFICIAL_PRESS_NOTE' if release else 'UNVERIFIED',
                release_evidence_source_ids=';'.join(x['source_id'] for x in verified) or None,
                metadata_correction='Corrected 2025-01-31 to official detailed-report release 2025-01-30; factsheet release is separately 2024-12-27.' if release else 'Exact detailed-report publication day could not be verified; retained unknown.')
        if sid == 'blue-official':
            r.update(observation_start_date=None, observation_end_date=None, reference_period_kind='REPORT_REFERENCE_PERIOD_NOT_STATUS_DATE',
                metadata_correction='2025-26 report context and OSM extraction do not establish a dated official commissioning observation.')
        if sid in ['approved-weights', 'assumptions', 'package-config']:
            r.update(observation_start_date=None, observation_end_date=None, release_date=None,
                release_date_status='NOT_APPLICABLE_INTERNAL_CONFIGURATION', reference_period_kind='CONFIGURATION_NOT_OBSERVATION',
                metadata_correction='Scenario valuation and local creation dates are not external observation or publication dates; original values remain in frozen v1.')
        rows.append(r)
    for ev in evidence:
        if ev['status'] != 'DOWNLOADED':
            continue
        r = {key: None for key in rows[0]}
        r.update(source_id=ev['source_id'], source_manifest_id=MANIFEST_V2, provenance_revision_id=REVISION,
            title='MoSPI HCES detailed-report release press note' if ev['source_id'].endswith('note') else 'PIB HCES detailed-report release announcement',
            source_url=ev['url'], licence='Government press publication; attribution retained', observation_start_date=release, observation_end_date=release,
            release_date=release, release_date_status='VERIFIED_OFFICIAL_PRESS_NOTE' if release else 'UNVERIFIED',
            retrieval_date=ev['response_completed_at_utc'][:10], timezone=TZ, geographic_scope='India', source_status='PUBLIC_SOURCE',
            notes='Release verification only, not a replacement for survey observations.', original_acquisition_record=ev['local_path'],
            reference_period_kind='PUBLICATION_EVENT', metadata_correction='New verification evidence; source file and request/completion timestamps preserved.')
        rows.append(r)
    r = {key: None for key in rows[0]}
    project = ROOT / 'data/demo/project.json'
    r.update(source_id='approved-project', source_manifest_id=MANIFEST_V2, provenance_revision_id=REVISION,
        title='Approved existing repository project defaults', source_url='data/demo/project.json', licence='Repository fixture',
        timezone=TZ, source_status='ASSUMED', geographic_scope='Project configuration', reference_period_kind='CONFIGURATION_NOT_OBSERVATION',
        notes='Budget, discount rate and horizon only; no Navi Mumbai coordinates copied.', original_acquisition_record=project.relative_to(ROOT).as_posix(),
        metadata_correction='Added explicit fixture provenance; no external observation or release date asserted.')
    rows.append(r)
    write('source_manifest.csv', rows)
    original = read(FROZEN / 'acquisition_files.csv')
    acquisitions = []
    for old in original:
        acquisitions.append(dict(old, request_started_at_utc=old['retrieved_at_utc'], response_completed_at_utc=None,
            timestamp_semantics='LEGACY_RETRIEVED_FIELD_IS_REQUEST_START', file_scope='FROZEN_BASELINE_REFERENCE_ONLY'))
    for ev in evidence:
        acquisitions.append(dict(url=ev['url'], path='data/bengaluru/revised_v2/' + ev.get('local_path', ''), status=ev['status'],
            bytes=ev.get('bytes'), sha256=ev.get('sha256'), retrieved_at_utc=ev['request_started_at_utc'], content_type=ev.get('content_type'), last_modified=None,
            error=ev.get('error'), request_started_at_utc=ev['request_started_at_utc'], response_completed_at_utc=ev.get('response_completed_at_utc'),
            timestamp_semantics='EXPLICIT_REQUEST_START_AND_RESPONSE_COMPLETION', file_scope='V2_RELEASE_VERIFICATION'))
    write('source_acquisitions.csv', acquisitions)
    return release

def correct_infrastructure():
    rows = []
    for old in read(FROZEN / 'infrastructure.csv'):
        r = dict(old)
        r.update(legacy_status_reference_date=old['status_reference_date'], legacy_status_verification_date=old['status_verification_date'],
            status_reference_date=None, status_verification_date=None, official_status_date_verification='UNKNOWN_NOT_NEWLY_VERIFIED',
            local_metadata_review_date=dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30))).date().isoformat(),
            baseline_valuation_date=ASOF, official_opening_date_status='UNKNOWN',
            scenario_date_status='ASSUMED_NOT_OFFICIAL' if old['hypothetical_open_date'] else 'NOT_APPLICABLE_OPERATIONAL_BASELINE',
            status_evidence_basis='Verified 2025-08-10 inauguration plus September 2025 operational counts; no fresh official status observation date' if old['infra_project_id'] == 'metro-yellow' else 'Historical 2025-26 government report and 2026-10-24 OSM construction tags; neither is a verified current official opening',
            provenance_revision_id=REVISION)
        rows.append(r)
    write('infrastructure.csv', rows)
    write('infrastructure_scenarios.csv', read(FROZEN / 'infrastructure_scenarios.csv'))

def assumptions(master):
    rows = read(FROZEN / 'synthetic_assumptions.csv')
    for site in master:
        template = dict(rows[0])
        template.update(table='candidate_sites', record_id=site['site_id'], field_name='locality', generated_value=site['locality'], unit='place label',
            source_status='SYNTHETIC_DEMO', assumption_id='candidate-locality', low=None, base=site['locality'], high=None,
            reason='Repair missing provenance for an already frozen analyst-selected locality anchor; no new observed premise asserted.',
            method_version='v2 provenance repair of build.py:build_sites fixed anchors', source_id='assumptions', benchmark_url=None, price_basis=None)
        rows.append(template)
        q = dict(template)
        q.update(table='site_features', field_name='source_quality_score', generated_value=site['source_quality_score'], unit='fixed fraction', source_status='ASSUMED',
            assumption_id='legacy-evidence-family-indicator', base=site['source_quality_score'], low=None, high=None,
            reason='Existing literal 6/8 metadata retained unchanged; not prediction confidence or observation reliability.')
        rows.append(q)
    r = dict(rows[-1])
    r.update(table='population_processing', record_id='worldpop-2020', field_name='within_pixel_density_method', generated_value='uniform', base='uniform',
        assumption_id='uniform-within-pixel-population', unit='spatial redistribution method', source_status='ASSUMED',
        reason='Document existing baseline method only: constant density within each 1km source pixel; not a new population observation.')
    rows.append(r)
    write('synthetic_assumptions.csv', rows)
    project_rows = read(FROZEN / 'project_assumptions.csv')
    for r in project_rows:
        if r['assumption_id'] in ['budget_inr', 'discount_rate_fraction', 'projection_years']:
            r['source_id'] = 'approved-project'
        elif r['assumption_id'] == 'population_reference_year':
            r['source_id'] = 'worldpop-2020'
        elif r['assumption_id'] == 'wallet_price_year':
            r['source_id'] = 'hces-2023-24'
        elif r['assumption_id'] == 'valuation_date':
            r['source_id'] = 'package-config'
    write('project_assumptions.csv', project_rows)
    grouped = defaultdict(list)
    for r in rows:
        grouped[r['assumption_id']].append(r)
    for r in project_rows:
        if r['assumption_id'] not in grouped:
            grouped[r['assumption_id']].append(dict(source_id=r['source_id'], source_status=r['source_status'], reason=r['notes']))
    registry = []
    for aid, rr in sorted(grouped.items()):
        registry.append(dict(assumption_id=aid, source_ids=';'.join(sorted({s for r in rr for s in r['source_id'].split(';')})),
            origin_statuses=';'.join(sorted({r['source_status'] for r in rr})), referenced_value_records=len(rr),
            description=rr[0]['reason'], provenance_revision_id=REVISION,
            scope='Existing approved parameter, configuration, method assumption or synthetic demo input; not a measured observation'))
    write('assumption_registry.csv', registry)

def daypart_and_enrichment(master):
    profiles = read(FROZEN / 'daypart_profiles.csv')
    pois = read(FROZEN / 'pois.csv')
    stations = read(FROZEN / 'metro_station_lookup.csv')
    averages = {(r['station_id'], r['day_type']): r for r in read(FROZEN / 'metro_activity_averages.csv')}
    wards = {r['site_id']: r for r in read(FROZEN / 'site_ward_lookup.csv')}
    grouped = defaultdict(list)
    for r in profiles:
        grouped[r['site_id']].append(r)
    support = []
    enriched = []
    revised_profiles = []
    for site in master:
        sid = site['site_id']
        pp = grouped[sid]
        assert len(pp) == 6 and {r['time_bin'] for r in pp} == set(BINS)
        near = [p for p in pois if dist(site, p) <= 1500]
        used = [p for p in near if p['category'] in ['office', 'shopping', 'leisure', 'school', 'hospital', 'transit']]
        counts = {}
        for field in ['poi_support_count', 'recorded_hours_support_count', 'assumed_hours_support_count']:
            values = {int(p[field]) for p in pp}
            assert len(values) == 1
            counts[field] = values.pop()
        recorded = sum(bool(p['opening_hours']) for p in used)
        total = len(used)
        parsed = counts['recorded_hours_support_count']
        assert counts['poi_support_count'] == total and parsed <= recorded <= total
        fraction = parsed / total if total else None
        support.append(dict(site_id=sid, poi_support_count=total, recorded_hours_support_count=parsed,
            assumed_hours_support_count=total-parsed, recorded_hours_support_fraction=fraction,
            opening_hours_recorded_count=recorded, opening_hours_unsupported_count=recorded-parsed,
            opening_hours_missing_count=total-recorded, opening_hours_recorded_fraction=recorded/total if total else None,
            coverage_status='PARTIAL_RECORDED_HOURS_ASSUMPTIONS_USED' if parsed < total else 'ALL_SUPPORT_HOURS_PARSED',
            has_assumed_hours=parsed < total, source_id='osm-pois;approved-weights;assumptions',
            source_snapshot_date=ASOF, data_role='POI_OPPORTUNITY_NOT_MEASURED_STORE_FOOTFALL'))
        row = dict(site)
        for b in BINS:
            p = next(p for p in pp if p['time_bin'] == b)
            start, end, days = BINS[b]
            assert int(p['duration_hours']) == end-start and int(p['starting_days_per_week']) == days
            row[b+'_weekly_exposure_share'] = p['weekly_exposure_share']
            rp = dict(p)
            rp.update(recorded_hours_support_fraction=fraction, coverage_status=support[-1]['coverage_status'],
                has_assumed_hours=parsed < total, period_basis='REPRESENTATIVE_WEEK_POI_PROXY_NOT_OBSERVED_SERVICE_PERIOD',
                observed_service_period_complete=None, provenance_revision_id=REVISION)
            revised_profiles.append(rp)
        row.update(daypart_poi_support_count=total, daypart_recorded_hours_support_count=parsed,
            daypart_assumed_hours_support_count=total-parsed, daypart_recorded_hours_fraction=fraction)
        for tag in ['supermarket', 'convenience', 'grocery']:
            row['mapped_'+tag+'_count_1500m'] = sum(p['category'] == 'competitor' and p['shop'] == tag for p in near)
        row['operational_metro_station_count_1500m'] = sum(s['operational_status'] == 'OPERATIONAL' and dist(site, s) <= 1500 for s in stations)
        row['ward_2011_id'] = wards[sid]['ward_2011_id'] or None
        row['ward_2025_id'] = wards[sid]['ward_2025_id'] or None
        for kind in ['weekday', 'weekend']:
            a = averages[site['nearest_metro_station_id'], kind]
            row['metro_sep2025_'+kind+'_observation_hours'] = a['observation_hours']
            row['metro_sep2025_'+kind+'_observed_days'] = a['observed_days']
        enriched.append(row)
    write('daypart_site_support.csv', support)
    write('daypart_opportunity_shares.csv', revised_profiles)
    write('site_features_enriched.csv', enriched, list(master[0])+EXTRA)
    return support

def assign_daypart(day, hour):
    if not 0 <= hour <= 23:
        raise ValueError('Hour must be 0..23')
    starting = day - dt.timedelta(days=1) if hour < 6 else day
    h = hour + 24 if hour < 6 else hour
    if starting.weekday() >= 5:
        return starting, 'weekend_day' if h < 18 else 'weekend_evening'
    return starting, 'weekday_morning' if h < 11 else 'weekday_lunch' if h < 15 else 'weekday_evening' if h < 20 else 'weekday_night'

def aggregate_metro(hourly, stations):
    """Only paired, nonnegative, actual 60-minute September intervals contribute.

    Calendar coverage includes the prior starting-day boundary and incomplete
    final overnight bins. Rates use COMPLETE bins with September starting dates.
    """
    grouped = defaultdict(list)
    seen = set()
    exclusions = Counter()
    eligible_intervals = []
    for r in hourly:
        key = (r['station_id'], r['service_date'], r['hour'])
        if key in seen:
            raise ValueError('Duplicate metro source interval: ' + str(key))
        seen.add(key)
        if not r['service_date'].startswith('2025-09-'):
            exclusions['outside_september_source_period'] += 1
            continue
        if r['interval_duration_minutes'] != '60' or not r['entries'] or not r['exits']:
            exclusions['missing_or_non_hourly_or_unpaired'] += 1
            continue
        start = dt.datetime.fromisoformat(r['interval_start_local'])
        end = dt.datetime.fromisoformat(r['interval_end_local'])
        hour = int(r['hour'])
        expected_start = dt.datetime.combine(dt.date.fromisoformat(r['service_date']), dt.time(hour), tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30)))
        if end-start != dt.timedelta(hours=1) or start.utcoffset() != dt.timedelta(hours=5, minutes=30) or end.utcoffset() != start.utcoffset() or start != expected_start:
            raise ValueError('Invalid interval duration/timezone')
        if r['station_id'] not in stations:
            raise ValueError('Unmatched metro station')
        if any(not re.fullmatch(r'\d+', r[k]) for k in ['entries', 'exits']):
            raise ValueError('Ridership must be a nonnegative integral observation')
        day, timebin = assign_daypart(dt.date.fromisoformat(r['service_date']), int(r['hour']))
        grouped[r['station_id'], day.isoformat(), timebin].append(r)
        eligible_intervals.append(r)
    daily = []
    first, last = dt.date(2025, 9, 1), dt.date(2025, 9, 30)
    for sid in sorted(stations):
        for offset in range(31):
            day = first - dt.timedelta(days=1) + dt.timedelta(days=offset)
            for b, (start, end, days) in BINS.items():
                if (day.weekday() >= 5) != (days == 2):
                    continue
                rr = grouped.get((sid, day.isoformat(), b), [])
                expected = end-start
                complete = len(rr) == expected
                within = first <= day <= last
                for direction in ['entries', 'exits']:
                    counts = [int(r[direction]) for r in rr]
                    daily.append(dict(station_id=sid, starting_local_date=day.isoformat(), time_bin=b, direction=direction,
                        observed_count=sum(counts) if counts else None, observed_hours=len(rr), expected_bin_hours=expected,
                        rate_per_observed_clock_hour=sum(counts)/len(rr) if rr else None,
                        is_complete_period=complete, incomplete_period_indicator=not complete, september_starting_date_eligible=within,
                        included_in_aggregate=complete and within, coverage_status='COMPLETE' if complete else 'PARTIAL' if rr else 'NO_OBSERVED_INTERVALS',
                        source_period_start='2025-09-01', source_period_end='2025-09-30', timezone=TZ,
                        source_id='metro-rti', traffic_measure='OBSERVED_TRANSIT_COUNTS_NOT_STORE_FOOTFALL'))
    rates = []
    for sid in sorted(stations):
        for b, (start, end, days) in BINS.items():
            for direction in ['entries', 'exits']:
                rr = [r for r in daily if r['station_id'] == sid and r['time_bin'] == b and r['direction'] == direction and r['september_starting_date_eligible']]
                used = [r for r in rr if r['included_in_aggregate']]
                numerator = sum(r['observed_count'] for r in used)
                denominator = sum(r['observed_hours'] for r in used)
                rates.append(dict(station_id=sid, time_bin=b, direction=direction, observed_count=numerator if used else None,
                    observed_hours=denominator, complete_starting_days=len(used), eligible_starting_days=len(rr),
                    incomplete_starting_days=sum(r['incomplete_period_indicator'] for r in rr), expected_bin_hours=end-start,
                    complete_bin_fraction=len(used)/len(rr) if rr else None,
                    rate_per_observed_clock_hour=numerator/denominator if denominator else None,
                    measurement_start_date='2025-09-01', measurement_end_date='2025-09-30',
                    paired_directions_only=True, aggregate_policy='COMPLETE_BINS_ONLY_SEPTEMBER_STARTING_DATES',
                    timezone=TZ, source_id='metro-rti', origin='DERIVED_FROM_SOURCE',
                    traffic_measure='HISTORICAL_OBSERVED_TRANSIT_NOT_STORE_FOOTFALL'))
    return daily, rates, eligible_intervals, dict(exclusions)

def metro_and_evidence(master, support):
    hourly = read(FROZEN / 'metro_hourly.csv')
    stations = {r['station_id'] for r in read(FROZEN / 'metro_station_lookup.csv')}
    daily, rates, valid, excluded = aggregate_metro(hourly, stations)
    write('metro_daypart_coverage.csv', daily)
    write('metro_daypart_rates.csv', rates)
    site_rates = [dict(site_id=s['site_id'], **r) for s in master for r in rates if r['station_id'] == s['nearest_metro_station_id']]
    write('site_metro_daypart_rates.csv', site_rates)
    ss = {r['site_id']: r for r in support}
    evidence = []
    for s in master:
        sid = s['nearest_metro_station_id']
        paired = sum(r['station_id'] == sid for r in valid)
        bins = [r for r in daily if r['station_id'] == sid and r['direction'] == 'entries' and r['september_starting_date_eligible']]
        sup = ss[s['site_id']]
        evidence.append(dict(site_id=s['site_id'], daypart_poi_support_count=sup['poi_support_count'],
            opening_hours_recorded_count=sup['opening_hours_recorded_count'], opening_hours_parsed_count=sup['recorded_hours_support_count'],
            opening_hours_assumed_count=sup['assumed_hours_support_count'], parsed_hours_support_fraction=sup['recorded_hours_support_fraction'],
            original_hours_recorded_fraction=sup['opening_hours_recorded_fraction'], nearest_metro_station_id=sid,
            metro_september_paired_intervals=paired, metro_september_expected_clock_intervals=720,
            metro_clock_interval_coverage_fraction=paired/720, metro_eligible_daypart_bins=len(bins),
            metro_complete_daypart_bins=sum(r['included_in_aggregate'] for r in bins),
            metro_complete_daypart_bin_fraction=sum(r['included_in_aggregate'] for r in bins)/len(bins),
            metro_incomplete_daypart_bins=sum(r['incomplete_period_indicator'] for r in bins),
            population_reference_year=2020, nominal_population_resolution='1km', population_origin='MODELLED_HISTORICAL_PROXY',
            household_denominator_available=False, validated_routing_available=False, financial_inputs_origin='SYNTHETIC_DEMO',
            osm_universe_completeness='UNKNOWN', evidence_interpretation='SUPPORT_COUNTS_AND_COVERAGE_NOT_CONFIDENCE',
            source_id='osm-pois;metro-rti;worldpop-2020;assumptions'))
    write('site_evidence_coverage.csv', evidence)
    save_json('metro_aggregation_metadata.json', dict(revision=REVISION, source_path='../final/metro_hourly.csv', source_sha256=sha(FROZEN/'metro_hourly.csv'),
        source_observation_period='2025-09-01/2025-09-30', timezone=TZ, valid_paired_clock_intervals=len(valid), excluded_intervals=excluded,
        incomplete_final_bin='2025-09-30 weekday_night: only 20:00-24:00 observed; October intervals unavailable; excluded from rate',
        previous_boundary='September 1 00:00-06:00 belongs to August 31 weekend_evening; shown as coverage, excluded from September starting-day aggregates',
        no_unreported_count_imputation=True, no_poi_opportunity_merged_with_transit=True))

def master_schema(master):
    """Use reviewed semantic dictionary, not inference from all-null columns."""
    text = (BASE/'reports/data_sources_for_presentation.md').read_text(encoding='utf-8')
    specs = {}
    for line in text.splitlines():
        if not re.match(r'^\| \d+ \| `', line):
            continue
        cells = [v.strip() for v in line.split('|')[1:-1]]
        name = cells[1].strip('`')
        dtype = 'String' if cells[4] in ['string', 'category/string'] else 'ISODate' if cells[4] == 'date' else 'Int64' if cells[4] == 'int64' else 'Float64'
        origin = cells[5]
        category = 'METADATA_CONFIG' if origin == 'M' else 'SYNTHETIC_DEMO' if origin in ['S', 'S/A'] else 'ASSUMED' if origin == 'A' else 'ASSUMED_METADATA' if origin.startswith('A/M') else 'DERIVED_WITH_ASSUMPTIONS' if origin == 'D+A' else 'DERIVED_FROM_MODELLED_SOURCE_WITH_ASSUMPTIONS' if origin == 'D/modelled' else 'UNRESOLVED_MISSING' if origin == 'U' else 'DERIVED_FROM_SOURCE'
        specs[name] = dict(unit=cells[3], logical_type=dtype, origin=category,
            nullable='nullable' in cells[4] or name in ['population_10min_est','accessible_households_est'], meaning=cells[2])
    assert list(specs) == list(master[0])
    specs['wallet_price_year']['origin'] = 'METADATA_CONFIG'
    for name in EXTRA:
        specs[name] = dict(unit='fraction' if 'share' in name or 'fraction' in name else 'station count' if name.startswith('operational') else 'hours' if name.endswith('_hours') else 'days' if name.endswith('_days') else 'identifier' if name.startswith('ward_') else 'mapped POI count',
            logical_type='String' if name.startswith('ward_') else 'Float64' if 'share' in name or 'fraction' in name else 'Int64',
            origin='DERIVED_WITH_ASSUMPTIONS' if name.endswith('_weekly_exposure_share') else 'DERIVED_FROM_SOURCE',
            nullable=name.startswith('ward_') or name == 'daypart_recorded_hours_fraction', meaning='Audited v2 enrichment; see column lineage for exact aggregation and join')
    return specs

def infer_spec(table, field, rows):
    """Logical CSV types and semantic units, with metadata taking precedence."""
    values = [str(r.get(field, '')) for r in rows if r.get(field) is not None and r.get(field) != '']
    nullable = len(values) < len(rows)
    semantic = {
        'population_est': ('estimated persons', 'Float64'), 'households_est': ('estimated households', 'Float64'),
        'monthly_grocery_per_capita_inr': ('INR/person/30 days', 'Float64'),
        'monthly_per_capita_inr': ('INR/person/30 days', 'Float64'),
        'annual_wallet_inr': ('INR/year, nominal 2023-24 prices', 'Float64'),
        'raw_opportunity_index': ('relative opportunity per nominal hour', 'Float64'),
        'weekly_opportunity_exposure': ('relative opportunity-hours per representative week', 'Float64'),
        'theta': ('dimensionless relative attraction', 'Float64'),
        'variable_contribution_margin': ('fraction 0-1', 'Float64'),
        'entries': ('reported transit passengers', 'Int64'), 'exits': ('reported transit passengers', 'Int64'),
        'interval_duration_minutes': ('minutes', 'Int64'), 'hour': ('local clock hour 0-23', 'Int64'),
        'local_start_hour': ('local clock hour 0-23', 'Int64'), 'local_end_hour': ('local clock hour 0-23', 'Int64'),
        'delay_months': ('calendar months', 'Int64'), 'bytes': ('bytes', 'Int64'),
        'source_station_code': ('source identifier', 'String'), 'osm_station_code': ('source identifier', 'String'),
        'Ward Num': ('ward identifier', 'String'), 'Assembly constituency': ('constituency label', 'String'),
        'area_sqm': ('square metres', 'Float64'), 'overlap_in_aoi_sqm': ('square metres', 'Float64'),
        'observed_service_period_complete': ('boolean; not applicable to representative POI week', 'Boolean'),
    }
    if field in semantic:
        unit, dtype = semantic[field]
        return dict(unit=unit, logical_type=dtype, nullable=nullable)
    if table == 'census_2011_wards' and field in ['Population','Male','Female','SC Population','SC male','SC Female','ST Population','ST Male','ST Female']:
        return dict(unit='persons in 2011 census ward', logical_type='Int64', nullable=nullable)
    if 'per_observed' in field or field.endswith('_per_hour'):
        return dict(unit='reported transit passengers/observed clock hour', logical_type='Float64', nullable=nullable)
    if field == 'starting_days_per_week':
        return dict(unit='starting days per representative week', logical_type='Int64', nullable=nullable)
    if field.endswith('_vintage') and values and all(v.isdigit() for v in values):
        return dict(unit='reference year, not observation date', logical_type='Int64', nullable=nullable)
    if field.endswith('_id') or field.endswith('_ids') or 'status' in field or field in ['unit','logical_type','origin','source_url','name','locality','notes','reason','generated_value','base','value']:
        return dict(unit='identifier' if field.endswith(('_id','_ids')) else 'metadata/text', logical_type='String', nullable=nullable)
    if field.endswith('_date'):
        return dict(unit='ISO calendar date', logical_type='ISODate', nullable=nullable)
    if field.endswith('_at_utc') or field.endswith('_local'):
        return dict(unit='ISO timestamp with offset', logical_type='ISOTimestamp', nullable=nullable)
    if values and all(v in ['True','False'] for v in values):
        return dict(unit='boolean', logical_type='Boolean', nullable=nullable)
    if field in ['low','high']:
        return dict(unit='same as record.unit', logical_type='Float64', nullable=nullable)
    numeric = bool(values) and all(re.fullmatch(r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?', v, re.I) for v in values)
    if numeric:
        dtype = 'Int64' if all(float(v).is_integer() for v in values) and not any(x in field for x in ['fraction','share','rate','average','latitude','longitude','weight','index','distance']) else 'Float64'
        unit = 'fraction' if 'fraction' in field or 'share' in field or 'margin' in field else 'decimal degrees EPSG:4326' if field in ['latitude','longitude'] else 'sqm' if field.endswith('_sqm') else 'metres' if field.endswith('_m') else 'year' if field.endswith('_year') else 'INR/person/30 days' if field == 'monthly_per_capita_inr' else 'INR/month' if field == 'monthly_rent_inr' else 'INR upfront' if field == 'capex_inr' else 'INR/year' if field.endswith('_inr') else 'hours' if 'hours' in field else 'days' if 'days' in field else 'passengers/observed clock hour' if 'per_observed_clock_hour' in field else 'reported transit passengers' if field == 'observed_count' else 'count' if 'count' in field or 'interval' in field or 'records' in field else 'relative weight' if 'weight' in field else 'unitless numeric'
        return dict(unit=unit, logical_type=dtype, nullable=nullable)
    return dict(unit='metadata/text', logical_type='String', nullable=nullable)

def lineage_and_schema(master):
    specs = master_schema(master)
    schema_rows = [dict(column_order=i, field_name=name, **spec, provenance_revision_id=REVISION) for i,(name,spec) in enumerate(specs.items(),1)]
    write('site_feature_schema.csv', schema_rows)
    old = read(FROZEN/'field_lineage.csv')
    base_by = {(r['record_id'],r['field_name']):r for r in old if r['table']=='site_features'}
    lines = []
    def append(table, rid, field, spec, source, aid, method, locator, value=None, legacy=None, period=None):
        category = spec.get('origin','DERIVED_FROM_SOURCE')
        if rid != '*' and (value is None or value == ''):
            category = 'UNRESOLVED_MISSING'
        lines.append(dict(table=table, record_id=rid, field_name=field, origin=category, unit=spec['unit'], logical_type=spec['logical_type'],
            nullable=spec['nullable'], source_ids=source, assumption_ids=aid or None, formula_or_method=method, source_locator=locator,
            observation_reference_period=period, valuation_date=ASOF,
            price_basis='2023-24 nominal survey prices; no adjustment' if field in ['annual_wallet_inr','wallet_price_year','monthly_per_capita_inr','monthly_grocery_per_capita_inr'] else '2026-10-24 nominal demo INR' if field in ['monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr'] else None,
            currency='INR' if 'INR' in spec['unit'] else None, provenance_revision_id=REVISION,
            legacy_origin=legacy['origin'] if legacy else None, legacy_unit=legacy['unit'] if legacy else None,
            limitations='No sales labels; historical inputs and source-plus-assumption estimates are explicitly distinct.'))
    for table, rows in [('site_features',master),('site_features_enriched',TABLES['site_features_enriched'])]:
        for row in rows:
            sid = row['site_id']
            for field, value in row.items():
                spec = specs[field]
                legacy = base_by.get((sid,field))
                if legacy:
                    source = legacy['source_ids'];aid = legacy['assumption_ids'];method = legacy['formula_or_method']
                    period = legacy['observation_reference_period'];locator = '../final/site_features.csv#site_id='+sid+'; frozen source derivation documented in baseline lineage'
                    if spec['origin']=='METADATA_CONFIG':
                        method='User-fixed configuration or provenance/status label, not an empirical observation; '+spec['meaning']
                    if field == 'source_quality_score':
                        source='assumptions';aid='legacy-evidence-family-indicator';method='Literal legacy 6/8 retained unchanged; never confidence/reliability; use site_evidence_coverage.csv for actual support.'
                    if field in ['population_1500m_est','mean_wallet_weighted_distance_m','annual_wallet_inr']:
                        aid=';'.join(x for x in [aid,'uniform-within-pixel-population'] if x)
                    if field.startswith('population') and field!='population_data_status' and value:
                        period='WorldPop reference year 2020; nominal 1km raster'
                else:
                    period='OSM extraction 2026-10-24'
                    if field.endswith('_weekly_exposure_share'):
                        source='osm-pois;approved-weights;assumptions';aid='approved-category-weights;unknown-hours-availability;unknown-hours-evidence;recorded-hours-evidence'
                        method='Pivot exact bin share: raw * duration_hours * starting_days_per_week / sum of weekly exposure across six bins; opportunity proxy, not footfall.'
                        locator='daypart_opportunity_shares.csv#site_id='+sid
                    elif field.startswith('daypart_'):
                        source='osm-pois';aid=None;method='One common support count across six bins, never sum duplicated support; parsed fraction=recorded_hours_support_count/poi_support_count.';locator='daypart_site_support.csv#site_id='+sid
                    elif field.startswith('mapped_'):
                        source='osm-pois';aid=None;method='Count deduplicated external competitor POIs by original shop tag within geodesic 1500m; mapped zero is not verified absence.';locator='../final/pois.csv; candidate '+sid
                    elif field.startswith('operational_'):
                        source='osm-pois;metro-rti;yellow-official';aid=None;method='Count matched operational station points within geodesic 1500m; excludes individual entrances/platforms.';locator='../final/metro_station_lookup.csv; candidate '+sid
                    elif field.startswith('ward_'):
                        source='wards-2012;wards-2025';aid=None;method='Validated one-to-one left join by site_id to existing point-in-polygon vintage lookup; unmatched ID stays null.';locator='../final/site_ward_lookup.csv#site_id='+sid;period='2012 historical geometry / 2025-12 new boundary vintage; Census context 2011'
                    else:
                        source='metro-rti';aid=None;method='Pivot actual day-type observation-hours/days and many-to-one join by nearest_metro_station_id; support metadata, not predictions.';locator='../final/metro_activity_averages.csv#station_id='+row['nearest_metro_station_id'];period='2025-09-01/2025-09-30'
                append(table,sid,field,spec,source,aid,method,locator,value,legacy,period)
    # Correct semantics for every supporting field from v1, and describe new
    # supporting outputs without expanding millions of metadata cell repeats.
    old_support = {(r['table'],r['field_name']):r for r in old if r['record_id']=='*'}
    assumption_fields = defaultdict(set)
    for r in TABLES['synthetic_assumptions']:
        assumption_fields[r['table'],r['field_name']].add(r['assumption_id'])
    tables = {p.stem:read(p) for p in FROZEN.glob('*.csv') if p.stem not in ['field_lineage','site_features']}
    tables.update(TABLES)
    for name, rows in sorted(tables.items()):
        if name in ['site_features_enriched','field_lineage'] or not rows:
            continue
        for field in rows[0]:
            spec = infer_spec(name,field,rows)
            legacy=old_support.get((name,field))
            source=';'.join(sorted({s for r in rows for key in ['source_id','source_ids'] for s in str(r.get(key) or '').split(';') if s}))
            source = source or (legacy['source_ids'] if legacy else 'package-config')
            spec['origin']='METADATA_CONFIG'
            if name in ['expenditure_inputs','census_2011_wards'] and spec['logical_type'] in ['Int64','Float64'] and field not in ['reference_year','price_year','population_reference_year','item_id']:
                spec['origin']='OBSERVED_SOURCE'
            elif name=='metro_hourly' and field in ['entries','exits']:
                spec['origin']='OBSERVED_SOURCE'
            elif name=='pois' and field in ['name','opening_hours','shop','amenity','tags_json','osm_id','osm_type','latitude','longitude']:
                spec['origin']='OBSERVED_SOURCE'
            elif name in ['candidate_sites','existing_stores'] and field in ['latitude','longitude','store_size_sqm','theta','variable_contribution_margin','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr','gross_margin_fraction','locality']:
                spec['origin']='SYNTHETIC_DEMO'
            elif name in ['daypart_weights','synthetic_assumptions','assumption_registry'] and field in ['category_weight','generated_value','base','low','high']:
                spec['origin']='ASSUMED'
            elif name in ['daypart_profiles','daypart_opportunity_shares','poi_daypart_availability','spending_cells'] and spec['logical_type'] in ['Int64','Float64']:
                spec['origin']='DERIVED_WITH_ASSUMPTIONS' if field not in ['population_reference_year','wallet_price_year'] else 'METADATA_CONFIG'
            elif spec['logical_type'] in ['Int64','Float64']:
                spec['origin']='DERIVED_FROM_SOURCE'
            if name == 'spending_cells' and field == 'households_est':
                spec['origin']='UNRESOLVED_MISSING'
            if name == 'source_manifest' or field in ['reference_year','price_year','population_reference_year','wallet_price_year','old_geometry_vintage','new_geometry_vintage','column_order'] or name == 'site_feature_schema':
                spec['origin']='METADATA_CONFIG'
            if name == 'infrastructure' and field in ['hypothetical_open_date','delayed_open_date','assumed_demand_effect_fraction']:
                spec['origin']='ASSUMED'
            aid=';'.join(sorted(assumption_fields.get((name,field),set()))) or None
            if name == 'spending_cells' and field in ['population_est','annual_wallet_inr']:
                aid=';'.join(x for x in [aid,'uniform-within-pixel-population'] if x)
            locator = name+'.csv' if name in TABLES else '../final/'+name+'.csv'
            method = 'Per-record original source/assumption IDs and locators; '+(legacy['formula_or_method'] if legacy else 'build_revised.py supporting transformation; no unsupported imputation')
            append(name,'*',field,spec,source,aid,method,locator,legacy=legacy)
    write('field_lineage.csv',lines)
    return specs

def metadata(release):
    baseline=load(V2/'baseline_hashes.json')
    save_json('dataset_metadata.json',dict(provenance_revision_id=REVISION, optional_enriched_view=True,
        master_embedded_feature_snapshot_id=load(BASE/'processed/build_config.json')['feature_snapshot_id'],
        master_embedded_source_manifest_id='bengaluru-sources-20261024-v1', corrected_provenance_manifest_id=MANIFEST_V2,
        revision_resolution='The first 50 fields and embedded v1 identities are immutable; this metadata maps them to optional v2 provenance/enrichment.',
        master_columns=list(read(FROZEN/'site_features.csv')[0]), enrichment_columns=EXTRA, total_enriched_columns=70,
        valuation_date=ASOF, timezone=TZ, coordinate_crs='EPSG:4326', distance_method='WGS84 ellipsoidal point distances', metric_crs='EPSG:32643',
        population_reference_year=2020, population_nominal_resolution='1km aggregated', population_resolution_degrees=0.0083333333,
        population_product_release_date=None, population_origin='MODELLED_HISTORICAL_PROXY',
        hces_reference_start_date='2023-08-01', hces_reference_end_date='2024-07-31', hces_detailed_report_release_date=release,
        hces_release_verification='OFFICIAL_PRESS_NOTE_AND_PIB' if release else 'UNVERIFIED_UNKNOWN',
        hces_fact_sheet_release_date='2024-12-27' if release else None, wallet_price_year=2024, wallet_price_basis='2023-24 nominal survey prices',
        financial_price_basis_date=ASOF, financial_inputs_origin='SYNTHETIC_DEMO', currency='INR', monthly_rent_period='MONTHLY',
        opex_period='ANNUAL_EXCLUDING_RENT_AND_COGS', capex_period='UPFRONT', financial_price_basis_mismatch=True, inflation_conversion_applied=False,
        metro_master_observation_period='2025-09-01/2025-09-30', metro_daypart_policy='COMPLETE_PAIRED_BINS_SEPTEMBER_STARTING_DATES_ONLY',
        source_quality_indicator_role='UNCHANGED_LEGACY_LITERAL_0.75_NOT_CONFIDENCE_OR_RELIABILITY',
        actual_coverage_table='site_evidence_coverage.csv', original_baseline_file_count=len(baseline['files']),
        public_distribution_status='NOT_CLEARED_FOR_PUBLIC_REDISTRIBUTION', original_git_head=baseline['head']))
    sensitive=['site_features_enriched.csv','metro_daypart_coverage.csv','metro_daypart_rates.csv','site_metro_daypart_rates.csv','site_evidence_coverage.csv']
    save_json('distribution_manifest.json',dict(public_package_created=False, raw_metro_workbooks_copied=False,
        unresolved_licensing='BMRCL contents copyright, GitHub ODbL and OpenCity cc-nc metadata conflict remain unresolved; neither downloads nor derivation resolve rights.',
        not_cleared_for_public_distribution=sensitive, inherited_metro_rights_apply_to_derived_records=True,
        legacy_zip_repo_relative_path='StoreScout_Bengaluru_Dataset.zip', legacy_zip_status='Existing workspace-root archive preserved unchanged; not cleared for publication',
        original_urls_checksums_and_timestamps='source_acquisitions.csv and baseline_hashes.json; references only, not copied workbooks'))

def main():
    preserved_baseline()
    master=read(FROZEN/'site_features.csv')
    release=correct_sources()
    correct_expenditure()
    correct_infrastructure()
    assumptions(master)
    support=daypart_and_enrichment(master)
    metro_and_evidence(master,support)
    lineage_and_schema(master)
    metadata(release)
    preserved_baseline()
    print(json.dumps({name:dict(rows=len(rows),columns=len(rows[0]),nulls=sum(v is None or v=='' for r in rows for v in r.values())) for name,rows in TABLES.items()},indent=2))

if __name__=='__main__':
    main()
