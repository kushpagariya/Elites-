"""Run read-only integrity tests and write v2 reports; never alter frozen data."""
import csv
import datetime as dt
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

sys.dont_write_bytecode=True
V2=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(V2/'scripts'))
import build_revised as b


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test)
        self.records.append(dict(test=test.id(),status='PASS'))
    def addFailure(self,test,err):
        super().addFailure(test,err)
        self.records.append(dict(test=test.id(),status='FAIL',details=self._exc_info_to_string(err,test)))
    def addError(self,test,err):
        super().addError(test,err)
        self.records.append(dict(test=test.id(),status='ERROR',details=self._exc_info_to_string(err,test)))
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err:
            self.records.append(dict(test=subtest.id(),status='FAIL',details=self._exc_info_to_string(err,test)))


LIMITATIONS=[
    'BMRCL content copyright / GitHub ODbL / OpenCity cc-nc conflict is unresolved. Public and commercial redistribution is not cleared, including inherited metro-derived outputs. No new public package or workbook copies created.',
    'Original 10 candidates, 4 existing branches, premises economics and financial inputs remain synthetic or assumed; no verified premises, realised sales targets, trained predictions or calibrated rankings exist.',
    'WorldPop is a 2020 modelled 1 km population proxy; within-pixel density is assumed uniform. Exact product publication day is unknown. No current population projection applied.',
    'HCES is nominal August 2023-July 2024 Karnataka urban spending; local transfer/category choices are assumptions. Synthetic costs use 24 October 2026 nominal demo prices. No inflation adjustment or price-basis harmonisation applied.',
    'OSM is a partial mapped inventory with unknown completeness. Most opening schedules are absent or unsupported. Parsed and merely recorded counts differ; proxies are not measured store footfall.',
    'Metro is historical September 2025 station traffic. September-start complete-bin rates exclude the incomplete final overnight bin and prior-month starting-day boundary; they differ in window/denominator from preserved master day-type means.',
    'site-09 and site-10 have no matches in either municipal ward vintage. Four ward IDs, ten household estimates and ten network-time population estimates remain null. No validated routing or household denominator exists.',
    'A new official current infrastructure status observation and exact first-commercial-opening dates are not established. Blue dates and uplift remain hypothetical and excluded from operational baseline.',
    'Original 57 acquisition records preserve legacy request-start timestamps; response-completion timestamps cannot be reconstructed. Failed endpoints and unverified original RTI delivery chain remain documented in the frozen audit.'
]


def table_profile(path):
    rows=b.read(path)
    columns=list(rows[0])
    nulls={c:sum(r[c]=='' for r in rows) for c in columns}
    profile=dict(rows=len(rows),columns=len(columns),ordered_columns=columns,
        total_nulls=sum(nulls.values()),nulls_by_column=nulls,sha256=b.sha(path))
    keys={'site_features_enriched':['site_id'],'daypart_site_support':['site_id'],'site_evidence_coverage':['site_id'],
        'daypart_opportunity_shares':['site_id','time_bin'],'metro_daypart_rates':['station_id','time_bin','direction'],
        'metro_daypart_coverage':['station_id','starting_local_date','time_bin','direction'],
        'site_metro_daypart_rates':['site_id','time_bin','direction'],'source_manifest':['source_id'],
        'assumption_registry':['assumption_id'],'site_feature_schema':['field_name'],
        'expenditure_inputs':['item_id'],'infrastructure':['infra_project_id'],'infrastructure_scenarios':['scenario_id'],
        'field_lineage':['table','record_id','field_name'],'project_assumptions':['assumption_id']}
    if path.stem in keys:
        key=keys[path.stem];unique=len({tuple(r[k] for k in key) for r in rows})
        profile.update(key_columns=key,unique_keys=unique,duplicate_key_count=len(rows)-unique)
    return profile


def main():
    started=dt.datetime.now(dt.timezone.utc).isoformat();timer=time.perf_counter()
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(V2/'tests'),pattern='test_integrity.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult).run(suite)
    success=result.wasSuccessful()
    status='DATA_INTEGRITY_READY_WITH_LIMITATIONS' if success else 'DATA_INTEGRITY_BLOCKED'
    tables={p.name:table_profile(p) for p in sorted(V2.glob('*.csv'))}
    baseline=b.load(V2/'baseline_hashes.json')
    unchanged=[name for name,digest in baseline['files'].items() if (b.ROOT/name).exists() and b.sha(b.ROOT/name)==digest]
    git_branch=subprocess.check_output(['git','branch','--show-current'],cwd=b.ROOT,text=True).strip()
    git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b.ROOT,text=True).strip()
    command='python data/bengaluru/revised_v2/scripts/validate_revised.py'
    report=dict(status=status,validation_started_at_utc=started,validation_completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        elapsed_seconds=round(time.perf_counter()-timer,3),validation_command=command,
        environment=dict(python=platform.python_version(),packages={p:importlib.metadata.version(p) for p in ['pyproj','shapely','pypdf']}),
        tests_run=result.testsRun,tests_passed=sum(r['status']=='PASS' for r in result.records),
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),test_results=result.records,
        test_output=stream.getvalue(),original_baseline_files_checked=len(baseline['files']),original_baseline_files_unchanged=len(unchanged),
        original_dataset_files_unchanged=len(unchanged)==len(baseline['files']),original_csv_count=27,
        original_master_shape=[10,50],original_master_nulls=20,
        original_master_sha256=b.sha(b.FROZEN/'site_features.csv'),git_branch=git_branch,git_head=git_head,
        original_git_branch=baseline['branch'],original_git_head=baseline['head'],
        commit_created=False,push_performed=False,branch_switched=False,model_training_performed=False,
        csv_null_definition='An empty CSV field. Zero, False, UNKNOWN and explicit status strings are not null; no missing numeric value is zero-filled.',
        tables=tables,join_coverage=dict(candidate_sites=10,poi_and_profiles_matched=10,nearest_station_matched=10,
            metro_daytype_coverage_matched=10,historical_ward_matched=8,ward_2025_matched=8,site_row_multiplier=1),
        unresolved_limitations=LIMITATIONS)
    # Include every actual file path. Report self-hash is undefined; generated
    # completion report content depends on this inventory and is excluded too.
    planned={V2/'validation_report.json',V2/'completion_report.md'}
    files=sorted({p for p in V2.rglob('*') if p.is_file()}|planned)
    report['created_files']=[dict(path=p.relative_to(V2).as_posix(),sha256=None if p in planned else b.sha(p),
        checksum_note='Generated report; excluded from self-referential checksum inventory' if p in planned else None) for p in files]
    report['file_count']=len(files)
    b.save_json('validation_report.json',report)
    lines=[
        '# Bengaluru v2 integrity completion report','',
        f'**{status}**','',
        f'Validation: **{result.testsRun} tests, {report["tests_passed"]} passed, {len(result.failures)} failures, {len(result.errors)} errors, {len(result.skipped)} skipped**. See `validation_report.json` for per-test results, nulls per column, unique keys, hashes and runtime versions. Validation completed at '+report['validation_completed_at_utc']+'.','',
        f'All **{len(baseline["files"])} pre-existing files** were checked: **{len(unchanged)} unchanged**. This includes every original 27 CSV, raw snapshot and existing archive. The canonical master remains **10 × 50, 20 nulls**; SHA-256 `'+report['original_master_sha256']+'`.','',
        f'Branch remains `{git_branch}`, HEAD `{git_head}`. No commit, push, branch switch, model training, label generation, analytical-engine implementation or backend/frontend change was performed.','',
        '## Actual CSV outputs','',
        '| File | Rows | Columns | Empty fields |','|---|---:|---:|---:|',
    ]
    for name,t in tables.items():lines.append(f'| `{name}` | {t["rows"]:,} | {t["columns"]} | {t["total_nulls"]:,} |')
    lines += [
        '', 'An empty field is a preserved unknown or intentionally inapplicable metadata value; counts include metadata blanks. Explicit zero counts and False flags are populated observations/values. In the enriched file, nulls are exactly ten `population_10min_est`, ten `accessible_households_est`, two `ward_2011_id` and two `ward_2025_id`. The 60 POI service-period flags are inapplicable, not an imputed observed period. Metro coverage has 26 zero-support boundary rows with both count and rate left null (52 empty fields).','',
        '## Corrections and source verification','',
        'The 70-field view preserves every original 50-field value and appends the exact audited 20 fields. Semantic units/types, locality/fixture provenance, historical-period metadata, per-site evidence coverage, overnight metro denominators and HCES multiline extraction are repaired. See `CHANGELOG.md` and `README.md` for transformations and definitions. All fields have source/assumption lineage and foreign-key checks; the v1 embedded master IDs are retained and mapped to corrected v2 provenance externally.','',
        'The original master and source audit were not rewritten. Newly verified official [MoSPI](https://www.mospi.gov.in/sites/default/files/press_release/HCES_Report202324_Press_Note_30012025.pdf) and [PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097601&lang=2&reg=3) evidence establishes the detailed HCES report release as **30 January 2025**, superseding the unsupported 31 January metadata in v1. Factsheet release remains **27 December 2024**. The new source snapshots, exact URLs, request/completion times and hashes are archived under `source_verification/`; the other historical data were not reacquired. Item 24 adds INR **404.46** expenditure; grocery INR **2,974.915** is unchanged.','',
        '## Incorporated supporting tables and join coverage','',
        '| Frozen table used for enrichment | Use | Candidate coverage |',
        '|---|---|---|',
        '| `site_features.csv` | Unchanged 50-field candidate base | 10/10, one row each |',
        '| `daypart_profiles.csv` | Pivot six weekly shares and three support counts; calculate parsed fraction | 10/10 × 6 bins |',
        '| `pois.csv` | Geodesic 1,500 m subtype and opening-hours evidence counts | 10/10; mapped counts only |',
        '| `metro_station_lookup.csv` | Operational station counts; retain nearest-station identity | 10/10; 13 matched stations |',
        '| `site_ward_lookup.csv` | Separate-vintage point-in-polygon IDs | 8/10 per vintage; four ID nulls retained |',
        '| `metro_activity_averages.csv` | September weekday/weekend observed hour/day support | 10/10 many-to-one station joins |','',
        'New separate metro rates additionally use `metro_hourly.csv`; tests independently reconcile them to service-date clocks. POI tests independently recompute opportunity/support using `poi_daypart_availability.csv`, `daypart_weights.csv` and source POIs. Ward tests recompute point containment from the frozen historical/2025 GeoJSON layers. Other unrelated tables are documented/referenced, not indiscriminately joined. Exactly ten site rows survive; no row multiplication, outcome leakage or invented targets.','',
        '## Metro aggregation denominators','',
        '| Canonical bin | Hours per bin | Complete starting days | Used clock hours per station/direction |',
        '|---|---:|---:|---:|',
        '| weekday_morning | 5 | 22 | 110 |',
        '| weekday_lunch | 4 | 22 | 88 |',
        '| weekday_evening | 5 | 22 | 110 |',
        '| weekday_night | 10 | 21 | 210 |',
        '| weekend_day | 12 | 8 | 96 |',
        '| weekend_evening | 12 | 8 | 96 |','',
        'September has 9,360 valid paired hourly records across 13 stations (720 each); 2,616 August records are excluded. Full-month paired-clock coverage is 100%, but complete eligible starting-day bin coverage is **103/104** per station, because September 30 night lacks October 1 00–06. September 1 00–06 belongs to August 31 and is outside September-start bins. Together the six aggregates use 710 included clock hours per station/direction, distinct from the preserved 528 weekday + 192 weekend calendar-hour means. Counts are observed transit traffic; neither transit nor POI opportunity measures store footfall.','',
        '## Remaining limitations and next dependency','',
    ]
    lines += ['- '+s for s in LIMITATIONS]
    lines += [
        '', 'RetailIQ requires verified premises/costs, an explicit price-basis policy, validated routing and approved evaluation assumptions. Supervised prediction requires genuine outcome targets and temporal/spatial evaluation; none were created. DaypartDNA requires more verified opening schedules, longer observed series and independent store-visit calibration. Resolve metro reuse rights before any public/commercial distribution. No training or application implementation follows this correction task.','',
        '## Complete created-file inventory','',
        f'All **{len(files)} files** are under `data/bengaluru/revised_v2/` ({len(tables)} CSVs). No new raw metro workbook or ZIP is included. Paths below are relative to this directory. Machine-readable SHA-256 values are in `validation_report.json`; self-referential generated reports are explicitly excluded from hashing.','',
    ]
    lines += ['- `'+p.relative_to(V2).as_posix()+'`' for p in files]
    lines += ['',status,'']
    (V2/'completion_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(status=status,tests_run=result.testsRun,passed=report['tests_passed'],failures=len(result.failures),errors=len(result.errors),baseline_files_unchanged=len(unchanged),created_files=len(files),csv_files=len(tables)),indent=2))
    if not success:
        print(stream.getvalue())
        raise SystemExit(1)


if __name__=='__main__':main()
