"""Independent integrity checks and completion report for the local dataset."""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from pyproj import Geod,Transformer
from shapely.geometry import Point,box,shape
from shapely.ops import unary_union,transform
import rasterio

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/bengaluru'
FINAL=DATA/'final'
REPORTS=DATA/'reports'
PROCESSED=DATA/'processed'
CONFIG=json.loads((PROCESSED/'build_config.json').read_text(encoding='utf-8'))
METRICS=json.loads((PROCESSED/'build_metrics.json').read_text(encoding='utf-8'))
CHECKS=[]

def read(name,folder=FINAL):
    with (folder/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def jsave(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def check(name,ok,details):
    CHECKS.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',details=details))
def f(v):return float(v)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def date(v):return dt.date.fromisoformat(v)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate():
    master=read('site_features.csv');sites=read('candidate_sites.csv');stores=read('existing_stores.csv')
    cells=read('spending_cells.csv');pois=read('pois.csv');hourly=read('metro_hourly.csv');lookup=read('metro_station_lookup.csv')
    profiles=read('daypart_profiles.csv');lineage=read('field_lineage.csv');assumptions=read('synthetic_assumptions.csv')
    manifest=read('source_manifest.csv');sources={r['source_id'] for r in manifest}
    fields=list(master[0]);check('exact_master_schema',fields==CONFIG['master_columns'] and len(master)==10 and len(fields)==50,{'rows':len(master),'columns':len(fields),'order_matches':fields==CONFIG['master_columns']})
    for name,rows,key in [('candidate',sites,'site_id'),('existing',stores,'store_id'),('cells',cells,'cell_id'),('pois',pois,'poi_id'),('station_lookup',lookup,'station_id')]:
        check(name+'_unique_keys',len({r[key] for r in rows})==len(rows),{'rows':len(rows)})
    check('requested_record_counts',len(sites)==10 and len(stores)==4 and len(cells)==100,{'sites':len(sites),'branches':len(stores),'cells':len(cells)})
    aoi=box(*CONFIG['bbox_west_south_east_north'])
    invalid=[]
    for table,rows in [('sites',sites),('stores',stores),('pois',pois),('cells',cells),('stations',lookup)]:
        for r in rows:
            if not aoi.covers(Point(f(r['longitude']),f(r['latitude']))):invalid.append([table,r])
    check('india_corridor_geography',not invalid,{'invalid_point_locations':len(invalid),'bbox':CONFIG['bbox_west_south_east_north']})
    financials=['store_size_sqm','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr']
    check('financial_nonnegative_and_units',all(f(r[x])>=0 for r in sites for x in financials) and all(0<=f(r['gross_margin_fraction'])<=1 for r in sites),
        'Rent monthly INR, CAPEX upfront INR, OPEX annual INR excluding rent/COGS, margin fraction; 2026-10-24 demo price basis.')
    check('missing_features_remain_null',all(not r['population_10min_est'] and not r['accessible_households_est'] for r in master),{'master_nulls':sum(not v for r in master for v in r.values())})
    check('finite_master_numeric_values',all(math.isfinite(f(r[k])) for r in master for k in fields if r[k] and (k in financials or k.endswith('_raw') or k.endswith('_per_hour') or k.endswith('_count_1500m') or k in ['population_1500m_est','annual_wallet_inr','gross_margin_fraction','source_quality_score','latitude','longitude'])), 'No NaN or Infinity in numeric features.')
    check('unique_metro_keys',len({(r['station_id'],r['service_date'],r['hour']) for r in hourly})==len(hourly),{'rows':len(hourly),'duplicates':0 if len({(r['station_id'],r['service_date'],r['hour']) for r in hourly})==len(hourly) else 'present'})
    check('metro_no_negative_or_fabricated_counts',all(not r[d] or f(r[d])>=0 for r in hourly for d in ['entries','exits']) and all(not r['exits'] for r in hourly if r['service_date'].startswith('2025-08')), 'August exits left null; observed workbook night zeros retained.')
    interval_errors=[]
    for r in hourly:
        start=dt.datetime.fromisoformat(r['interval_start_local'])
        if start.utcoffset()!=dt.timedelta(hours=5,minutes=30) or r['timezone']!='Asia/Kolkata':interval_errors.append('timezone')
        if r['interval_duration_minutes']:
            end=dt.datetime.fromisoformat(r['interval_end_local'])
            if (end-start).total_seconds()!=3600:interval_errors.append('duration')
        elif r['interval_end_local'] or not (r['service_date'].startswith('2025-08') and r['hour']=='23'):interval_errors.append('variable')
    check('timezone_and_interval_integrity',not interval_errors,{'invalid_intervals':len(interval_errors),'variable_last_train_intervals':sum(not r['interval_duration_minutes'] for r in hourly)})
    ids={r['station_id'] for r in lookup}
    check('station_mapping_consistency',all(r['station_id'] in ids for r in hourly) and all(r['nearest_metro_station_id'] in ids for r in master) and all(r['mapping_status']=='EXACT_NAME_MATCH' for r in lookup), {'matched_corridor_stations':len(ids),'unresolved_corridor_mappings':0})
    # Execute boundary examples against the build's actual bin function.
    from build import assign_daypart,opening_schedule
    examples=[('2025-09-06',2,'2025-09-05','weekday_night'),('2025-09-08',2,'2025-09-07','weekend_evening'),
      ('2025-09-05',20,'2025-09-05','weekday_night'),('2025-09-06',6,'2025-09-06','weekend_day'),
      ('2025-09-06',18,'2025-09-06','weekend_evening'),('2025-09-05',11,'2025-09-05','weekday_lunch'),('2025-09-05',15,'2025-09-05','weekday_evening')]
    check('overnight_daypart_assignment',all((lambda got:(got[0].isoformat(),got[1])==(expected,b))(assign_daypart(date(d),h)) for d,h,expected,b in examples),{'boundary_examples':len(examples)})
    parsed=opening_schedule('Fr 20:00-02:00')
    check('recorded_hours_overnight_schedule',parsed is not None and parsed[4*1440+23*60] and parsed[5*1440+60] and not parsed[5*1440+3*60] and opening_schedule('Mo-Fr sunrise-sunset') is None,'Friday 20:00-02:00 stays open Saturday 01:00; unsupported syntax not silently interpreted.')
    expected={'weekday_morning','weekday_lunch','weekday_evening','weekday_night','weekend_day','weekend_evening'}
    groups=defaultdict(list)
    for r in profiles:groups[r['site_id']].append(r)
    check('six_daypart_bins_and_duration_normalization',len(profiles)==60 and all({r['time_bin'] for r in rr}==expected and abs(sum(f(r['weekly_exposure_share']) for r in rr)-1)<1e-9 and sum(f(r['duration_hours'])*f(r['starting_days_per_week']) for r in rr)==168 for rr in groups.values()),'Raw indices are per nominal hour; weekly shares weight bin hours and starting days, totalling 168 hours.')
    geod=Geod(ellps='WGS84')
    badcounts=[]
    mapping_={'office_poi_count_1500m':['office'],'education_poi_count_1500m':['school'],'healthcare_poi_count_1500m':['hospital'],'transit_poi_count_1500m':['transit'],'shopping_poi_count_1500m':['shopping'],'food_leisure_poi_count_1500m':['leisure'],'competitor_count_1500m':['competitor']}
    for r in master:
        counts=Counter(p['category'] for p in pois if geod.inv(f(r['longitude']),f(r['latitude']),f(p['longitude']),f(p['latitude']))[2]<=1500)
        for field,cats in mapping_.items():
            if int(r[field])!=sum(counts[c] for c in cats):badcounts.append([r['site_id'],field])
    check('poi_counts_recomputed_geodesically',not badcounts,{'site_category_checks':70,'mismatches':badcounts})
    # Verify the exact opportunity formula for all six bins at one site,
    # independently reading weights and availability from exported tables.
    weights={(r['category'],r['time_bin']):f(r['category_weight']) for r in read('daypart_weights.csv')}
    availability={(r['poi_id'],r['time_bin']):(f(r['availability_fraction']),f(r['evidence_weight'])) for r in read('poi_daypart_availability.csv')}
    first=master[0];recalc={b:0.0 for b in expected}
    for p in pois:
        d=geod.inv(f(first['longitude']),f(first['latitude']),f(p['longitude']),f(p['latitude']))[2]
        if d>1500:continue
        for b in expected:
            if (p['category'],b) in weights:
                av,ev=availability[p['poi_id'],b]
                recalc[b]+=weights[p['category'],b]*math.exp(-d/750)*av*ev
    check('daypart_formula_recomputed',all(abs(recalc[b]-f(first[b+'_raw']))<1e-9 for b in expected),recalc)
    cellsgeo=json.loads((FINAL/'spending_cells.geojson').read_text(encoding='utf-8'))['features']
    polygons=[shape(r['geometry']) for r in cellsgeo]
    union=unary_union(polygons)
    check('cells_partition_boundary_without_overlap',abs(sum(p.area for p in polygons)-union.area)<1e-12 and union.symmetric_difference(aoi).area<1e-12,{'cells':len(polygons),'overlap_area_degrees2':sum(p.area for p in polygons)-union.area,'boundary_difference_degrees2':union.symmetric_difference(aoi).area})
    total=sum(f(r['population_est']) for r in cells)
    check('population_conservation',abs(total-METRICS['population_total'])<0.0001,{'source_clipped_population':METRICS['population_total'],'cell_population':total,'difference_persons':total-METRICS['population_total']})
    grocery=METRICS['grocery_monthly_per_capita_inr']
    check('one_wallet_per_cell_and_consistent_annualization',all(abs(f(r['annual_wallet_inr'])-f(r['population_est'])*grocery*12)<0.04 for r in cells) and len({r['network_baseline_id'] for r in cells})==1,{'unique_cell_wallets':100,'annual_wallet_total_inr':sum(f(r['annual_wallet_inr']) for r in cells),'note':'Overlapping site catchment totals are descriptive views and must never be concatenated into the network wallet.'})
    with rasterio.open(PROCESSED/'worldpop_2020_corridor_window.tif') as raster:
        arr=raster.read(1)
        check('population_raster_overlap',str(raster.crs)=='EPSG:4326' and np.isfinite(arr).all() and (arr>=0).all(),{'window_shape':list(arr.shape),'resolution_degrees':list(raster.res),'population_reference_year':2020,'nodata_pixels':int((arr==raster.nodata).sum())})
    unknown_sources=[]
    for path in FINAL.glob('*.csv'):
        if path.name=='source_manifest.csv':continue
        for r in read(path.name):
            for field in ['source_id','source_ids']:
                if field in r and r[field]:
                    for sid in r[field].split(';'):
                        if sid not in sources:unknown_sources.append([path.name,sid])
    check('source_references_resolve',not unknown_sources,{'missing_source_references':unknown_sources[:20]})
    lmaster=[r for r in lineage if r['table']=='site_features']
    check('master_field_lineage_complete',len(lmaster)==500 and len({(r['record_id'],r['field_name']) for r in lmaster})==500 and all(r['source_ids'] for r in lmaster),{'record_field_pairs':len(lmaster)})
    required_assumed=['latitude','longitude','store_size_sqm','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr','gross_margin_fraction']
    recorded={(r['table'],r['record_id'],r['field_name']) for r in assumptions}
    check('generated_business_values_labelled',all(('candidate_sites',r['site_id'],key) in recorded for r in sites for key in required_assumed) and all(r['source_status']=='SYNTHETIC_DEMO' for r in sites+stores),{'assumption_rows':len(assumptions),'candidate_record_field_checks':70})
    check('source_licence_and_attribution',all(r['licence'] and r['source_url'] for r in manifest),{'source_count':len(manifest),'unresolved_rights':'Metro ODbL versus OpenCity non-commercial metadata retained; no commercial rights resolution claimed.'})
    acq=read('acquisition_files.csv')
    mismatches=[]
    checked_sources=0
    for r in acq:
        if r['status']!='DOWNLOADED':continue
        if r['path'].endswith('commercial_rent_attempt.html'):continue # intentionally not redistributed
        checked_sources+=1
        path=ROOT/r['path']
        if not path.exists() or sha(path)!=r['sha256']:mismatches.append(r['path'])
    check('downloaded_source_checksums',not mismatches,{'downloaded_files_checked':checked_sources,'hash_mismatches':mismatches,'intentional_exclusion':'Proprietary commercial HTML, unused as a statistical input'})
    for r in assumptions:
        if r['low'] and r['high']:
            try:
                if not f(r['low'])<=f(r['generated_value'])<=f(r['high']):mismatches.append([r['table'],r['record_id'],r['field_name']])
            except ValueError:pass
    check('bounded_generated_values',not mismatches,{'generated_values_checked':len(assumptions),'out_of_range':mismatches})
    check('no_fake_training_targets_or_model_outputs',not any(re.search(r'(^target$|predicted|ranking|npv|roi|revenue|sales)',c) for c in fields) and not any(r.get('actual_annual_sales_inr') for r in stores),{'master_columns_checked':50,'supervised_training_readiness':'NOT_READY_NO_LABELS_BY_DESIGN'})
    for field in ['snapshot_as_of_date','metro_measurement_start_date','metro_measurement_end_date']:
        check('valid_dates_'+field,all(date(r[field])<=date(CONFIG['reference_date']) for r in master),{'reference_date':CONFIG['reference_date']})
    infra=read('infrastructure.csv');scenarios=read('infrastructure_scenarios.csv')
    check('no_future_infrastructure_baseline_leakage',next(r for r in infra if r['infra_project_id']=='metro-yellow')['included_current_baseline']=='True' and next(r for r in infra if r['infra_project_id']=='metro-blue-2a')['included_current_baseline']=='False' and all(r['future_geometry_in_baseline_features']=='False' for r in scenarios), 'Yellow operational baseline; Blue geometry and assumed effects remain separate future scenario inputs.')
    check('delayed_opening_24_months',date(next(r for r in infra if r['infra_project_id']=='metro-blue-2a')['delayed_open_date'])==dt.date(2029,7,1) and date(next(r for r in infra if r['infra_project_id']=='metro-blue-2a')['hypothetical_open_date'])==dt.date(2027,7,1),'Both dates are explicitly assumed; verified commercial opening date remains null.')
    invalid_geo=[]
    for path in FINAL.glob('*.geojson'):
        features=json.loads(path.read_text(encoding='utf-8'))['features']
        invalid_geo += [(path.name,i) for i,feature in enumerate(features) if not shape(feature['geometry']).is_valid]
    check('geojson_geometry_validity',not invalid_geo,{'invalid_geometries':invalid_geo[:10],'source_geometry_repairs':METRICS['ward_geometry_repairs']})
    check('canonical_fixtures_preserved',all(sha(ROOT/'data/demo'/name)==v['sha256'] for name,v in CONFIG['inspected_fixtures'].items()),CONFIG['inspected_fixtures'])
    tracked=git('diff','--name-only')
    head=git('rev-parse','HEAD');branch=git('branch','--show-current')
    check('git_history_branch_and_existing_code_unchanged',head==CONFIG['baseline_git_head'] and branch=='ML' and not tracked,{'branch':branch,'head':head,'tracked_changes':tracked,'commit_created':False,'push_performed':False,'branch_switched':False})
    # Actual schema compatibility, with extras explicitly selected away.
    import sys
    sys.path.insert(0,str(ROOT))
    from backend.app.schemas import Project
    fields_site=['site_id','name','latitude','longitude','store_size_sqm','capex_inr','monthly_rent_inr','gross_margin_fraction']
    fields_store=['store_id','name','latitude','longitude','store_size_sqm','theta','variable_contribution_margin']
    project=dict(project_id='bengaluru-data-readiness-only',city='Bengaluru',category='grocery',budget_inr=20000000,
      discount_rate_fraction=0.12,projection_years=5,source_status='SYNTHETIC',
      sites=[dict({k:r[k] for k in fields_site},annual_opex_inr=r['annual_opex_excl_rent_inr']) for r in sites],
      stores=[{k:r[k] for k in fields_store} for r in stores])
    try:
        Project.model_validate(project)
        check('canonical_project_schema_mapping',True,'All 10 candidates and 4 branches validate against unchanged backend Project/Site/Store models. No evaluation engine invoked.')
    except Exception as exc:check('canonical_project_schema_mapping',False,str(exc))
    return master,manifest

import re

LIMITATIONS=[
 'No measured sales labels or trained model exist. The 50-column file is a feature snapshot, not a supervised training dataset. Inference awaits a separately trained compatible model.',
 'Population is a modelled 2020 WorldPop 1km estimate, carried as a historical proxy. Within-pixel density is assumed uniform; it is not a 2026 measurement or a 100m product.',
 'Annual category wallets combine 2020 population with Karnataka urban HCES 2023-24 expenditure, 50% grocery eligibility for the processed-food/cooked-meal category, and a state-to-local transfer assumption. They are addressable category expenditure, not store sales.',
 'Wallet price year is 2024 (2023-24 nominal survey prices); fictional rent, CAPEX and non-rent OPEX use a 2026-10-24 price basis. No inflation adjustment or matched-price economic forecast is claimed.',
 'Ten-minute population and accessible households are null for all ten sites. No validated travel-time graph or local household denominator was obtained.',
 'OSM is incomplete crowdsourced coverage. Counts of zero mean zero mapped records, not verified absence. Node/way centres, facility subdivisions and unrecorded shops can affect counts. Same-name/category duplicates within 40m are collapsed and logged.',
 'Daypart weights and missing-hours availability/evidence weights are assumptions. Only a conservative opening-hours syntax subset is interpreted. Profiles are POI opportunity proxies, not measured store footfall. Metro traffic is kept separate.',
 'Metro records cover August 1-18 and September 1-30, 2025 at network level. Corridor Yellow Line stations have later August coverage after launch. August exits are null because no exit-clock workbook was acquired; 23:00-to-last-train intervals have unknown duration. Master averages use September only and include observed night zeros.',
 'Census 2011 remains historical. A 2012 198-ward geometry layer is joined by ward code to Census; geometry-only overlap crosswalks link it to December 2025 wards. Geometry repairs are recorded. Two Electronic City candidates lie outside available municipal ward polygons and retain null ward joins.',
 'Yellow Line inauguration is verified as 2025-08-10; first commercial service date is not independently asserted. Blue Line official completion programmes are historical, not guaranteed openings. July 1, 2027 and the 24-month delayed July 1, 2029 date, plus a 10% illustrative effect, are explicitly assumed and excluded from baseline features. Blue geometry is an OSM partial alignment, not a verified official station-access map.',
 'All candidate premises, areas, financials and existing company branches are synthetic. Public commercial listings were retrieved but mixed offices, asking prices and promoted distant properties do not verify available grocery premises or lease benchmarks.',
 'Metro repository ODbL and OpenCity non-commercial metadata differ; BMRCL contents copyright is also stated. Rights for commercial redistribution remain unresolved. OSM ODbL, WorldPop CC-BY-4.0 and DataMeet CC-BY-SA-2.5-IN attribution/share-alike obligations are preserved.',
 'Some original release dates are unverified and remain null. Retrieval times and file hashes are stored separately; retrieval is never substituted for observation or release date.',
 'source_quality_score is 6/8 evidence-family availability, not a calibrated reliability measure, model confidence or prediction score. It does not measure source completeness within the corridor.'
]

def reports(master,manifest):
    failed=[r for r in CHECKS if r['status']=='FAIL']
    dimensions=[]
    for path in sorted(FINAL.glob('*.csv')):
        rows=read(path.name)
        with path.open(encoding='utf-8',newline='') as f0:columns=next(csv.reader(f0))
        dimensions.append(dict(path=path.relative_to(ROOT).as_posix(),rows=len(rows),columns=len(columns),null_values=sum(not v for r in rows for v in r.values()),validation_status='PASS' if not failed else 'SEE_FAILED_CHECKS',sha256=sha(path)))
    with (REPORTS/'table_dimensions.csv').open('w',newline='',encoding='utf-8') as f0:
        w=csv.DictWriter(f0,fieldnames=list(dimensions[0]));w.writeheader();w.writerows(dimensions)
    readiness={
      'reference_sales_training':'NOT_READY: no observed sales labels by design; no training or split performed',
      'reference_sales_inference':'FEATURES_PREPARED_WITH_NULLS: needs later compatible trained artifact, missingness policy and feature contract',
      'DaypartDNA':'READY_WITH_ASSUMPTIONS: 4995 mapped POIs before category filtering, 6 bins, weights, schedules, availability and evidence inputs',
      'infrastructure_scenarios':'READY_FOR_ASSUMED_DEMO: current/opens/delayed inputs, no verified Blue opening date',
      'Huff_cannibalisation':'INPUTS_PREPARED_WITH_ASSUMPTIONS: unique 100 cell wallets, 4 fictional branches, external competitors, attraction defaults; no allocation run',
      'financial_calculations':'INPUTS_PREPARED_WITH_PRICE_MISMATCH: all required store financial fields and project assumptions; 2024 wallets versus 2026 demo costs need explicit later treatment',
      'FailFast':'PARTIAL: financial inputs exist; critical demand/model evidence and routing/households remain unavailable; no viability calculated',
      'sensitivity':'INPUTS_PREPARED: labelled low/base/high commercial assumptions, no forecasting performed',
      'ranking_and_portfolio':'INPUTS_PREPARED_ONLY: 10 candidates and budget; awaits later evaluation/inference/network/finance; no ranking/optimization performed'}
    quality=dict(verdict='DATASET_BLOCKED' if failed else 'DATASET_READY_WITH_LIMITATIONS',
      feature_snapshot_id=CONFIG['feature_snapshot_id'],source_manifest_id=CONFIG['source_manifest_id'],
      reference_date=CONFIG['reference_date'],generated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
      checks=CHECKS,checks_passed=sum(r['status']=='PASS' for r in CHECKS),checks_failed=len(failed),
      tables=dimensions,master_origin_breakdown=METRICS['master_value_origins'],
      master_origin_scope='500 master record/field values only; observed source records are transformed before entry into this feature table. Derived values may depend on explicit assumptions.',
      observed_supporting_records=dict(osm_raw_elements=METRICS['osm_raw_elements'],deduplicated_pois=len(read('pois.csv')),corridor_metro_intervals=len(read('metro_hourly.csv')),census_2011_wards=len(read('census_2011_wards.csv'))),
      metrics=METRICS,limitations=LIMITATIONS,readiness=readiness,git=dict(branch=git('branch','--show-current'),head=git('rev-parse','HEAD'),new_commits=0,pushes=0,branch_changes=0,all_new_work_local_uncommitted=True))
    jsave(REPORTS/'data_quality_report.json',quality);jsave(FINAL/'data_quality_report.json',quality)
    logs=json.loads((DATA/'acquisition_log.json').read_text(encoding='utf-8'))
    acq=['# Bengaluru dataset acquisition report','',f'Reference date: {CONFIG["reference_date"]}. Sources were retrieved on October 24, 2026; exact UTC timestamps are in acquisition_files.csv.','',
         'All six canonical Navi Mumbai fixture files were inspected and preserved. Counts: 10 candidates, 4 fictional stores, 100 cells, 60 POIs, 1 hypothetical event and 36 assumed category/bin weights. No coordinates or financial actuals were copied from Navi Mumbai. The approved engineering weights and project-level budget/horizon/discount assumptions remain assumptions.','',
         'The first DataMeet candidate file (`raw/wards/BBMP_198.geojson`) is actually a **243-ward 2022 layer**, as its README makes clear. It is archived as an unused acquisition and is not used for Census joining. The separately acquired `BBMP_2012_198.geojson` contains the historical 198 wards.','',
         '| Status | Local file | Bytes | Source URL |','|---|---|---:|---|']
    for r in logs:acq.append(f'| {r["status"]} | {r["path"]} | {r.get("bytes", "")} | {r["url"]} |')
    acq += ['', 'Failed endpoints have legitimate alternatives archived above. eSankhyiki HTTP 200 app shells are not counted as downloaded statistical records. The official full NSS report supplies the expenditure observations instead. Census portal TLS validation was not bypassed; OpenCity CSVs supply the historical records. The proprietary commercial HTML is retained locally only and excluded from the deliverable ZIP.', '', 'All raw files have exact URLs, retrieval times and SHA-256 hashes in acquisition_files.csv. Downloading a document does not imply that all its contents were used. Upstream parse.py is archived for inspection only, never executed.']
    (REPORTS/'acquisition_report.md').write_text('\n'.join(acq),encoding='utf-8')
    temporal=['# Temporal alignment report','', '| Source | Observation / reference period | Snapshot use |','|---|---|---|']
    for r in manifest:temporal.append(f'| {r["source_id"]} | {r["observation_start_date"]} to {r["observation_end_date"]} | {r["notes"]} |')
    temporal += ['', 'Source observation dates, release dates, exact retrieval timestamps, snapshot valuation date and monetary price bases are separate. Unknown release dates remain null. WorldPop 2020 is not grown to 2026. Census 2011 is not relabelled as a 2025 ward population.', '',
       'Metro conversion reads original wide workbooks. August labels are preserved verbatim. H00-H23 September codes are recorded as reported clock hours; timestamps include +05:30 and timezone Asia/Kolkata. August 23:00 to last train has null end/duration and is excluded from hourly averages. August exits remain null. Derived origin-destination destination sums in the alternative processed CSV do not establish the clock time of station exits.', '',
       'All master ridership averages use paired September 1-30, 2025 observations only: 22 weekdays and 8 weekend days per station, each with 24 observed clock intervals. These are historical proxies, not 2026 predictions. August/September coverage and all gaps across August 1-September 30 are explicit in metro_date_coverage.csv. No missing service day is filled with zero.', '',
       'Six bins use starting local days. For example Saturday 02:00 belongs to Friday weekday_night; Monday 02:00 belongs to Sunday weekend_evening. Per-hour POI opportunity indices are kept separate from duration/frequency-weighted weekly exposures and shares. Measured metro counts are not added to the POI index.', '',
       f'Addressable grocery expenditure per person per month is INR {METRICS["grocery_monthly_per_capita_inr"]:.3f}: sum of Karnataka urban HCES Statement 3U categories 1-13, plus 0.5 times category 14, plus toiletries (18) and household consumables (19). A twelve-month annualization is applied to source-estimated population. The 0.5 eligibility split and transfer of the Karnataka urban average to local residents are assumptions, not store capture rates.', '',
       'wallet_price_year=2024 denotes nominal 2023-24 survey prices. Candidate cost assumptions use nominal INR at October 24, 2026. The mismatch is retained explicitly; no unverified inflation factor was applied. Later financial inference must resolve it or operate in a declared mismatch assumption mode.', '',
       'Blue Line construction/alignment records and hypothetical 2027/2029 scenario dates never enter current baseline features. The 2026-12 published official programme is historical and not copied into verified_opening_date. Yellow Line inauguration is recorded separately from commercial opening.']
    (REPORTS/'temporal_alignment_report.md').write_text('\n'.join(temporal),encoding='utf-8')
    missing=['# Missing data report','']+[f'- {x}' for x in LIMITATIONS]
    missing += ['', 'missing_fields.csv records every generated field classification and each nullable supporting column (wildcard record ID with null_count). ASSUMPTION_ALLOWED and SYNTHETIC_DEMO_ALLOWED are the only generation categories. FETCH_RETRY is used for absent opening hours; those original observations remain null while separate explicitly assumed availability is recorded. No census counts, metro counts, dates or training labels are generated.']
    (REPORTS/'missing_data_report.md').write_text('\n'.join(missing),encoding='utf-8')
    licence=['# Source attribution and use conditions','', 'This local package combines separately attributed datasets and explicit assumptions. No single unrestricted licence is asserted for every component.','',
      '- OpenStreetMap data: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright. ODbL 1.0 attribution and database share-alike requirements apply to relevant derived database components.',
      '- WorldPop, University of Southampton and collaborators: Global 2000-2020 UN-adjusted aggregated 1km population, India 2020. CC-BY-4.0; exact downloaded licence text is archived in raw/worldpop_licence.txt. The 100m underlying-series API metadata is contextual and is not misrepresented as the downloaded 1km release.',
      '- BMRCL ridership obtained under RTI, published by Vonter/bmrcl-ridership-hourly at the Git revision archived in raw/github_tree.json. ODbL repository licence is archived; the README notes BMRCL content copyright. OpenCity labels corresponding RTI data non-commercial. This conflict remains unresolved for commercial redistribution.',
      '- Census of India 2011 and GBA December 2025 ward records via OpenCity. Catalogue metadata labels these Other (Public Domain). Original attribution is retained.',
      '- DataMeet Bangalore 2012 ward geometry: Creative Commons Attribution-ShareAlike 2.5 India, per archived raw/wards/datameet_Readme.md. Embedded population attributes are not used.',
      '- MoSPI NSS Report 592, HCES 2023-24, Statement 3U, Karnataka urban column 14. Exact small table values are extracted with source locations. Government statistical dissemination policy is recorded; no blanket relicensing of the full government report is asserted.',
      '- Prime Minister Office / Press Information Bureau and Government of Karnataka Economic Survey 2025-26 retain their government publication attribution.',
      '- Magicbricks commercial-page acquisition was inspected for source suitability only. It supplies no redistributed listing records and its proprietary raw HTML is excluded from the ZIP.', '',
      'The ZIP is created locally only. No dataset is uploaded or pushed to GitHub.']
    (REPORTS/'ATTRIBUTION_AND_LICENCES.md').write_text('\n'.join(licence),encoding='utf-8')
    report=['# StoreScout Bengaluru dataset completion report','',f'Verdict: **{quality["verdict"]}**. {quality["checks_passed"]} integrity checks passed; {quality["checks_failed"]} failed.','',
      '## A. Acquisition and inspected fixtures','', 'Actual public-source files are archived in raw/ and indexed with URLs, timestamps and hashes in final/acquisition_files.csv. See acquisition_report.md for every success, failed endpoint and alternative. Census 2011 tables, WorldPop India 2020 raster, BMRCL original hourly workbooks, OSM POIs/roads, historical and 2025 ward geometry, official HCES expenditure tables and official infrastructure documents were downloaded.','',
      'The six existing demo JSON fixtures were inspected (10 sites, 4 branches, 100 cells, 60 POIs, 1 event, six-bin assumed weight matrix) and remain byte-for-byte unchanged. Backend schemas and pipeline seams were inspected and unchanged.','',
      '## B. Output dimensions','', '**site_features.csv contains exactly 10 candidate rows and exactly 50 columns in the requested order.** CSV empty fields mean null, never implicit zero.','',
      '| Path | Rows | Columns | Null values | Validation |','|---|---:|---:|---:|---|']
    for r in dimensions:report.append(f'| {r["path"]} | {r["rows"]:,} | {r["columns"]} | {r["null_values"]:,} | {r["validation_status"]} |')
    report += ['', 'data_quality_report.json is supplied in both final/ and reports/. Geographic line/polygon records are GeoJSON, and the clipped population window is a GeoTIFF in processed/.', '',
      '## C. Data origin','', 'For the 500 master site-feature values: 400 derived (80%), 80 synthetic/assumed (16%), 20 unresolved nulls (4%), zero directly copied observed values, zero copied fixture values. Counts and station activity are derived from real records; derived values are not all purely observed because spending and opportunity depend on separately recorded assumptions. These counts include identifiers/status metadata and must not be interpreted as a market-evidence percentage.','',
      f'Observed supporting evidence: {METRICS["osm_raw_elements"]:,} OSM records before filtering/deduplication, {METRICS["poi_rows"]:,} retained POIs, {METRICS["metro_corridor_hourly_rows"]:,} corridor metro interval records from original workbooks, {len(read("census_2011_wards.csv"))} historical Census wards, and {METRICS["population_raster_pixels"]} clipped source-raster pixels. The six-bin fixture supplies 36 assumed weights; project budget, discount rate and horizon retain their approved fixture assumption status. synthetic_assumptions.csv supplies record-level generated values, units, reasons and low/base/high bounds where meaningful.', '',
      '## D. Temporal integrity','', 'See temporal_alignment_report.md. Metro source periods are August 1-18 and September 1-30, 2025; all master metro aggregates use September 2025 only. Population reference year 2020, Census 2011, boundaries 2012/December 2025, and expenditure August 2023-July 2024 remain separate. All interval timestamps use Asia/Kolkata (+05:30). Historical proxies are explicit. The 2024 wallet versus 2026 cost price mismatch remains documented.', '',
      '## E. Data quality','', f'{METRICS["poi_duplicates_removed"]} same-name/category OSM duplicates were removed and logged; {METRICS["poi_excluded_centres"]} boundary-intersecting elements with out-of-bound centres were excluded. No duplicate metro key is present. {METRICS["ward_geometry_repairs"]} source ward geometries required validity repair. Source IDs resolve and every master field has a lineage entry. Two Electronic City sites have no municipal ward join, without changing their valid corridor locations.', '',
      '## F. StoreScout compatibility','']
    for component,status in readiness.items():report.append(f'- **{component}**: {status}')
    report += ['', 'The generated inputs validate against the existing canonical Project, Site and Store schemas after explicit column selection/renaming. No endpoint or schema was modified. The dataset is not automatically loaded into the Navi Mumbai demo; backend integration remains a later task.', '',
      '## G. Final deliverables','', f'- Master: `{(FINAL/"site_features.csv").resolve()}`', f'- Supporting datasets, manifest and lineage: `{FINAL.resolve()}`',
      f'- Quality report: `{(REPORTS/"data_quality_report.json").resolve()}`',f'- ZIP: `{(ROOT/"StoreScout_Bengaluru_Dataset.zip").resolve()}`', '',
      '## H. Git confirmation','',f'Branch: `{quality["git"]["branch"]}`. Existing HEAD: `{quality["git"]["head"]}`. No commits, pushes, branch switches or other Git state/history mutations were performed. Existing tracked code and fixtures are unchanged; all new files remain local and uncommitted.', '',
      '## I. Limitations and next dependency','']+[f'{i}. {x}' for i,x in enumerate(LIMITATIONS,1)]
    report += ['', 'Next dependency: a separately authorised model-data/training instruction and a coordinated backend integration of this distinct feature snapshot. No domain engine, model, fitted artifact, training labels, split, API or frontend implementation was added. Stop after dataset creation, validation and reporting.']
    (REPORTS/'completion_report.md').write_text('\n'.join(report),encoding='utf-8')
    return quality

def package(quality):
    if quality['checks_failed']:raise RuntimeError('Dataset has failed integrity checks; ZIP is not created.')
    readme='''# StoreScout Bengaluru dataset

Reference date: 2026-10-24. Read reports/completion_report.md first.
CSV is UTF-8 with a header row; an empty field is null. All monetary amounts
are INR. Costs and wallet prices have different explicitly recorded bases.
No model, labels, forecast, allocation or ranking is included.

Offline reproduction (Python 3.12):

    python -m pip install numpy rasterio shapely pyproj openpyxl pypdf pydantic
    python ml/bengaluru/inspect_data.py
    python ml/bengaluru/build.py
    python ml/bengaluru/validate.py

Run from the original repository root. Existing backend canonical schemas are
read for compatibility validation; they are not copied into this dataset ZIP.
The immutable raw snapshots and their SHA-256 hashes reproduce the dataset
offline. Re-fetching live OSM later can change inputs and requires a new snapshot.
The acquisition scripts preserve source files and failures. acquisition_files.csv
contains every original URL, exact retrieval time, size and hash.

The ZIP intentionally excludes the proprietary commercial-listing HTML and
Python caches. See reports/ATTRIBUTION_AND_LICENCES.md for component terms.
Git history and branches have not been modified. All additions are uncommitted.
'''
    (DATA/'README.md').write_text(readme,encoding='utf-8')
    files=[]
    for base in [DATA,ROOT/'ml/bengaluru']:
        for p in base.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name not in ['commercial_rent_attempt.html','deliverable_checksums.json']:files.append(p)
    hashes=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]
    jsave(REPORTS/'deliverable_checksums.json',hashes)
    files.append(REPORTS/'deliverable_checksums.json')
    output=ROOT/'StoreScout_Bengaluru_Dataset.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(files)):z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert 'data/bengaluru/final/site_features.csv' in z.namelist()
        assert not any('commercial_rent_attempt.html' in n or '__pycache__' in n for n in z.namelist())
    print(json.dumps(dict(verdict=quality['verdict'],checks_passed=quality['checks_passed'],checks_failed=quality['checks_failed'],
       tables=len(quality['tables']),master=next(r for r in quality['tables'] if r['path'].endswith('/site_features.csv')),
       zip_path=str(output),zip_bytes=output.stat().st_size,zip_members=len(set(files)),zip_integrity='PASS'),indent=2))

if __name__=='__main__':
    master,manifest=validate()
    result=reports(master,manifest)
    for r in CHECKS:
        if r['status']=='FAIL':print('FAIL',r)
    package(result)
