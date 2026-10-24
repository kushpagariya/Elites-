"""Build StoreScout's evidence-labelled Bengaluru data package, offline.

No fitting, inference, financial engine, allocation, or ranking takes place.
Requires numpy, rasterio, shapely, pyproj, openpyxl and pypdf.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import html
import json
import math
import random
import re
import shutil
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import openpyxl
import rasterio
from rasterio.windows import from_bounds, Window
from pyproj import Geod, Transformer
from shapely.geometry import Point, Polygon, MultiPolygon, box, mapping, shape
from shapely.ops import transform, unary_union
from shapely import make_valid

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/bengaluru'
RAW,PROCESSED,FINAL,REPORTS=[DATA/n for n in ['raw','processed','final','reports']]
for p in [PROCESSED,FINAL,REPORTS]:p.mkdir(parents=True,exist_ok=True)
ASOF='2026-10-24'
SNAP='bengaluru-features-20261024-v1'
MANIFEST='bengaluru-sources-20261024-v1'
TZ='Asia/Kolkata'
BOUNDS=(77.600,12.815,77.725,12.940) # west, south, east, north
AOI=box(*BOUNDS)
GEOD=Geod(ellps='WGS84')
FWD=Transformer.from_crs(4326,32643,always_xy=True).transform
REV=Transformer.from_crs(32643,4326,always_xy=True).transform
BINS={'weekday_morning':(6,11,5),'weekday_lunch':(11,15,5),
      'weekday_evening':(15,20,5),'weekday_night':(20,30,5),
      'weekend_day':(6,18,2),'weekend_evening':(18,30,2)}
MASTER='site_id,feature_snapshot_id,snapshot_as_of_date,city,locality,latitude,longitude,store_format,source_manifest_id,store_size_sqm,population_1500m_est,population_10min_est,accessible_households_est,annual_wallet_inr,wallet_price_year,mean_wallet_weighted_distance_m,travel_time_method,competitor_count_1500m,competitor_attraction_index,nearest_competitor_distance_m,office_poi_count_1500m,education_poi_count_1500m,healthcare_poi_count_1500m,transit_poi_count_1500m,shopping_poi_count_1500m,food_leisure_poi_count_1500m,weekday_morning_raw,weekday_lunch_raw,weekday_evening_raw,weekday_night_raw,weekend_day_raw,weekend_evening_raw,nearest_metro_station_id,nearest_metro_distance_m,metro_weekday_entries_per_hour,metro_weekday_exits_per_hour,metro_weekend_entries_per_hour,metro_weekend_exits_per_hour,metro_measurement_start_date,metro_measurement_end_date,daypart_data_status,poi_data_status,population_data_status,ridership_data_status,comp_data_status,monthly_rent_inr,capex_inr,annual_opex_excl_rent_inr,gross_margin_fraction,source_quality_score'.split(',')
assert len(MASTER)==50
TABLES={}
LINEAGE=[]
GENERATED=[]
MISSING=[]
METRICS={}

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def json_out(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def csv_out(name,rows,columns=None,folder=FINAL):
    rows=list(rows)
    if columns is None:columns=list(rows[0]) if rows else []
    assert columns,name
    with (folder/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='raise')
        w.writeheader();w.writerows(rows)
    if folder==FINAL:TABLES[name]={'rows':len(rows),'columns':len(columns),'nulls':sum(r.get(c) is None or r.get(c)=='' for r in rows for c in columns)}
    return rows
def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def geo_out(name,features,folder=FINAL):json_out(folder/name,dict(type='FeatureCollection',features=features))
def feat(geom,props):return dict(type='Feature',geometry=mapping(geom),properties=props)
def distance(a,b):return GEOD.inv(a[0],a[1],b[0],b[1])[2]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def assumed(table,rid,field,value,unit,aid,lo=None,hi=None,reason='No verified site-level business record; explicitly permitted demo input.',status='ASSUMED',source='assumptions'):
    GENERATED.append(dict(table=table,record_id=rid,field_name=field,generated_value=value,unit=unit,
        source_status=status,assumption_id=aid,low=lo,base=value,high=hi,reason=reason,
        method_version='bengaluru-data-1; seed=20261024',source_id=source,benchmark_url=None,
        price_basis='2026-10-24 nominal INR' if 'INR' in unit else None))
    return value
def lineage(table,rid,field,origin,sources,formula,unit='unitless',period=None,assumptions=None,locator=None,limitations=None):
    LINEAGE.append(dict(table=table,record_id=rid,field_name=field,origin=origin,source_ids=sources,
        source_locator=locator,formula_or_method=formula,unit=unit,observation_reference_period=period,
        assumption_ids=assumptions,limitations=limitations))

def build_manifest():
    # Dates which are not verified are deliberately null.
    definitions=[
      ('osm-pois','OpenStreetMap contributors, Overpass POI extract','https://www.openstreetmap.org/copyright','ODbL-1.0','2026-10-24','2026-10-24',None,'Crowdsourced mapped features, not a verified business census; attribution and share-alike apply.'),
      ('osm-roads','OpenStreetMap contributors, roads and rail geometry','https://www.openstreetmap.org/copyright','ODbL-1.0','2026-10-24','2026-10-24',None,'Road access tags are retained; no ten-minute travel-time claim.'),
      ('worldpop-2020','WorldPop Global 2000-2020, UN-adjusted aggregated 1km population','https://hub.worldpop.org/Global1_2000-2020','CC-BY-4.0','2020-01-01','2020-12-31',None,'Modelled population estimates, not measured 2026 Census counts. Original 1km product release date unverified.'),
      ('metro-rti','BMRCL RTI workbooks via Vonter/bmrcl-ridership-hourly','https://github.com/Vonter/bmrcl-ridership-hourly','ODbL-1.0; BMRCL contents copyright; OpenCity cc-nc conflict','2025-08-01','2025-09-30',None,'GitHub asserts ODbL, OpenCity labels corresponding data non-commercial; do not assume commercial redistribution rights resolved.'),
      ('census-2011','Census of India 2011, OpenCity historical ward and housing tables','https://data.opencity.in/dataset/bengaluru-census-2011','Other (Public Domain), per OpenCity','2011-01-01','2011-12-31',None,'Housing and assets fields are percentages, not household counts. Do not convert directly into households.'),
      ('wards-2012','DataMeet 198 Bangalore wards, map vintage 2012','https://github.com/datameet/Municipal_Spatial_Data/tree/master/Bangalore','CC-BY-SA-2.5-IN','2012-01-01','2012-12-31',None,'Use geometry and ward codes only; embedded population differs from Census 2011 and is excluded.'),
      ('wards-2025','GBA final 369 wards, December 2025, OpenCity','https://data.opencity.in/dataset/gba-wards-delimitation-2025','Other (Public Domain), per OpenCity','2025-12-01','2025-12-31',None,'Administrative boundary vintage; embedded TOT_P year not independently verified and not used as current population.'),
      ('hces-2023-24','MoSPI NSS Report 592, HCES 2023-24','https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf','Government statistical publication; GSDD/NDSAP catalogue policy','2023-08-01','2024-07-31','2025-01-31','State/urban survey estimates in nominal survey-period INR; local transfer is an explicit assumption.'),
      ('yellow-official','Prime Minister Office / PIB Yellow Line inauguration','https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848','Government publication; attribution retained','2025-08-10','2025-08-10','2025-08-10','Inauguration date is verified; separate first commercial service date is not asserted.'),
      ('blue-official','Government of Karnataka Economic Survey 2025-26, section 5.10.2','https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf','Government report; attribution retained',None,None,None,'Reference publication 2025-26; exact status observation date unverified. Published completion programmes are not verified openings and may be superseded; OSM currently maps construction.'),
      ('commercial-attempt','Magicbricks public commercial listings acquisition attempt','https://www.magicbricks.com/commercial-property-for-rent-in-electronic-city-bangalore-pppfr','Proprietary page; not redistributed in final ZIP','2026-10-24','2026-10-24',None,'Asking listings include offices and distant promoted properties; no verified supermarket premises/lease or comparable benchmark obtained.'),
      ('approved-weights','Existing approved six-bin engineering weights','data/demo/weights.json','Repository fixture','2026-10-24','2026-10-24',None,'ASSUMED, not calibrated footfall. Values retained with duration handling documented.'),
      ('assumptions','StoreScout explicitly permitted assumptions and synthetic demo records','USER_SPECIFICATION','Local assumptions; original dataset components','2026-10-24','2026-10-24','2026-10-24','Never represent these records as real shops, financial actuals, or measured traffic.'),
      ('package-config','User-fixed Bengaluru dataset configuration and identifiers','USER_SPECIFICATION','Local metadata','2026-10-24','2026-10-24','2026-10-24','Analyst-selected rectangular AOI is not an official jurisdiction.'),
    ]
    rows=[]
    for sid,title,url,lic,start,end,release,note in definitions:
        rows.append(dict(source_id=sid,source_manifest_id=MANIFEST,title=title,source_url=url,licence=lic,
           observation_start_date=start,observation_end_date=end,release_date=release,retrieval_date=ASOF,
           timezone=TZ,geographic_scope='Bengaluru corridor' if sid.startswith('osm') else 'See source title and notes',
           source_status='ASSUMED' if sid in ['approved-weights','assumptions'] else 'METADATA' if sid=='package-config' else 'PUBLIC_SOURCE',notes=note))
    csv_out('source_manifest.csv',rows)
    logs=load(DATA/'acquisition_log.json')
    for r in logs:
        if r['path'].endswith(('hces_statement_4.xlsx','hces_catalogue.html','hces_portal.html')) and r['status']=='DOWNLOADED':
            r['status']='UNUSABLE_HTML_APP_SHELL';r['error']='HTTP 200 returned a 1198-byte JS application shell, not a data table.'
        r['path']=r['path'].replace('\\','/')
    json_out(DATA/'acquisition_log.json',logs)
    csv_out('acquisition_files.csv',logs,['url','path','status','bytes','sha256','retrieved_at_utc','content_type','last_modified','error'])
    return rows,logs

def build_sites():
    points=[('Central Silk Board',12.9188,77.6239),('Bommanahalli',12.9088,77.6268),
      ('Hongasandra',12.9024,77.6381),('Garvebhavi Palya',12.8994,77.6468),
      ('Kudlu Gate',12.8898,77.6419),('Singasandra',12.8808,77.6472),
      ('Hosa Road',12.8726,77.6578),('Beratena Agrahara',12.8642,77.6605),
      ('Electronic City Phase 1',12.8516,77.6607),('Konappana Agrahara',12.8455,77.6718)]
    rng=random.Random(20261024)
    rows=[]
    for i,(locality,lat,lon) in enumerate(points,1):
        sid=f'site-{i:02d}'
        area=rng.randrange(350,651,25)
        row=dict(site_id=sid,name=f'Hypothetical grocery candidate {i}',city='Bengaluru',locality=locality,
           latitude=lat,longitude=lon,store_format='supermarket',store_size_sqm=area,
           monthly_rent_inr=area*700,capex_inr=area*18000,annual_opex_excl_rent_inr=area*7200,
           gross_margin_fraction=0.22,source_status='SYNTHETIC_DEMO',source_id='assumptions',
           price_basis_date=ASOF,premises_availability_status='UNVERIFIED_HYPOTHETICAL',feature_snapshot_id=SNAP)
        ranges={'latitude':(None,None),'longitude':(None,None),'store_size_sqm':(350,650),
                'monthly_rent_inr':(area*450,area*1000),'capex_inr':(area*12000,area*25000),
                'annual_opex_excl_rent_inr':(area*5000,area*10000),'gross_margin_fraction':(0.18,0.27)}
        for f,(lo,hi) in ranges.items():
            assumed('candidate_sites',sid,f,row[f],'degrees' if f in ['latitude','longitude'] else 'sqm' if f=='store_size_sqm' else 'fraction' if f=='gross_margin_fraction' else 'INR/month' if f=='monthly_rent_inr' else 'INR/year excluding rent and COGS' if f.startswith('annual') else 'INR upfront',f'candidate-{f}',lo,hi,status='SYNTHETIC_DEMO')
        rows.append(row)
    csv_out('candidate_sites.csv',rows)
    coords=[(12.9140,77.6390),(12.8960,77.6320),(12.8770,77.6610),(12.8470,77.6550)]
    stores=[]
    for i,(lat,lon) in enumerate(coords,1):
        rid=f'store-{i:02d}'
        r=dict(store_id=rid,name=f'Fictional branch {i}',latitude=lat,longitude=lon,store_size_sqm=500,
               theta=0.2,variable_contribution_margin=0.18,source_status='SYNTHETIC_DEMO',source_id='assumptions',
               feature_snapshot_id=SNAP)
        for f in ['latitude','longitude','store_size_sqm','theta','variable_contribution_margin']:
            assumed('existing_stores',rid,f,r[f],'degrees' if f in ['latitude','longitude'] else 'sqm' if f=='store_size_sqm' else 'dimensionless',f'branch-{f}',status='SYNTHETIC_DEMO')
        stores.append(r)
    csv_out('existing_stores.csv',stores)
    geo_out('candidate_sites.geojson',[feat(Point(r['longitude'],r['latitude']),r) for r in rows])
    geo_out('existing_stores.geojson',[feat(Point(r['longitude'],r['latitude']),r) for r in stores])
    geo_out('boundary.geojson',[feat(AOI,dict(boundary_id='bengaluru-corridor-aoi-v1',source_id='package-config',
          source_status='ANALYST_SELECTED',crs='EPSG:4326',bbox_west=BOUNDS[0],bbox_south=BOUNDS[1],
          bbox_east=BOUNDS[2],bbox_north=BOUNDS[3],area_sqm=transform(FWD,AOI).area))])
    return rows,stores

def build_expenditure():
    text=(PROCESSED/'hces_2023_24_full_extracted.txt').read_text(encoding='utf-8')
    page=text.split('PDF_PAGE 90\n')[1].split('PDF_PAGE 91\n')[0]
    inputs=[]
    for line in page.splitlines():
        m=re.match(r'^(\d+)\.\s+(.+?)\s+([\d,]+\.\d+)\s*$',line)
        if not m:continue
        num=int(m[1]);value=float(m[3].replace(',',''))
        # Strip the other five state columns from the item description.
        label=re.split(r'\s+(?:[\d,]+\.\d+|-)\s',m[2])[0]
        inputs.append(dict(item_id=num,item_category=label,monthly_per_capita_inr=value,sector='urban',
            geographic_level='Karnataka state',reference_start_date='2023-08-01',reference_end_date='2024-07-31',
            price_year=2024,price_period='2023-24 nominal survey prices; unadjusted',imputation='without social-transfer imputation',
            source_id='hces-2023-24',source_status='OBSERVED_SURVEY_ESTIMATE',source_locator='NSS Report 592, PDF page 90, Statement 3U, column 14'))
    vals={r['item_id']:r['monthly_per_capita_inr'] for r in inputs}
    assert vals[32]==8075.62 and vals[15]==3041.91
    assert all(x in vals for x in range(1,20))
    # The processed-food category includes cooked meals. Half is an explicit
    # grocery eligibility assumption, not an observed split or capture rate.
    processed_share=assumed('project_assumptions','grocery-processed-share','value',0.5,'fraction','grocery-processed-share',0.25,0.75,
        reason='HCES beverages/processed-food category includes purchased cooked meals; no site-specific grocery split is observed.')
    grocery=sum(vals[i] for i in range(1,14))+processed_share*vals[14]+vals[18]+vals[19]
    assumed('project_assumptions','state-to-local-expenditure','value',1.0,'multiplier','state-to-local-expenditure',0.8,1.2,
        reason='No local expenditure survey: transfer Karnataka urban mean to modelled corridor residents without claiming local measurement.')
    csv_out('expenditure_inputs.csv',inputs)
    METRICS['grocery_monthly_per_capita_inr']=grocery
    return grocery

def build_population(grocery):
    srcpath=next((RAW/'population').glob('*.tif'))
    pixels=[]
    with rasterio.open(srcpath) as src:
        w=from_bounds(*BOUNDS,src.transform)
        c0,r0=math.floor(w.col_off),math.floor(w.row_off)
        win=Window(c0,r0,math.ceil(w.col_off+w.width)-c0,math.ceil(w.row_off+w.height)-r0)
        arr=src.read(1,window=win)
        trans=src.window_transform(win)
        profile=src.profile.copy();profile.update(width=arr.shape[1],height=arr.shape[0],transform=trans)
        with rasterio.open(PROCESSED/'worldpop_2020_corridor_window.tif','w',**profile) as dst:dst.write(arr,1)
        for r in range(arr.shape[0]):
            for c in range(arr.shape[1]):
                v=float(arr[r,c]);x,y=trans*(c,r);x1,y1=trans*(c+1,r+1)
                poly=box(x,y1,x1,y);cut=poly.intersection(AOI)
                if cut.is_empty:continue
                assert v!=src.nodata and v>=0
                whole=transform(FWD,poly);geom=transform(FWD,cut)
                pixels.append(dict(geometry=geom,population=v*geom.area/whole.area,density=v/whole.area))
        metadata=dict(source_id='worldpop-2020',source_file=srcpath.relative_to(ROOT).as_posix(),
          sha256=digest(srcpath),population_reference_year=2020,crs=str(src.crs),
          resolution_degrees=list(src.res),nominal_resolution='1km aggregated (30 arc seconds), not 100m',
          product='Global_2000_2020_1km_UNadj/2020/IND',release_date=None,licence='CC-BY-4.0',
          method='EPSG:32643 area-weighted pixel intersections, constant population density inside each source pixel',
          raster_overlap_fraction=1.0,source_pixel_count=len(pixels),no_2026_growth_applied=True)
    json_out(PROCESSED/'population_metadata.json',metadata)
    rows=[];geoms=[]
    west,south,east,north=BOUNDS
    grid=[box(west+(east-west)*c/10,south+(north-south)*r/10,
              west+(east-west)*(c+1)/10,south+(north-south)*(r+1)/10)
          for r in range(10) for c in range(10)]
    grid_metric=[transform(FWD,g) for g in grid]
    allocated=np.zeros(100,dtype=float)
    for pixel in pixels:
        overlaps=np.array([pixel['geometry'].intersection(g).area for g in grid_metric])
        # Normalize per source pixel to remove sub-metre projection edge
        # approximation gaps, conserving every clipped population count once.
        assert overlaps.sum()>0
        allocated+=pixel['population']*overlaps/overlaps.sum()
    for r in range(10):
        for c in range(10):
            poly=grid[r*10+c]
            geom=grid_metric[r*10+c]
            pop=float(allocated[r*10+c])
            rid=f'cell-{r*10+c+1:03d}';point=poly.centroid
            row=dict(cell_id=rid,latitude=point.y,longitude=point.x,population_est=round(pop,6),
                population_reference_year=2020,households_est=None,annual_wallet_inr=round(pop*grocery*12,2),
                wallet_price_year=2024,wallet_price_period='2023-24 nominal survey prices',
                monthly_grocery_per_capita_inr=grocery,area_sqm=geom.area,source_id='worldpop-2020;hces-2023-24;assumptions',
                source_status='DERIVED_WITH_ASSUMPTIONS',assumption_ids='grocery-processed-share;state-to-local-expenditure',
                feature_snapshot_id=SNAP,network_baseline_id='bengaluru-network-baseline-v1',
                spending_measure='ANNUAL_ADDRESSABLE_CATEGORY_EXPENDITURE_NOT_STORE_SALES')
            rows.append(row);geoms.append(feat(poly,{'cell_id':rid}))
    csv_out('spending_cells.csv',rows)
    geo_out('spending_cells.geojson',geoms)
    METRICS.update(population_total=sum(p['population'] for p in pixels),cell_population_total=sum(r['population_est'] for r in rows),
                   annual_network_wallet_inr=sum(r['annual_wallet_inr'] for r in rows),population_raster_pixels=len(pixels))
    return pixels,rows

def category(tags):
    if tags.get('shop') in ['supermarket','grocery','convenience']:return 'competitor'
    if tags.get('office'):return 'office'
    a=tags.get('amenity');s=tags.get('shop')
    if a in ['school','college','university','kindergarten']:return 'school'
    if a in ['hospital','clinic','doctors','pharmacy']:return 'hospital'
    if tags.get('railway') in ['station','halt','subway_entrance'] or tags.get('public_transport') in ['station','platform','stop_position'] or tags.get('highway')=='bus_stop' or a=='bus_station':return 'transit'
    if s in ['mall','department_store']:return 'shopping'
    if a in ['restaurant','cafe','fast_food','food_court','cinema','theatre'] or tags.get('leisure'):return 'leisure'
    return None

def build_pois():
    data=load(RAW/'osm_pois_alternative.json')
    rows=[];rejected=[];seen=set();named=[];duplicates=[]
    for el in sorted(data['elements'],key=lambda e:(0 if e['type']=='node' else 1,e['id'])):
        t=el.get('tags',{});cat=category(t)
        if cat is None:continue
        pos=el if 'lat' in el else el.get('center',{})
        if not pos:rejected.append({'osm_id':el['id'],'reason':'No point/centre'});continue
        lon,lat=pos['lon'],pos['lat'];pid=f'osm-{el["type"]}-{el["id"]}'
        if not AOI.covers(Point(lon,lat)):
            rejected.append({'osm_id':pid,'reason':'Element intersects AOI but centre is outside'});continue
        if pid in seen:duplicates.append({'duplicate_id':pid,'retained_id':pid,'reason':'Same OSM element'});continue
        seen.add(pid)
        name=t.get('name:en') or t.get('name')
        key=re.sub(r'[^a-z0-9]','',(name or '').lower())
        # Only collapse equal names of the same category within 40m; preserve
        # different named businesses and unnamed features.
        duplicate=next((p for p in named if key and key==p['key'] and cat==p['category'] and distance((lon,lat),p['xy'])<40),None)
        if duplicate:
            duplicates.append({'duplicate_id':pid,'retained_id':duplicate['id'],'reason':'Same normalized name/category within 40m, node preferred'})
            continue
        named.append({'key':key,'category':cat,'xy':(lon,lat),'id':pid})
        operational=t.get('railway') not in ['construction','proposed'] and not any(k in t for k in ['disused:shop','abandoned:shop'])
        rows.append(dict(poi_id=pid,osm_type=el['type'],osm_id=el['id'],name=name,category=cat,
            latitude=lat,longitude=lon,coordinate_method='OSM_NODE' if el['type']=='node' else 'OSM_BBOX_CENTRE',
            opening_hours=t.get('opening_hours'),shop=t.get('shop'),amenity=t.get('amenity'),
            operational_status='MAPPED_ACTIVE_UNVERIFIED' if operational else 'NOT_BASELINE',
            external_competitor=cat=='competitor',source_id='osm-pois',source_status='OBSERVED_OSM_RECORD',
            extracted_at_utc=data['osm3s']['timestamp_osm_base'],tags_json=json.dumps(t,ensure_ascii=False,sort_keys=True),
            feature_snapshot_id=SNAP))
    csv_out('pois.csv',rows)
    csv_out('poi_deduplication.csv',duplicates,['duplicate_id','retained_id','reason'])
    json_out(PROCESSED/'poi_exclusions.json',rejected)
    METRICS.update(osm_raw_elements=len(data['elements']),poi_rows=len(rows),poi_duplicates_removed=len(duplicates),poi_excluded_centres=len(rejected))
    # A map extract is not a complete census of premises. A mapped zero is
    # explicitly distinguished from a verified absence in site status fields.
    return rows

def build_stations_and_metro(pois):
    aliases={r['alt_name']:r['name'] for r in csv.DictReader((RAW/'metro/raw_station-names.csv').open(encoding='utf-8'),delimiter=';')}
    allrows={};stations={};nulls=0
    for filename,month in [('raw_august_station-hourly.xlsx','08'),('raw_september_station-hourly.xlsx','09')]:
        book=openpyxl.load_workbook(RAW/'metro'/filename,read_only=True,data_only=True)
        for sheet in book:
            direction='exits' if 'Exit' in sheet.title else 'entries'
            vals=sheet.values;header=next(vals)
            for excelrow,values in enumerate(vals,2):
                if not values[0] or not values[1]:continue
                rawdate,rawname=str(values[0])[:10],str(values[1])
                try:day=dt.date.fromisoformat(rawdate)
                except ValueError:continue
                code,name=rawname.split('-',1);name=aliases.get(name,name)
                sid='bmrcl-'+code
                if sid in stations:assert stations[sid]['station_name']==name
                stations[sid]=dict(station_id=sid,station_name=name,original_station_label=rawname,source_station_code=code)
                for idx,label in enumerate(header[2:-1],2):
                    hour=idx-2;key=(sid,rawdate,hour)
                    if key not in allrows:
                        start=dt.datetime.combine(day,dt.time(hour),dt.timezone(dt.timedelta(hours=5,minutes=30)))
                        variable=month=='08' and hour==23
                        allrows[key]=dict(station_id=sid,station_name=name,service_date=rawdate,hour=hour,
                          interval_start_local=start.isoformat(),interval_end_local=None if variable else (start+dt.timedelta(hours=1)).isoformat(),
                          interval_duration_minutes=None if variable else 60,original_interval_label=label,
                          interval_status='VARIABLE_END_LAST_TRAIN' if variable else 'REPORTED_HOUR',entries=None,exits=None,
                          observation_status=None,source_id='metro-rti',source_locator=f'{filename};{sheet.title};row {excelrow}',
                          entries_source_locator=None,exits_source_locator=None,timezone=TZ)
                    row=allrows[key]
                    row[direction+'_source_locator']=f'{filename};{sheet.title};row {excelrow};column {idx+1}'
                    value=values[idx]
                    if value is not None:
                        assert isinstance(value,(float,int)) and value>=0
                        assert row[direction] is None,'Duplicate direction record'
                        row[direction]=int(value)
                    else:nulls+=1
        book.close()
    full=[]
    for key,row in sorted(allrows.items()):
        row['observation_status']='OBSERVED_ENTRIES_AND_EXITS' if row['entries'] is not None and row['exits'] is not None else 'PARTIAL_ENTRIES_ONLY' if row['entries'] is not None else 'MISSING_RAW_VALUES'
        full.append(row)
    csv_out('metro_all_stations_hourly.csv',full,folder=PROCESSED)
    # Match by exact normalized source names. No fuzzy geocoding is accepted.
    def norm(v):return re.sub(r'[^a-z0-9]','',v.lower())
    metro_pois=[p for p in pois if json.loads(p['tags_json']).get('station')=='subway' and json.loads(p['tags_json']).get('railway')=='station']
    lookup=[]
    for p in metro_pois:
        matches=[s for s in stations.values() if norm(s['station_name'])==norm(p['name'])]
        assert len(matches)==1,(p['name'],matches)
        r=dict(matches[0],latitude=p['latitude'],longitude=p['longitude'],osm_poi_id=p['poi_id'],
          osm_station_code=json.loads(p['tags_json']).get('code'),line='Yellow',operational_status='OPERATIONAL',
          status_source_id='yellow-official;metro-rti',mapping_status='EXACT_NAME_MATCH',
          source_id='metro-rti;osm-pois',source_status='DERIVED_SOURCE_CROSSWALK')
        lookup.append(r)
    csv_out('metro_station_lookup.csv',lookup)
    selected={r['station_id'] for r in lookup}
    hourly=[r for r in full if r['station_id'] in selected]
    csv_out('metro_hourly.csv',hourly)
    averages=[];coverage=[]
    for s in lookup:
        rid=s['station_id'];records=[r for r in hourly if r['station_id']==rid]
        valid=[r for r in records if r['service_date'].startswith('2025-09') and r['interval_duration_minutes']==60 and r['entries'] is not None and r['exits'] is not None]
        for kind in ['weekday','weekend']:
            subset=[r for r in valid if (dt.date.fromisoformat(r['service_date']).weekday()<5)==(kind=='weekday')]
            averages.append(dict(station_id=rid,day_type=kind,entries_per_observed_clock_hour=statistics.mean(r['entries'] for r in subset) if subset else None,
              exits_per_observed_clock_hour=statistics.mean(r['exits'] for r in subset) if subset else None,
              observation_hours=len(subset),observed_days=len({r['service_date'] for r in subset}),
              measurement_start_date=min(r['service_date'] for r in subset) if subset else None,
              measurement_end_date=max(r['service_date'] for r in subset) if subset else None,
              source_id='metro-rti',source_status='HISTORICAL_PROXY',averaging_method='September paired complete 60-minute clock intervals, including observed night zeros; no 2026 projection'))
        dates={r['service_date'] for r in records}
        for day in (dt.date(2025,8,1)+dt.timedelta(days=i) for i in range(61)):
            rr=[r for r in records if r['service_date']==day.isoformat()]
            coverage.append(dict(station_id=rid,service_date=day.isoformat(),reported_intervals=len(rr),
                observed_entry_intervals=sum(r['entries'] is not None for r in rr),observed_exit_intervals=sum(r['exits'] is not None for r in rr),
                coverage_status='OBSERVED' if rr else 'NOT_REPORTED_NOT_ZERO',source_id='metro-rti'))
    csv_out('metro_activity_averages.csv',averages)
    csv_out('metro_date_coverage.csv',coverage)
    METRICS.update(metro_corridor_stations=len(lookup),metro_all_network_stations=len(stations),metro_raw_null_values_preserved=nulls,
      metro_all_network_hourly_rows=len(full),metro_corridor_hourly_rows=len(hourly),metro_duplicates_removed=0,
      august_exits='MUST_REMAIN_UNKNOWN: processed destination counts do not establish exit-clock observations')
    return lookup,hourly,averages

def assign_daypart(day,hour):
    # Early morning belongs to the previous starting day, including across
    # Friday/Saturday and Sunday/Monday boundaries.
    startday=day-dt.timedelta(days=1) if hour<6 else day
    adjusted=hour+24 if hour<6 else hour
    if startday.weekday()>=5:return startday,'weekend_day' if adjusted<18 else 'weekend_evening'
    return startday,'weekday_morning' if adjusted<11 else 'weekday_lunch' if adjusted<15 else 'weekday_evening' if adjusted<20 else 'weekday_night'

DAYNUM={'Mo':0,'Tu':1,'We':2,'Th':3,'Fr':4,'Sa':5,'Su':6}
def opening_schedule(text):
    """Conservative subset parser. Unknown syntax stays an availability assumption."""
    if not text:return None
    if text=='24/7':return np.ones(7*24*60,dtype=bool)
    a=np.zeros(7*24*60,dtype=bool)
    for part in text.split(';'):
        m=re.fullmatch(r'\s*(?:(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?\s+)?((?:\d{2}:\d{2}-\d{2}:\d{2})(?:,\d{2}:\d{2}-\d{2}:\d{2})*|off)\s*',part)
        if not m:return None
        days=list(range(7)) if not m[1] else [DAYNUM[m[1]]]
        if m[2]:
            days=[];d=DAYNUM[m[1]]
            while True:
                days.append(d)
                if d==DAYNUM[m[2]]:break
                d=(d+1)%7
        if m[3]=='off':continue
        for interval in m[3].split(','):
            start,end=interval.split('-')
            sh,sm=map(int,start.split(':'));eh,em=map(int,end.split(':'))
            if sh>23 or eh>24 or sm>59 or em>59 or (eh==24 and em):return None
            s=60*sh+sm;e=60*eh+em
            if e<=s:e+=1440
            for day in days:a[(np.arange(day*1440+s,day*1440+e)%(7*1440)).astype(int)]=True
    return a

def build_dayparts(sites,pois,hourly):
    weights=load(ROOT/'data/demo/weights.json')['category_weights']
    wrows=[]
    for cat,w in weights.items():
        for timebin,value in w.items():
            start,end,days=BINS[timebin]
            wrows.append(dict(weight_id=f'{cat}-{timebin}',category=cat,time_bin=timebin,category_weight=value,
              local_start_hour=start,local_end_hour=end%24,duration_hours=end-start,starting_days_per_week=days,
              decay_scale_m=750,catchment_radius_m=1500,source_id='approved-weights',source_status='ASSUMED',
              weight_version='weights-demo-1',index_unit='relative opportunity per nominal hour'))
            assumed('daypart_weights',f'{cat}-{timebin}','category_weight',value,'relative weight','approved-category-weights',source='approved-weights',reason='Approved fixture weights; no calibration to measured store visits.')
    csv_out('daypart_weights.csv',wrows)
    availability={};arows=[]
    for p in pois:
        if p['category'] not in weights:continue
        schedule=opening_schedule(p['opening_hours'])
        availability[p['poi_id']]={}
        for timebin,(start,end,days) in BINS.items():
            daynums=range(5) if days==5 else range(5,7)
            indices=np.concatenate([np.arange(d*1440+start*60,d*1440+end*60)%(7*1440) for d in daynums])
            value=float(schedule[indices].mean()) if schedule is not None else 0.5
            evidence=1.0 if schedule is not None else 0.5
            availability[p['poi_id']][timebin]=(value,evidence)
            rid=p['poi_id']+'|'+timebin
            arows.append(dict(poi_id=p['poi_id'],time_bin=timebin,availability_fraction=value,evidence_weight=evidence,
              availability_status='DERIVED_FROM_RECORDED_OPENING_HOURS' if schedule is not None else 'ASSUMED_UNKNOWN_OR_UNSUPPORTED_HOURS',
              opening_hours_original=p['opening_hours'],source_id='osm-pois;assumptions' if schedule is None else 'osm-pois',
              assumption_id='unknown-hours-availability' if schedule is None else 'recorded-hours-evidence'))
            if schedule is None:assumed('poi_daypart_availability',rid,'availability_fraction',value,'fraction','unknown-hours-availability',0,1,reason='OSM opening hours absent or syntax unsupported; explicit conservative scenario availability.')
            assumed('poi_daypart_availability',rid,'evidence_weight',evidence,'fraction','unknown-hours-evidence' if schedule is None else 'recorded-hours-evidence',0,1,reason='Engineering evidence weighting; not calibrated probability or measured accuracy.')
    csv_out('poi_daypart_availability.csv',arows)
    rows=[];site_raw={}
    for site in sites:
        sid=site['site_id'];values={};details={}
        nearby=[]
        for p in pois:
            if p['category'] not in weights:continue
            d=distance((site['longitude'],site['latitude']),(p['longitude'],p['latitude']))
            if d<=1500:nearby.append((p,d))
        for b,(start,end,days) in BINS.items():
            values[b]=sum(weights[p['category']][b]*math.exp(-d/750)*availability[p['poi_id']][b][0]*availability[p['poi_id']][b][1] for p,d in nearby)
            details[b]=sum(availability[p['poi_id']][b][1]==1 for p,d in nearby)
        weekly=sum(values[b]*(BINS[b][1]-BINS[b][0])*BINS[b][2] for b in BINS)
        for b,(start,end,days) in BINS.items():
            exposure=values[b]*(end-start)*days
            rows.append(dict(site_id=sid,time_bin=b,raw_opportunity_index=values[b],duration_hours=end-start,
                starting_days_per_week=days,weekly_opportunity_exposure=exposure,weekly_exposure_share=exposure/weekly if weekly else None,
                poi_support_count=len(nearby),recorded_hours_support_count=details[b],assumed_hours_support_count=len(nearby)-details[b],
                source_id='osm-pois;approved-weights;assumptions',source_status='DERIVED_OPPORTUNITY_PROXY_WITH_ASSUMPTIONS',
                feature_snapshot_id=SNAP,metro_counts_included=False,timezone=TZ))
        site_raw[sid]=values
    csv_out('daypart_profiles.csv',rows)
    grouped=defaultdict(list)
    for r in hourly:
        if r['interval_duration_minutes']!=60:continue
        day,b=assign_daypart(dt.date.fromisoformat(r['service_date']),r['hour'])
        grouped[(r['station_id'],day.isoformat(),b)].append(r)
    mr=[]
    for (station,day,b),records in sorted(grouped.items()):
        expected=BINS[b][1]-BINS[b][0]
        for direction in ['entries','exits']:
            vals=[r[direction] for r in records if r[direction] is not None]
            mr.append(dict(station_id=station,starting_local_date=day,time_bin=b,direction=direction,
                observed_count=sum(vals) if vals else None,observed_hours=len(vals),expected_bin_hours=expected,
                count_per_observed_hour=sum(vals)/len(vals) if vals else None,
                bin_coverage_status='COMPLETE' if len(vals)==expected else 'PARTIAL_OR_UNREPORTED',
                source_id='metro-rti',timezone=TZ))
    csv_out('metro_daypart_coverage.csv',mr)
    METRICS['daypart_opening_hours_parsed_pois']=len({r['poi_id'] for r in arows if r['availability_status'].startswith('DERIVED')})
    return site_raw

def build_geography(sites):
    n={'k':'http://www.opengis.net/kml/2.2'}
    root=ET.parse(RAW/'wards/9013d656-8051-4e2d-9648-46efd0d86d3d.kml').getroot()
    wards=[];repairs=0
    for pm in root.findall('.//k:Placemark',n):
        props={el.get('name'):el.text for el in pm.findall('.//k:SimpleData',n)}
        polygons=[]
        for pe in pm.findall('.//k:Polygon',n):
            outer=pe.find('.//k:outerBoundaryIs/k:LinearRing/k:coordinates',n)
            if outer is None:continue
            coords=lambda el:[tuple(map(float,x.split(',')[:2])) for x in el.text.strip().split()]
            holes=[coords(e) for e in pe.findall('.//k:innerBoundaryIs/k:LinearRing/k:coordinates',n)]
            polygons.append(Polygon(coords(outer),holes))
        if not polygons:continue
        g=unary_union(polygons)
        if not g.is_valid:g=make_valid(g);repairs+=1
        if not g.intersects(AOI):continue
        props={k:props.get(k) for k in ['id','Corporation','corporation_id','ward_id','ward_name']}
        props.update(source_id='wards-2025',boundary_vintage='2025-12',population_used=False)
        wards.append((g,props))
    geo_out('wards_2025.geojson',[feat(g,p) for g,p in wards])
    census=read_csv(RAW/'census/269cdf01-dae5-4736-8f4d-72a8e57fa3a9.csv')
    for r in census:r.update(source_id='census-2011',population_reference_year=2011,source_status='OBSERVED_HISTORICAL')
    csv_out('census_2011_wards.csv',census)
    census_by={int(r['Ward Num']):r for r in census}
    old=load(RAW/'wards/BBMP_2012_198.geojson')['features']
    olds=[]
    for f in old:
        g=shape(f['geometry'])
        if not g.is_valid:g=make_valid(g);repairs+=1
        if g.intersects(AOI):
            num=int(f['properties']['WARD_NO']);observed=census_by.get(num)
            assert observed is not None
            # Geometry source's embedded POP_TOTAL values are explicitly discarded.
            props=dict(ward_2011_id=num,ward_name=census_by[num]['Ward Name'],source_id='wards-2012;census-2011',
                       geometry_vintage=2012,population_reference_year=2011,census_population=int(observed['Population']))
            olds.append((g,props))
    geo_out('wards_historical_2012.geojson',[feat(g,p) for g,p in olds])
    cross=[]
    for new,np_ in wards:
        for old,op in olds:
            overlap=new.intersection(old).intersection(AOI)
            if overlap.is_empty or transform(FWD,overlap).area<1:continue
            area=transform(FWD,overlap).area
            cross.append(dict(ward_2025_id=np_['id'],corporation=np_['Corporation'],ward_2025_name=np_['ward_name'],
               ward_2011_id=op['ward_2011_id'],ward_2011_name=op['ward_name'],overlap_in_aoi_sqm=area,
               fraction_of_old_ward_area=area/transform(FWD,old).area,
               fraction_of_new_ward_aoi_area=area/transform(FWD,new.intersection(AOI)).area,
               crosswalk_method='EPSG:32643 polygon area intersection, clipped to AOI; geometry-only, no population allocation',
               population_reference_year=2011,old_geometry_vintage=2012,new_geometry_vintage=2025,
               source_id='wards-2012;wards-2025;census-2011'))
    csv_out('ward_crosswalk.csv',cross)
    joins=[]
    for s in sites:
        p=Point(s['longitude'],s['latitude'])
        new=[r for g,r in wards if g.covers(p)];old=[r for g,r in olds if g.covers(p)]
        joins.append(dict(site_id=s['site_id'],ward_2025_id=new[0]['id'] if len(new)==1 else None,
           ward_2025_name=new[0]['ward_name'] if len(new)==1 else None,ward_2011_id=old[0]['ward_2011_id'] if len(old)==1 else None,
           ward_2011_name=old[0]['ward_name'] if len(old)==1 else None,
           spatial_join_status='MATCHED_BOTH' if len(new)==len(old)==1 else 'OUTSIDE_OR_AMBIGUOUS_WARD_COVERAGE',
           source_id='wards-2012;wards-2025',demographic_use='Historical context only; no ward totals copied into catchments'))
    csv_out('site_ward_lookup.csv',joins)
    METRICS.update(ward_geometry_repairs=repairs,historical_aoi_wards=len(olds),new_aoi_wards=len(wards))

def build_infrastructure(stations):
    roads=load(RAW/'osm_roads.json')['elements']
    geoms=[]
    for e in roads:
        coords=[(p['lon'],p['lat']) for p in e.get('geometry',[]) if p]
        if len(coords)<2:continue
        from shapely.geometry import LineString
        tags=e.get('tags',{})
        geoms.append(feat(LineString(coords),dict(osm_id=e['id'],source_id='osm-roads',tags_json=json.dumps(tags,ensure_ascii=False))))
    geo_out('transport_connections.geojson',geoms)
    blue=[g for g in geoms if 'Phase 2A' in json.loads(g['properties']['tags_json']).get('name','')]
    yellow=[feat(Point(s['longitude'],s['latitude']),{'infra_project_id':'metro-yellow','station_id':s['station_id'],'source_id':'osm-pois'}) for s in stations]
    for g in blue:g['properties']['infra_project_id']='metro-blue-2a'
    geo_out('infrastructure_geometry.geojson',yellow+blue)
    rows=[dict(infra_project_id='metro-yellow',name='Bengaluru Metro Yellow Line RV Road to Bommasandra',
      status='OPERATIONAL',status_reference_date=ASOF,status_verification_date=ASOF,verified_opening_date=None,
      verified_inauguration_date='2025-08-10',official_published_completion_target=None,
      source_id='yellow-official;metro-rti;osm-pois',official_source_url='https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848',
      geometry_reference='infrastructure_geometry.geojson: metro-yellow station points',geometry_status='OSM_STATION_LOCATIONS',
      included_current_baseline=True,hypothetical_open_date=None,delayed_open_date=None,delay_months=24,
      assumed_demand_effect_fraction=0.0,source_status='VERIFIED_OPERATIONAL_WITH_SEPARATE_OSM_GEOMETRY'),
      dict(infra_project_id='metro-blue-2a',name='Bengaluru Metro Phase 2A Central Silk Board to KR Puram',
      status='UNDER_CONSTRUCTION',status_reference_date=ASOF,status_verification_date=ASOF,verified_opening_date=None,
      verified_inauguration_date=None,official_published_completion_target='2026-12 (historic programme, not an opening commitment)',
      source_id='blue-official;osm-roads;assumptions',official_source_url=next(r['source_url'] for r in read_csv(FINAL/'source_manifest.csv') if r['source_id']=='blue-official'),
      geometry_reference='infrastructure_geometry.geojson: metro-blue-2a OSM way segments',geometry_status='OSM_PARTIAL_LINE_SEGMENTS_NOT_OFFICIAL_ALIGNMENT',
      included_current_baseline=False,hypothetical_open_date='2027-07-01',delayed_open_date='2029-07-01',delay_months=24,
      assumed_demand_effect_fraction=0.10,source_status='OFFICIAL_PROJECT_WITH_ASSUMED_SCENARIO_DATE_AND_EFFECT')]
    for field,unit,lo,hi in [('hypothetical_open_date','date',None,None),('delayed_open_date','date',None,None),('assumed_demand_effect_fraction','fraction',-0.1,0.2)]:
        assumed('infrastructure','metro-blue-2a',field,rows[1][field],unit,'blue-scenario-'+field,lo,hi,
           reason='No verified commercial opening date or measured retail impact; explicit scenario input only.')
    csv_out('infrastructure.csv',rows)
    scenarios=[dict(scenario_id=s,infrastructure_state=s,feature_snapshot_id=SNAP,
       blue_line_active=False if s=='current' else None,blue_scenario_open_date=None if s=='current' else '2027-07-01' if s=='opens' else '2029-07-01',
       delay_months=24,scenario_source_status='ASSUMED',baseline_contains_operational_yellow=True,
       future_geometry_in_baseline_features=False,source_id='assumptions;yellow-official;blue-official') for s in ['current','opens','delayed']]
    csv_out('infrastructure_scenarios.csv',scenarios)
    METRICS['transport_line_records']=len(geoms);METRICS['blue_osm_segments']=len(blue)

def build_assumptions(grocery):
    values=[('catchment_radius_m',1500,'m','User-specified feature catchment'),('distance_decay_scale_m',750,'m','User-specified opportunity decay'),
      ('delay_months',24,'months','User-specified scenario delay'),('outside_attraction',1.0,'relative attraction','Approved future network default, no allocation performed'),
      ('attraction_gamma',1.0,'dimensionless','Approved future network default'),('attraction_tau_m',750,'m','Approved future network default'),
      ('grocery_monthly_per_capita_inr',grocery,'INR/person/month','HCES 1-13 + 0.5*14 +18+19; state urban mean transferred locally'),
      ('population_reference_year',2020,'year','WorldPop estimate reference year; no population growth applied'),
      ('wallet_price_year',2024,'year','2023-24 survey nominal prices represented by ending year'),
      ('valuation_date',ASOF,'date','User fixed valuation date'),('financial_price_basis',ASOF,'date','Demo rent, CAPEX and OPEX price basis'),
      ('grocery_processed_share',0.5,'fraction','Assumed grocery-eligible share of HCES beverages/processed foods including purchased meals'),
      ('state_to_local_expenditure_multiplier',1.0,'multiplier','Assumed transfer of state urban mean to corridor, not a measured local estimate'),
      ('unknown_hours_availability',0.5,'fraction','Assumed where opening hours unavailable or parser unsupported'),
      ('unknown_hours_evidence',0.5,'fraction','Assumed evidence weight, not confidence'),('recorded_hours_evidence',1.0,'fraction','Engineering reference weight for parsed OSM schedule'),
      ('competitor_unit_attraction',1.0,'relative attraction','Equal competitor mass; actual sizes/turnover unavailable'),
      ('monthly_rent_rate',700,'INR/sqm/month','Demo engineering assumption; listings not comparable verified grocery leases'),
      ('capex_rate',18000,'INR/sqm upfront','Demo engineering assumption, no benchmark claimed'),
      ('opex_rate',7200,'INR/sqm/year excluding rent and COGS','Demo engineering assumption'),
      ('gross_margin_fraction',0.22,'fraction','Demo grocery assumption, not observed business margin'),
      ('budget_inr',20000000,'INR','Existing approved project assumption'),('discount_rate_fraction',0.12,'fraction','Existing approved project assumption'),
      ('projection_years',5,'years','Existing approved project assumption')]
    rows=[]
    for key,value,unit,note in values:
        status='DERIVED_WITH_ASSUMPTIONS' if key=='grocery_monthly_per_capita_inr' else 'EXISTING_FIXTURE_ASSUMED' if key in ['budget_inr','discount_rate_fraction','projection_years'] else 'REFERENCE_METADATA' if key in ['population_reference_year','wallet_price_year','valuation_date','financial_price_basis'] else 'ASSUMED'
        source='hces-2023-24;assumptions' if key=='grocery_monthly_per_capita_inr' else 'approved-weights' if key in ['catchment_radius_m','distance_decay_scale_m'] else 'assumptions'
        rows.append(dict(assumption_id=key,value=value,unit=unit,source_status=status,source_id=source,notes=note,feature_snapshot_id=SNAP))
        if status=='ASSUMED' and not any(r['table']=='project_assumptions' and r['record_id']==key for r in GENERATED):
            assumed('project_assumptions',key,'value',value,unit,key,reason=note)
    csv_out('project_assumptions.csv',rows)

def build_master(sites,pixels,pois,stations,averages,raws,grocery):
    rows=[];avg={(r['station_id'],r['day_type']):r for r in averages}
    for s in sites:
        sid=s['site_id'];xy=(s['longitude'],s['latitude']);catch=Point(*FWD(*xy)).buffer(1500,quad_segs=96)
        population=0;weighted=0
        for p in pixels:
            inter=p['geometry'].intersection(catch)
            if inter.is_empty:continue
            count=p['density']*inter.area;population+=count
            point=transform(REV,inter.centroid)
            weighted+=count*distance(xy,(point.x,point.y))
        distances=[(p,distance(xy,(p['longitude'],p['latitude']))) for p in pois]
        local=[(p,d) for p,d in distances if d<=1500]
        comp=[(p,d) for p,d in local if p['category']=='competitor']
        counts=Counter(p['category'] for p,d in local)
        nearest=min(stations,key=lambda r:distance(xy,(r['longitude'],r['latitude'])))
        weekday=avg[nearest['station_id'],'weekday'];weekend=avg[nearest['station_id'],'weekend']
        row=dict(site_id=sid,feature_snapshot_id=SNAP,snapshot_as_of_date=ASOF,city='Bengaluru',locality=s['locality'],
          latitude=s['latitude'],longitude=s['longitude'],store_format='supermarket',source_manifest_id=MANIFEST,
          store_size_sqm=s['store_size_sqm'],population_1500m_est=round(population,4),population_10min_est=None,
          accessible_households_est=None,annual_wallet_inr=round(population*grocery*12,2),wallet_price_year=2024,
          mean_wallet_weighted_distance_m=weighted/population if population else None,
          travel_time_method='UNAVAILABLE_NO_VALIDATED_ROUTING; population_1500m uses metric circle',
          competitor_count_1500m=len(comp),competitor_attraction_index=sum(math.exp(-d/750) for p,d in comp),
          nearest_competitor_distance_m=min((d for p,d in comp),default=None),office_poi_count_1500m=counts['office'],
          education_poi_count_1500m=counts['school'],healthcare_poi_count_1500m=counts['hospital'],
          transit_poi_count_1500m=counts['transit'],shopping_poi_count_1500m=counts['shopping'],
          food_leisure_poi_count_1500m=counts['leisure'],**{b+'_raw':raws[sid][b] for b in BINS},
          nearest_metro_station_id=nearest['station_id'],nearest_metro_distance_m=distance(xy,(nearest['longitude'],nearest['latitude'])),
          metro_weekday_entries_per_hour=weekday['entries_per_observed_clock_hour'],metro_weekday_exits_per_hour=weekday['exits_per_observed_clock_hour'],
          metro_weekend_entries_per_hour=weekend['entries_per_observed_clock_hour'],metro_weekend_exits_per_hour=weekend['exits_per_observed_clock_hour'],
          metro_measurement_start_date='2025-09-01',metro_measurement_end_date='2025-09-30',
          daypart_data_status='DERIVED_ASSUMED_OPPORTUNITY_PROXY',poi_data_status='OSM_PARTIAL_COVERAGE_MAPPED_COUNTS',
          population_data_status='HISTORICAL_MODELLED_PROXY_2020',ridership_data_status='HISTORICAL_PROXY_2025_09',
          comp_data_status='OSM_PARTIAL;MAPPED_ZERO_NOT_VERIFIED_ABSENCE;EQUAL_ATTRACTION_ASSUMED',
          monthly_rent_inr=s['monthly_rent_inr'],capex_inr=s['capex_inr'],annual_opex_excl_rent_inr=s['annual_opex_excl_rent_inr'],
          gross_margin_fraction=s['gross_margin_fraction'],source_quality_score=6/8)
        assert set(row)==set(MASTER)
        rows.append(row)
        for field,value in row.items():
            source='package-config';origin='DERIVED';method='User-specified identity/configuration or deterministic status metadata';period=ASOF;aid=None;unit='text'
            if field in ['latitude','longitude','store_size_sqm','monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr','gross_margin_fraction','locality']:
                source='assumptions';origin='SYNTHETIC_ASSUMED';method='Hypothetical candidate; deterministic seed and bounded area-scaled financial inputs';aid='candidate-'+field
            elif field in ['population_1500m_est','mean_wallet_weighted_distance_m']:
                source='worldpop-2020';method='EPSG:32643 area-weighted 1500m circle intersection with source raster pixels; weighted distance uses intersection centroids';period='2020'
            elif field=='annual_wallet_inr':
                source='worldpop-2020;hces-2023-24;assumptions';method='population_1500m_est(unrounded) * monthly_category_expenditure * 12';period='population 2020; spending 2023-08 to 2024-07';aid='grocery-processed-share;state-to-local-expenditure'
            elif field=='wallet_price_year':source='hces-2023-24';method='Ending year of nominal survey period; no inflation adjustment';period='2023-24'
            elif field.endswith('_raw'):
                source='osm-pois;approved-weights;assumptions';method='sum(category_weight * exp(-distance_m/750) * availability_fraction * evidence_weight), 1500m radius, index per nominal hour';aid='approved-category-weights;unknown-hours-availability;unknown-hours-evidence;recorded-hours-evidence'
            elif field.startswith('competitor') or field=='nearest_competitor_distance_m':
                source='osm-pois;assumptions' if field=='competitor_attraction_index' else 'osm-pois';method='Mapped grocery/convenience/supermarket external POIs within 1500m; attraction=sum(exp(-d/750)), equal mass=1; nearest within catchment';aid='competitor_unit_attraction' if field=='competitor_attraction_index' else None
            elif '_poi_count_' in field:source='osm-pois';method='Count deduplicated mapped category POIs within geodesic 1500m; not a complete census'
            elif field in ['nearest_metro_station_id','nearest_metro_distance_m']:
                source='osm-pois;yellow-official;metro-rti';method='Minimum WGS84 ellipsoidal distance to matched operational Yellow Line station'
            elif field.startswith('metro_'):
                source='metro-rti';method='September 2025 paired observed 60-minute clock intervals, weekday/weekend stratification; night zeros retained';period='2025-09-01/2025-09-30'
            elif field=='source_quality_score':method='6/8 public evidence-family availability: population, spending, competition, POIs, station geography, ridership available; household denominator and validated routing unavailable. Not accuracy or model confidence.'
            if value is None:origin='UNRESOLVED_MISSING';source='package-config';method='No defensible source-supported computation; see missing_fields.csv'
            if field.endswith('_inr'):unit='INR/month' if field=='monthly_rent_inr' else 'INR upfront' if field=='capex_inr' else 'INR/year'
            elif field.endswith('_m'):unit='metres'
            elif field.endswith('_sqm'):unit='sqm'
            elif field.startswith('population'):unit='persons'
            elif field in ['latitude','longitude']:unit='decimal degrees EPSG:4326'
            elif field.endswith('_fraction') or field=='source_quality_score':unit='fraction'
            elif field.endswith('_per_hour'):unit='passengers/observed clock hour'
            lineage('site_features',sid,field,origin,source,method,unit,period,aid,limitations='Snapshot combines source years; see temporal_alignment_report.md')
        for field in ['population_10min_est','accessible_households_est']:
            MISSING.append(dict(table='site_features',record_id=sid,field_name=field,classification='MUST_REMAIN_UNKNOWN',
              resolution='NULL',reason='No validated travel-time routing' if field=='population_10min_est' else 'No defensible local persons-per-household denominator; housing source contains percentages, not household counts',source_attempts='osm-roads' if field=='population_10min_est' else 'census-2011;hces-2023-24',assumption_id=None))
    csv_out('site_features.csv',rows,MASTER)
    return rows

def schema_mapping():
    rows=[]
    for field in MASTER:
        target='project.inputs.feature_snapshot.'+field
        notes='Internal prepared feature; public feature transport schema is not yet defined; integration owner must wire without inventing API fields.'
        if field in ['site_id','latitude','longitude','store_size_sqm','capex_inr','monthly_rent_inr','gross_margin_fraction']:
            target='Project.sites[].'+field;notes='Direct mapping, same units'
        elif field=='annual_opex_excl_rent_inr':target='Project.sites[].annual_opex_inr';notes='Rename only; annual non-rent cash OPEX excluding COGS'
        elif field=='city':target='Project.city';notes='Bengaluru data package remains separate from Navi Mumbai demo'
        rows.append(dict(source_table='site_features',source_field=field,target=target,conversion='identity',notes=notes))
    rows += [dict(source_table='candidate_sites',source_field='name',target='Project.sites[].name',conversion='identity',notes='Hypothetical name, no real available premises claim'),
      dict(source_table='existing_stores',source_field='store_id,name,latitude,longitude,store_size_sqm,theta,variable_contribution_margin',target='Project.stores[]',conversion='select canonical fields only',notes='Source status must accompany import as provenance'),
      dict(source_table='candidate_sites',source_field='SYNTHETIC_DEMO',target='Project.source_status',conversion='SYNTHETIC_DEMO -> SYNTHETIC',notes='Public enum supports SYNTHETIC/REAL/ASSUMED only; retain richer per-source provenance internally'),
      dict(source_table='spending_cells',source_field='cell_id,latitude,longitude,annual_wallet_inr',target="project['inputs']['cells']",conversion='select canonical fields; preserve one baseline',notes='Do not concatenate site catchment wallets or duplicate overlapping spending'),
      dict(source_table='infrastructure_scenarios',source_field='blue_scenario_open_date',target='Scenario.assumptions.opening_date',conversion='ISO date; leave official date separate',notes='Explicit hypothetical date, not an official promise')]
    csv_out('schema_mapping.csv',rows)
    shutil.copyfile(FINAL/'schema_mapping.csv',REPORTS/'schema_mapping.csv')

def build():
    manifests,logs=build_manifest()
    sites,stores=build_sites()
    grocery=build_expenditure()
    pixels,cells=build_population(grocery)
    pois=build_pois()
    stations,hourly,averages=build_stations_and_metro(pois)
    raws=build_dayparts(sites,pois,hourly)
    build_geography(sites)
    build_infrastructure(stations)
    build_assumptions(grocery)
    master=build_master(sites,pixels,pois,stations,averages,raws,grocery)
    schema_mapping()
    for row in GENERATED:
        MISSING.append(dict(table=row['table'],record_id=row['record_id'],field_name=row['field_name'],
            classification='SYNTHETIC_DEMO_ALLOWED' if row['source_status']=='SYNTHETIC_DEMO' else 'ASSUMPTION_ALLOWED',
            resolution='GENERATED_EXPLICITLY_LABELLED',reason=row['reason'],source_attempts='commercial-attempt' if row['table']=='candidate_sites' else row['source_id'],assumption_id=row['assumption_id']))
    csv_out('synthetic_assumptions.csv',GENERATED)
    # Also classify every nullable supporting column. Optional metadata blanks
    # are not confused with zero or silently filled.
    for r in MISSING:r['null_count']=None
    for path in sorted(FINAL.glob('*.csv')):
        if path.name in ['missing_fields.csv','field_lineage.csv','site_features.csv']:continue
        records=read_csv(path)
        if not records:continue
        for field in records[0]:
            count=sum(not r[field] for r in records)
            if not count:continue
            reason='Unreported or inapplicable source/assumption metadata; preserved as null, not fabricated.'
            classification='MUST_REMAIN_UNKNOWN'
            if field=='opening_hours':reason='OSM hours unreported; original field remains null and opportunity availability has a separate explicit assumption.';classification='FETCH_RETRY'
            elif field=='households_est':reason='Historical housing tables contain percentages; no defensible local household denominator.'
            elif field.startswith('verified_'):reason='Official commercial opening date not verified; inauguration and hypothetical scenario dates are separate fields.'
            elif path.name=='metro_hourly.csv' and field in ['exits','exits_source_locator']:reason='August workbook contains entries only; do not use OD origin-time aggregates as measured exit-clock traffic.'
            elif path.name=='metro_hourly.csv' and field in ['interval_end_local','interval_duration_minutes']:reason='August 23:00 to last train has an unknown end time/duration.'
            elif path.name=='site_ward_lookup.csv':reason='Electronic City candidates fall outside the available historical/new municipal ward coverage; no ward identity imputed.'
            MISSING.append(dict(table=path.stem,record_id='*',field_name=field,classification=classification,
                resolution='NULL_RETAINED',reason=reason,source_attempts='See acquisition_files.csv and record.source_id',assumption_id=None,null_count=count))
    csv_out('missing_fields.csv',MISSING)
    # Supporting field lineage uses a table wildcard plus each record's source
    # identifiers and original source locator/tags, avoiding millions of repeats.
    support_methods={
      'acquisition_files':('build_manifest','package-config','DERIVED','Exact request URL, retrieval time, response metadata and SHA-256; failed acquisition is not observed data'),
      'candidate_sites':('build_sites','assumptions;package-config','SYNTHETIC_ASSUMED','Hypothetical coordinates and bounded seeded business inputs; explicit field-level generated values in synthetic_assumptions'),
      'existing_stores':('build_sites','assumptions','SYNTHETIC_ASSUMED','Fictional branch coordinates, size and attraction parameters, never observed company outlets'),
      'spending_cells':('build_population','worldpop-2020;hces-2023-24;assumptions','DERIVED','Per-source-pixel area fractions normalized across a non-overlapping 10x10 grid; wallet = people * grocery per-capita monthly expenditure * 12'),
      'pois':('build_pois','osm-pois','DERIVED','Exact raw OSM element lookup using osm_type/osm_id; direct original tags and coordinates preserved; category/dedup/status derived'),
      'poi_deduplication':('build_pois','osm-pois','DERIVED','Same normalized name/category within 40m; links dropped element to retained element'),
      'expenditure_inputs':('build_expenditure','hces-2023-24','OBSERVED','NSS Report 592, PDF page 90, Statement 3U, column 14, Karnataka urban; source_locator identifies exact table'),
      'metro_hourly':('build_stations_and_metro','metro-rti','DERIVED','Original workbook row/column in entries_source_locator and exits_source_locator; original interval preserved; no missing-count imputation'),
      'metro_station_lookup':('build_stations_and_metro','metro-rti;osm-pois;yellow-official','DERIVED','Exact normalized station-name join, original station label and OSM ID retained'),
      'metro_activity_averages':('build_stations_and_metro','metro-rti','DERIVED','September paired valid hour entries/exits grouped by day type, observed clock-hour denominator'),
      'metro_date_coverage':('build_stations_and_metro','metro-rti','DERIVED','Calendar coverage over August 1 to September 30; no records is unreported, not zero traffic'),
      'daypart_weights':('build_dayparts','approved-weights','EXISTING_FIXTURE','Original category weights from data/demo/weights.json; six-bin durations/frequencies explicit; weights remain ASSUMED'),
      'poi_daypart_availability':('build_dayparts','osm-pois;assumptions','DERIVED','Parse recorded weekly schedule if fully supported; otherwise availability 0.5 and evidence 0.5, separately labelled assumptions'),
      'daypart_profiles':('build_dayparts','osm-pois;approved-weights;assumptions','DERIVED','sum(category_weight*exp(-distance_m/750)*availability*evidence) within 1500m; duration/frequency-adjusted weekly shares; excludes metro counts'),
      'metro_daypart_coverage':('build_dayparts','metro-rti','DERIVED','Early hours assigned to prior starting date; observed counts divided by observed hours with expected bin hours and partial coverage'),
      'census_2011_wards':('build_geography','census-2011','OBSERVED','Original OpenCity Census 2011 ward CSV; added year and source fields are metadata'),
      'ward_crosswalk':('build_geography','wards-2012;wards-2025;census-2011','DERIVED','Area overlap in EPSG:32643 clipped to AOI; no proportional redistribution of historical population asserted'),
      'site_ward_lookup':('build_geography','wards-2012;wards-2025;assumptions','DERIVED','Point-in-polygon against each vintage separately; unjoined/outside sites remain null'),
      'infrastructure':('build_infrastructure','yellow-official;blue-official;osm-roads;assumptions','DERIVED','Official project facts remain separate from OSM partial geometry and explicitly assumed opening/effect fields'),
      'infrastructure_scenarios':('build_infrastructure','yellow-official;blue-official;assumptions','SYNTHETIC_ASSUMED','Current has operational Yellow; hypothetical Blue opens 2027-07-01 and delays by 24 months; no feature uplift calculated'),
      'project_assumptions':('build_assumptions','assumptions;approved-weights;hces-2023-24','DERIVED','Per-record source_status/notes distinguish user configuration, approved project defaults and expenditure transformation'),
      'source_manifest':('build_manifest','package-config','DERIVED','Original licence/catalogue records and source-year metadata; unknown release or observation dates remain null'),
      'schema_mapping':('schema_mapping','package-config','DERIVED','Read-only comparison with backend/app/schemas.py; renames and internal seam mappings documented'),
      'synthetic_assumptions':('assumed','assumptions;approved-weights','SYNTHETIC_ASSUMED','Exact table/record/field generated value, generation class, method, reason, units and meaningful ranges'),
      'missing_fields':('build','package-config','DERIVED','Every generated input classification and each nullable supporting field classified without filling unknown observations'),
    }
    for path in sorted(FINAL.glob('*.csv')):
        if path.name in ['site_features.csv','field_lineage.csv']:continue
        rows=read_csv(path)
        if not rows:continue
        function,sources,origin,method=support_methods[path.stem]
        for f in rows[0]:
            lineage(path.stem,'*',f,origin,sources,
              'build.py:'+function+'; '+method,
              locator=path.name,limitations='Wildcard applies to every record in this table; all generated numeric/coordinate inputs have explicit record-level assumption rows.')
    csv_out('field_lineage.csv',LINEAGE)
    METRICS['master_value_origins']=dict(Counter(r['origin'] for r in LINEAGE if r['table']=='site_features'))
    json_out(PROCESSED/'build_metrics.json',METRICS)
    json_out(PROCESSED/'build_config.json',dict(feature_snapshot_id=SNAP,source_manifest_id=MANIFEST,reference_date=ASOF,
        timezone=TZ,currency='INR',coordinate_crs='EPSG:4326',metric_crs='EPSG:32643',seed=20261024,
        bbox_west_south_east_north=BOUNDS,master_columns=MASTER,baseline_git_head='569f4f52f459ed09129c04a17ac97485601d7bb7',
        inspected_fixtures={p.name:dict(sha256=digest(p),rows=len(load(p)) if isinstance(load(p),list) else None) for p in (ROOT/'data/demo').glob('*.json')}))
    print(json.dumps(METRICS,indent=2))

if __name__=='__main__':build()
