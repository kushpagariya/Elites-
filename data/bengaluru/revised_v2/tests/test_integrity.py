"""Read-only integrity checks; test mutations are in-memory copies only."""
import csv
import datetime as dt
from decimal import Decimal
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unittest
from collections import defaultdict

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bengaluru_v2_builder', V2/'scripts/build_revised.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
from pyproj import Geod
from shapely.geometry import Point, shape
from pypdf import PdfReader

G = Geod(ellps='WGS84')


class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = {p.stem: b.read(p) for p in V2.glob('*.csv')}
        cls.old = {p.stem: b.read(p) for p in b.FROZEN.glob('*.csv')}
        cls.master = cls.old['site_features']
        cls.enriched = cls.v['site_features_enriched']
        cls.meta = b.load(V2/'dataset_metadata.json')
        cls.schema = {r['field_name']: r for r in cls.v['site_feature_schema']}

    def test_01_frozen_files_and_git_identity(self):
        saved = b.preserved_baseline()
        self.assertEqual(len(saved['files']), 199)
        self.assertEqual(len(list(b.FROZEN.glob('*.csv'))), 27)
        self.assertEqual(b.sha(b.FROZEN/'site_features.csv'), '766ba60f599277b70a810993088a27317154b5b10b561b7516d0cff602584868')
        for args, expected in [(['branch','--show-current'], 'ML'), (['rev-parse','HEAD'], saved['head'])]:
            self.assertEqual(subprocess.check_output(['git', *args], cwd=b.ROOT, text=True).strip(), expected)
        self.assertEqual(subprocess.check_output(['git','diff','--name-only','HEAD'], cwd=b.ROOT, text=True).strip(), '')

    def test_02_exact_order_shape_and_string_preservation(self):
        columns = list(self.enriched[0])
        self.assertEqual(len(self.enriched), 10)
        self.assertEqual(len(columns), 70)
        self.assertEqual(columns, list(self.master[0]) + b.EXTRA)
        self.assertEqual([r['site_id'] for r in self.enriched], [r['site_id'] for r in self.master])
        self.assertEqual(len({r['site_id'] for r in self.enriched}), 10)
        for original, revised in zip(self.master, self.enriched):
            self.assertEqual({k:revised[k] for k in original}, original)

    def test_03_null_preservation_no_unsupported_imputation(self):
        self.assertEqual(sum(not v for r in self.master for v in r.values()), 20)
        self.assertEqual(sum(not v for r in self.enriched for v in r.values()), 24)
        for r in self.enriched:
            self.assertEqual(r['accessible_households_est'], '')
            self.assertEqual(r['population_10min_est'], '')
            for field in ['ward_2011_id','ward_2025_id']:
                self.assertEqual(not bool(r[field]), r['site_id'] in ['site-09','site-10'])
        self.assertTrue(all(r['households_est']=='' for r in self.old['spending_cells']))

    def test_04_provenance_foreign_keys_all_tables(self):
        sources = {r['source_id'] for r in self.v['source_manifest']}
        assumptions = {r['assumption_id'] for r in self.v['assumption_registry']}
        self.assertEqual(len(sources), len(self.v['source_manifest']))
        self.assertEqual(len(assumptions), len(self.v['assumption_registry']))
        # Include referenced frozen supporting tables; v2 overrides repaired versions.
        for table, rows in (self.old | self.v).items():
            if table == 'field_lineage':
                rows = self.v[table]
            for i, row in enumerate(rows):
                # Frozen missing_fields.source_attempts is a narrative field,
                # sometimes a locator, and is not declared a source-ID FK.
                for field, allowed in [('source_id',sources),('source_ids',sources),('status_source_id',sources),('release_evidence_source_ids',sources),('assumption_id',assumptions),('assumption_ids',assumptions)]:
                    for token in row.get(field, '').split(';'):
                        if token:
                            with self.subTest(table=table, row=i, field=field, token=token):
                                self.assertIn(token, allowed)
        for r in self.enriched:
            self.assertEqual(r['source_manifest_id'], self.meta['master_embedded_source_manifest_id'])
        self.assertEqual({r['source_manifest_id'] for r in self.v['source_manifest']}, {self.meta['corrected_provenance_manifest_id']})

    def test_05_locality_and_existing_assumption_records(self):
        rows = self.v['synthetic_assumptions']
        self.assertEqual(rows[:len(self.old['synthetic_assumptions'])], self.old['synthetic_assumptions'])
        loc = [r for r in rows if r['assumption_id']=='candidate-locality']
        self.assertEqual(len(loc), 10)
        self.assertEqual({r['record_id']:r['generated_value'] for r in loc}, {r['site_id']:r['locality'] for r in self.master})
        self.assertTrue(all(r['source_status']=='SYNTHETIC_DEMO' for r in loc))

    def test_06_all_master_cells_have_unique_typed_lineage(self):
        lines = self.v['field_lineage']
        keys = [(r['table'],r['record_id'],r['field_name']) for r in lines]
        self.assertEqual(len(keys),len(set(keys)))
        for table, fields in [('site_features',list(self.master[0])),('site_features_enriched',list(self.enriched[0]))]:
            subset = [r for r in lines if r['table']==table]
            self.assertEqual(len(subset), 10*len(fields))
            lookup = {(r['record_id'],r['field_name']):r for r in subset}
            data = self.master if table=='site_features' else self.enriched
            for row in data:
                for field, value in row.items():
                    l = lookup[row['site_id'],field]
                    self.assertEqual(l['logical_type'],self.schema[field]['logical_type'])
                    self.assertEqual(l['unit'],self.schema[field]['unit'])
                    self.assertTrue(l['formula_or_method'] and l['source_locator'])
                    if not value:
                        self.assertEqual(l['origin'],'UNRESOLVED_MISSING')

    def test_07_logical_types_all_v2_fields(self):
        lines = {(r['table'],r['field_name']):r for r in self.v['field_lineage'] if r['record_id']=='*'}
        for table, rows in self.v.items():
            if table=='field_lineage':
                continue
            for row in rows:
                for field,value in row.items():
                    s = self.schema[field] if table=='site_features_enriched' else lines[table,field]
                    if not value:
                        self.assertEqual(s['nullable'],'True', (table,field))
                        continue
                    dtype = s['logical_type']
                    if dtype=='Int64':
                        self.assertRegex(value,r'^-?\d+$',(table,field,value))
                    elif dtype=='Float64':
                        self.assertTrue(math.isfinite(float(value)),(table,field,value))
                    elif dtype=='Boolean':
                        self.assertIn(value,['True','False'],(table,field,value))
                    elif dtype=='ISODate':
                        self.assertEqual(dt.date.fromisoformat(value).isoformat(),value)
                    elif dtype=='ISOTimestamp':
                        self.assertIsNotNone(dt.datetime.fromisoformat(value).utcoffset())
                    else:
                        self.assertEqual(dtype,'String',(table,field))

    def test_08_semantic_units_currency_and_metadata(self):
        expected = {'population_1500m_est':'estimated persons','population_10min_est':'estimated persons','accessible_households_est':'estimated households','population_data_status':'status label','wallet_price_year':'year','competitor_count_1500m':'mapped POI count'}
        for name,unit in expected.items():
            self.assertEqual(self.schema[name]['unit'],unit)
        for binname in b.BINS:
            self.assertEqual(self.schema[binname+'_raw']['logical_type'],'Float64')
            self.assertIn('nominal hour', self.schema[binname+'_raw']['unit'])
        for r in self.v['field_lineage']:
            if 'INR' in r['unit']:
                self.assertEqual(r['currency'],'INR')
            if r['table'] in ['site_features','site_features_enriched'] and r['field_name'] in ['annual_wallet_inr','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr']:
                self.assertTrue(r['price_basis'])
        support = {(r['table'],r['field_name']):r for r in self.v['field_lineage'] if r['record_id']=='*'}
        self.assertEqual(support['spending_cells','monthly_grocery_per_capita_inr']['unit'],'INR/person/30 days')
        self.assertEqual(support['spending_cells','households_est']['logical_type'],'Float64')
        self.assertEqual(support['metro_hourly','interval_duration_minutes']['unit'],'minutes')
        self.assertIn('clock hour', support['metro_daypart_rates','rate_per_observed_clock_hour']['unit'])
        self.assertEqual(self.schema['wallet_price_year']['origin'],'METADATA_CONFIG')

    def test_09_origin_categories_and_synthetic_financials(self):
        for field in ['latitude','longitude','locality','store_size_sqm','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr']:
            self.assertEqual(self.schema[field]['origin'],'SYNTHETIC_DEMO')
        self.assertEqual(self.schema['annual_wallet_inr']['origin'],'DERIVED_WITH_ASSUMPTIONS')
        self.assertIn('MODELLED',self.schema['population_1500m_est']['origin'])
        self.assertIn('ASSUMPTIONS',self.schema['population_1500m_est']['origin'])
        support = {(r['table'],r['field_name']):r for r in self.v['field_lineage'] if r['record_id']=='*'}
        self.assertEqual(support['metro_hourly','entries']['origin'],'OBSERVED_SOURCE')
        self.assertEqual(support['expenditure_inputs','monthly_per_capita_inr']['origin'],'OBSERVED_SOURCE')
        self.assertEqual(support['pois','opening_hours']['origin'],'OBSERVED_SOURCE')

    def test_10_temporal_and_nominal_price_basis(self):
        m=self.meta
        self.assertEqual(m['population_reference_year'],2020)
        self.assertEqual(m['population_nominal_resolution'],'1km aggregated')
        self.assertIsNone(m['population_product_release_date'])
        self.assertEqual((m['hces_reference_start_date'],m['hces_reference_end_date']),('2023-08-01','2024-07-31'))
        self.assertEqual(m['wallet_price_year'],2024)
        self.assertEqual(m['metro_master_observation_period'],'2025-09-01/2025-09-30')
        self.assertEqual(m['valuation_date'],'2026-10-24')
        self.assertEqual(m['financial_price_basis_date'],'2026-10-24')
        self.assertTrue(m['financial_price_basis_mismatch'])
        self.assertFalse(m['inflation_conversion_applied'])
        self.assertTrue(all(r['wallet_price_year']=='2024' and r['snapshot_as_of_date']=='2026-10-24' for r in self.enriched))
        sources={r['source_id']:r for r in self.v['source_manifest']}
        for sid in ['worldpop-2020','census-2011','wards-2012','wards-2025','blue-official','approved-weights','assumptions','package-config']:
            self.assertEqual(sources[sid]['observation_start_date'],'')
        for sid in ['worldpop-2020','census-2011','wards-2012','wards-2025','blue-official']:
            self.assertEqual(sources[sid]['release_date'],'')

    def test_11_release_evidence_verifies_date_and_retrieval_integrity(self):
        evidence=b.load(V2/'source_verification/verification_log.json')
        self.assertEqual(len(evidence),2)
        self.assertEqual(self.meta['hces_detailed_report_release_date'],'2025-01-30')
        for e in evidence:
            p=V2/e['local_path']
            self.assertEqual(b.sha(p),e['sha256'])
            self.assertEqual(p.stat().st_size,e['bytes'])
            self.assertEqual(e['verified_release_date'],'2025-01-30')
            self.assertTrue(e['date_and_release_statement_verified'])
            self.assertLessEqual(dt.datetime.fromisoformat(e['request_started_at_utc']),dt.datetime.fromisoformat(e['response_completed_at_utc']))
            self.assertRegex(e['url'],r'^https://www\.(mospi|pib)\.gov\.in/')
        text=' '.join(PdfReader(V2/evidence[0]['local_path']).pages[0].extract_text().split()).lower()
        self.assertRegex(text,r'30(?:th)?\s+january\s*,?\s*2025')
        self.assertIn('released',text)
        html=(V2/evidence[1]['local_path']).read_text(encoding='utf-8',errors='replace')
        self.assertIn('30 JAN 2025',html)

    def test_12_original_source_acquisition_ledger_preserved(self):
        old=self.old['acquisition_files']
        new=self.v['source_acquisitions']
        self.assertEqual(len(old),57)
        self.assertEqual(len(new),59)
        for a,c in zip(old,new):
            self.assertEqual(a,{k:c[k] for k in a})
            self.assertEqual(c['request_started_at_utc'],a['retrieved_at_utc'])
            self.assertEqual(c['response_completed_at_utc'],'')
        sources={r['source_id']:r for r in self.v['source_manifest']}
        for row in self.old['source_manifest']:
            self.assertEqual(row['source_url'],sources[row['source_id']]['source_url'])

    def test_13_hces_multiline_parser_and_unchanged_grocery(self):
        text=PdfReader(b.BASE/'raw/hces_2023_24_full.pdf').pages[89].extract_text()
        parsed=b.parse_hces_statement3u(text)
        self.assertEqual(set(parsed),set(range(1,33)))
        self.assertEqual(parsed[24][1],Decimal('404.46'))
        rows=self.v['expenditure_inputs']
        self.assertEqual(len(rows),32)
        old={r['item_id']:r for r in self.old['expenditure_inputs']}
        for row in rows:
            if row['item_id'] in old:self.assertEqual(row,old[row['item_id']])
        grocery=sum(parsed[i][1] for i in range(1,14))+parsed[14][1]/2+parsed[18][1]+parsed[19][1]
        self.assertEqual(grocery,Decimal('2974.915'))
        self.assertEqual(b.load(V2/'expenditure_processing.json')['grocery_monthly_per_capita_inr'],str(grocery))
        without_footnote=re.split(r'\n\s*\*excludes',text,maxsplit=1)[0]
        with self.assertRaises(ValueError):b.parse_hces_statement3u(without_footnote+'\n24. duplicate 404.46\n')

    def test_14_infrastructure_known_facts_and_assumed_future(self):
        r={r['infra_project_id']:r for r in self.v['infrastructure']}
        y,c=r['metro-yellow'],r['metro-blue-2a']
        self.assertEqual(y['verified_inauguration_date'],'2025-08-10')
        self.assertEqual(y['included_current_baseline'],'True')
        self.assertEqual(c['included_current_baseline'],'False')
        self.assertEqual((c['hypothetical_open_date'],c['delayed_open_date']),('2027-07-01','2029-07-01'))
        self.assertEqual(c['assumed_demand_effect_fraction'],'0.1')
        self.assertEqual(c['scenario_date_status'],'ASSUMED_NOT_OFFICIAL')
        for row in r.values():
            self.assertEqual(row['status_reference_date'],'')
            self.assertEqual(row['status_verification_date'],'')
            self.assertEqual(row['verified_opening_date'],'')
            self.assertEqual(row['official_opening_date_status'],'UNKNOWN')
            self.assertEqual(row['baseline_valuation_date'],'2026-10-24')
        self.assertEqual(self.v['infrastructure_scenarios'],self.old['infrastructure_scenarios'])

    def test_15_overnight_and_exact_bin_boundaries(self):
        cases=[('2025-09-05',5,'2025-09-04','weekday_night'),('2025-09-05',6,'2025-09-05','weekday_morning'),('2025-09-05',10,'2025-09-05','weekday_morning'),('2025-09-05',11,'2025-09-05','weekday_lunch'),('2025-09-05',15,'2025-09-05','weekday_evening'),('2025-09-05',20,'2025-09-05','weekday_night'),('2025-09-06',2,'2025-09-05','weekday_night'),('2025-09-06',6,'2025-09-06','weekend_day'),('2025-09-06',17,'2025-09-06','weekend_day'),('2025-09-06',18,'2025-09-06','weekend_evening'),('2025-09-07',2,'2025-09-06','weekend_evening'),('2025-09-08',2,'2025-09-07','weekend_evening'),('2025-09-08',6,'2025-09-08','weekday_morning')]
        for date,h,start,binname in cases:
            self.assertEqual(b.assign_daypart(dt.date.fromisoformat(date),h),(dt.date.fromisoformat(start),binname))
        for hour in [-1,24]:
            with self.assertRaises(ValueError):b.assign_daypart(dt.date(2025,9,1),hour)

    def test_16_metro_valid_interval_population_and_clock_consistency(self):
        raw=self.old['metro_hourly']
        valid=[r for r in raw if r['service_date'].startswith('2025-09-') and r['interval_duration_minutes']=='60' and r['entries'] and r['exits']]
        self.assertEqual(len(valid),9360)
        self.assertEqual(len({(r['station_id'],r['service_date'],r['hour']) for r in raw}),len(raw))
        for r in valid:
            start=dt.datetime.fromisoformat(r['interval_start_local']);end=dt.datetime.fromisoformat(r['interval_end_local'])
            self.assertEqual(start.date().isoformat(),r['service_date'])
            self.assertEqual(start.hour,int(r['hour']))
            self.assertEqual(end-start,dt.timedelta(hours=1))
            self.assertEqual(start.utcoffset(),dt.timedelta(hours=5,minutes=30))
        self.assertTrue(any(r['entries']=='0' for r in valid))
        m=b.load(V2/'metro_aggregation_metadata.json')
        self.assertEqual(m['valid_paired_clock_intervals'],9360)
        self.assertEqual(m['excluded_intervals'],{'outside_september_source_period':2616})

    def test_17_metro_bad_intervals_rejected_or_excluded_without_zero_fill(self):
        row=next(r for r in self.old['metro_hourly'] if r['service_date']=='2025-09-01')
        stations={row['station_id']}
        with self.assertRaises(ValueError):b.aggregate_metro([row,row],stations)
        for patch in [{'entries':'-1'},{'entries':'1.5'},{'interval_end_local':row['interval_start_local']},{'hour':str((int(row['hour'])+1)%24)},{'station_id':'unmatched'}]:
            with self.assertRaises(ValueError):b.aggregate_metro([dict(row,**patch)],stations)
        for patch in [{'exits':''},{'entries':''},{'interval_duration_minutes':'120'}]:
            daily,rates,valid,excluded=b.aggregate_metro([dict(row,**patch)],stations)
            self.assertEqual(len(valid),0)
            self.assertEqual(excluded['missing_or_non_hourly_or_unpaired'],1)
            self.assertTrue(all(r['observed_count'] is None and r['rate_per_observed_clock_hour'] is None for r in daily+rates))

    def test_18_metro_coverage_and_month_edges(self):
        rows=self.v['metro_daypart_coverage']
        self.assertEqual(len(rows),2756)
        self.assertEqual(len({(r['station_id'],r['starting_local_date'],r['time_bin'],r['direction']) for r in rows}),len(rows))
        for r in rows:
            hours=int(r['observed_hours']);expected=int(r['expected_bin_hours'])
            self.assertEqual(r['is_complete_period']=='True',hours==expected)
            if not hours:
                self.assertEqual(r['observed_count'],'');self.assertEqual(r['rate_per_observed_clock_hour'],'')
            if r['starting_local_date']=='2025-08-31':
                self.assertEqual(r['included_in_aggregate'],'False')
                self.assertEqual(hours,6 if r['time_bin']=='weekend_evening' else 0)
            if r['starting_local_date']=='2025-09-30' and r['time_bin']=='weekday_night':
                self.assertEqual(hours,4);self.assertEqual(r['included_in_aggregate'],'False')

    def test_19_metro_rates_independent_calendar_denominators(self):
        expected={'weekday_morning':110,'weekday_lunch':88,'weekday_evening':110,'weekday_night':210,'weekend_day':96,'weekend_evening':96}
        self.assertEqual(sum(expected.values()),710)
        # Independently classify raw calendar hours, without builder assign_daypart.
        counts=defaultdict(int);hours=defaultdict(int)
        for r in self.old['metro_hourly']:
            if not r['service_date'].startswith('2025-09-') or r['interval_duration_minutes']!='60' or not r['entries'] or not r['exits']:continue
            h=int(r['hour']);date=dt.date.fromisoformat(r['service_date'])
            start=date-dt.timedelta(days=int(h<6))
            if start.month!=9 or (start==dt.date(2025,9,30) and h>=20):continue
            if start.weekday()>=5:binname='weekend_day' if 6<=h<18 else 'weekend_evening'
            else:binname='weekday_morning' if 6<=h<11 else 'weekday_lunch' if 11<=h<15 else 'weekday_evening' if 15<=h<20 else 'weekday_night'
            for direction in ['entries','exits']:
                key=(r['station_id'],binname,direction);counts[key]+=int(r[direction]);hours[key]+=1
        self.assertEqual(len(self.v['metro_daypart_rates']),156)
        for r in self.v['metro_daypart_rates']:
            key=(r['station_id'],r['time_bin'],r['direction'])
            self.assertEqual(int(r['observed_hours']),expected[r['time_bin']])
            self.assertEqual(int(r['observed_hours']),hours[key])
            self.assertEqual(int(r['observed_count']),counts[key])
            self.assertAlmostEqual(float(r['rate_per_observed_clock_hour']),counts[key]/hours[key])
            self.assertEqual(int(r['incomplete_starting_days']),int(r['time_bin']=='weekday_night'))

    def test_20_poi_support_counts_and_parsed_vs_recorded(self):
        availability={(r['poi_id'],r['time_bin']):r for r in self.old['poi_daypart_availability']}
        support={r['site_id']:r for r in self.v['daypart_site_support']}
        for site in self.master:
            used=[p for p in self.old['pois'] if p['category'] in ['office','shopping','leisure','school','hospital','transit'] and G.inv(float(site['longitude']),float(site['latitude']),float(p['longitude']),float(p['latitude']))[2]<=1500]
            recorded=sum(bool(p['opening_hours']) for p in used)
            parsed=sum(availability[p['poi_id'],'weekday_morning']['availability_status']=='DERIVED_FROM_RECORDED_OPENING_HOURS' for p in used)
            s=support[site['site_id']]
            self.assertEqual(int(s['poi_support_count']),len(used))
            self.assertEqual(int(s['opening_hours_recorded_count']),recorded)
            self.assertEqual(int(s['recorded_hours_support_count']),parsed)
            self.assertEqual(int(s['assumed_hours_support_count']),len(used)-parsed)
            self.assertEqual(int(s['opening_hours_unsupported_count']),recorded-parsed)
            self.assertEqual(int(s['opening_hours_missing_count']),len(used)-recorded)
            self.assertAlmostEqual(float(s['recorded_hours_support_fraction']),parsed/len(used))
            self.assertAlmostEqual(float(s['opening_hours_recorded_fraction']),recorded/len(used))
            self.assertEqual(s['coverage_status'],'PARTIAL_RECORDED_HOURS_ASSUMPTIONS_USED')

    def test_21_weekly_opportunity_formula_shares_and_no_transit_mixture(self):
        availability={(r['poi_id'],r['time_bin']):r for r in self.old['poi_daypart_availability']}
        weights={(r['category'],r['time_bin']):float(r['category_weight']) for r in self.old['daypart_weights']}
        profiles={(r['site_id'],r['time_bin']):r for r in self.v['daypart_opportunity_shares']}
        for site in self.enriched:
            near=[]
            for p in self.old['pois']:
                if (p['category'],'weekday_morning') not in weights:continue
                d=G.inv(float(site['longitude']),float(site['latitude']),float(p['longitude']),float(p['latitude']))[2]
                if d<=1500:near.append((p,d))
            raw={binname:sum(weights[p['category'],binname]*math.exp(-d/750)*float(availability[p['poi_id'],binname]['availability_fraction'])*float(availability[p['poi_id'],binname]['evidence_weight']) for p,d in near) for binname in b.BINS}
            exposures={binname:value*(b.BINS[binname][1]-b.BINS[binname][0])*b.BINS[binname][2] for binname,value in raw.items()}
            self.assertAlmostEqual(sum(float(site[k+'_weekly_exposure_share']) for k in b.BINS),1)
            for binname,value in exposures.items():
                p=profiles[site['site_id'],binname]
                self.assertAlmostEqual(float(p['raw_opportunity_index']),raw[binname])
                self.assertAlmostEqual(float(p['weekly_opportunity_exposure']),value)
                self.assertAlmostEqual(float(site[binname+'_weekly_exposure_share']),value/sum(exposures.values()))
                self.assertEqual(p['metro_counts_included'],'False')
                self.assertEqual(p['observed_service_period_complete'],'')
                self.assertIn('PROXY',p['period_basis'])

    def test_22_geographic_poi_and_station_joins(self):
        stations={r['station_id']:r for r in self.old['metro_station_lookup']}
        self.assertEqual(len(stations),13)
        self.assertEqual(len({r['poi_id'] for r in self.old['pois']}),len(self.old['pois']))
        for site in self.enriched:
            distances={sid:G.inv(float(site['longitude']),float(site['latitude']),float(p['longitude']),float(p['latitude']))[2] for sid,p in stations.items()}
            nearest=min(distances,key=distances.get)
            self.assertEqual(site['nearest_metro_station_id'],nearest)
            self.assertAlmostEqual(float(site['nearest_metro_distance_m']),distances[nearest])
            self.assertEqual(int(site['operational_metro_station_count_1500m']),sum(v<=1500 and stations[k]['operational_status']=='OPERATIONAL' for k,v in distances.items()))
            counts={tag:0 for tag in ['supermarket','convenience','grocery']}
            for p in self.old['pois']:
                if p['category']=='competitor' and G.inv(float(site['longitude']),float(site['latitude']),float(p['longitude']),float(p['latitude']))[2]<=1500:counts[p['shop']]+=1
            self.assertEqual(sum(counts.values()),int(site['competitor_count_1500m']))
            for tag,value in counts.items():self.assertEqual(int(site['mapped_'+tag+'_count_1500m']),value)
            self.assertTrue(12.7<float(site['latitude'])<13.2 and 77.3<float(site['longitude'])<77.9)

    def test_23_ward_geometries_left_join_and_nulls(self):
        look={r['site_id']:r for r in self.old['site_ward_lookup']}
        self.assertEqual(len(look),10)
        for field,filename,key in [('ward_2011_id','wards_historical_2012.geojson','ward_2011_id'),('ward_2025_id','wards_2025.geojson','id')]:
            features=b.load(b.FROZEN/filename)['features']
            for site in self.enriched:
                p=Point(float(site['longitude']),float(site['latitude']))
                matches=[str(f['properties'][key]) for f in features if shape(f['geometry']).covers(p)]
                self.assertLessEqual(len(matches),1)
                self.assertEqual(site[field],matches[0] if len(matches)==1 else '')
                self.assertEqual(site[field],look[site['site_id']][field])

    def test_24_site_joins_have_expected_cardinality_and_coverage(self):
        ids={r['site_id'] for r in self.master}
        for table in ['daypart_site_support','site_evidence_coverage','site_features_enriched']:
            self.assertEqual(len(self.v[table]),10)
            self.assertEqual({r['site_id'] for r in self.v[table]},ids)
        self.assertEqual(len(self.v['site_metro_daypart_rates']),120)
        keys={(r['site_id'],r['time_bin'],r['direction']) for r in self.v['site_metro_daypart_rates']}
        self.assertEqual(len(keys),120)
        master={r['site_id']:r for r in self.master}
        rates={(r['station_id'],r['time_bin'],r['direction']):r for r in self.v['metro_daypart_rates']}
        for r in self.v['site_metro_daypart_rates']:
            self.assertEqual(r['station_id'],master[r['site_id']]['nearest_metro_station_id'])
            self.assertEqual({k:v for k,v in r.items() if k!='site_id'},rates[r['station_id'],r['time_bin'],r['direction']])
        for r in self.enriched:
            self.assertEqual([int(r['metro_sep2025_'+d+'_'+f]) for d in ['weekday','weekend'] for f in ['observation_hours','observed_days']],[528,22,192,8])

    def test_25_actual_coverage_not_legacy_confidence(self):
        supports={r['site_id']:r for r in self.v['daypart_site_support']}
        self.assertEqual({r['source_quality_score'] for r in self.enriched},{'0.75'})
        fractions=set()
        for r in self.v['site_evidence_coverage']:
            s=supports[r['site_id']]
            self.assertEqual(r['daypart_poi_support_count'],s['poi_support_count'])
            self.assertEqual(r['parsed_hours_support_fraction'],s['recorded_hours_support_fraction'])
            fractions.add(r['parsed_hours_support_fraction'])
            self.assertEqual(int(r['metro_september_paired_intervals']),720)
            self.assertEqual(float(r['metro_clock_interval_coverage_fraction']),1)
            self.assertEqual((int(r['metro_eligible_daypart_bins']),int(r['metro_complete_daypart_bins']),int(r['metro_incomplete_daypart_bins'])),(104,103,1))
            self.assertAlmostEqual(float(r['metro_complete_daypart_bin_fraction']),103/104)
            self.assertEqual(r['household_denominator_available'],'False')
            self.assertEqual(r['validated_routing_available'],'False')
            self.assertEqual(r['evidence_interpretation'],'SUPPORT_COUNTS_AND_COVERAGE_NOT_CONFIDENCE')
        self.assertGreater(len(fractions),1)

    def test_26_no_sales_targets_predictions_training_or_ranks(self):
        forbidden=re.compile(r'(^|_)(sales|prediction|predicted|target|label|rank|revenue)(_|$)',re.I)
        for table,rows in self.v.items():
            self.assertFalse([field for field in rows[0] if forbidden.search(field) and field!='official_published_completion_target'],table)
        self.assertFalse(list(V2.rglob('*.pkl'))+list(V2.rglob('*.joblib'))+list(V2.rglob('*.pt'))+list(V2.rglob('*.onnx')))

    def test_27_distribution_restrictions_and_no_raw_metro_copy(self):
        m=b.load(V2/'distribution_manifest.json')
        self.assertFalse(m['public_package_created'])
        self.assertFalse(m['raw_metro_workbooks_copied'])
        self.assertTrue(m['inherited_metro_rights_apply_to_derived_records'])
        self.assertIn('cc-nc',m['unresolved_licensing'])
        self.assertIn('ODbL',m['unresolved_licensing'])
        self.assertIn('site_features_enriched.csv',m['not_cleared_for_public_distribution'])
        self.assertFalse(list(V2.rglob('*.xlsx'))+list(V2.rglob('*.xls'))+list(V2.rglob('*.zip')))


if __name__=='__main__':
    unittest.main(verbosity=2)
