"""Public-source acquisition only; no models, engines, or Git mutations."""
from pathlib import Path
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'bengaluru'
RAW = DATA / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
LOG = DATA / 'acquisition_log.json'

def fetch(url, name, timeout=60):
    path = RAW / name
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'StoreScout-public-research/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            content_type = r.headers.get('Content-Type', '')
            last_modified = r.headers.get('Last-Modified')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        record = dict(url=url, path=str(path.relative_to(ROOT)), status='DOWNLOADED',
                      bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                      retrieved_at_utc=started, content_type=content_type,last_modified=last_modified)
    except Exception as exc:
        record = dict(url=url, path=str(path.relative_to(ROOT)), status='FAILED',
                      error=str(exc), retrieved_at_utc=started)
    return record

def main():
    sources = [
        ('https://api.github.com/repos/Vonter/bmrcl-ridership-hourly/git/trees/main?recursive=1','github_tree.json'),
        ('https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/README.md','ridership_README.md'),
        ('https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/DATA.md','ridership_DATA.md'),
        ('https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/LICENSE','ridership_LICENSE.txt'),
        ('https://data.opencity.in/api/3/action/package_show?id=bmrcl-station-wise-ridership-data','opencity_metro_metadata.json'),
        ('https://data.opencity.in/api/3/action/package_show?id=bengaluru-census-2011','opencity_census_metadata.json'),
        ('https://data.opencity.in/api/3/action/package_show?id=gba-wards-delimitation-2025','opencity_wards_metadata.json'),
        ('https://www.worldpop.org/rest/data/pop/wpgp?iso3=IND','worldpop_metadata.json'),
        ('https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif','population/ind_ppp_2020_1km_Aggregated_UNadj.tif'),
        ('https://esankhyiki.mospi.gov.in/catalogue-main/catalogue?product=HCES','hces_catalogue.html'),
        ('https://microdata.gov.in/nada/index.php/catalog/237/related-materials','hces_related_materials.html'),
        ('https://www.mospi.gov.in/sites/default/files/publication_reports/Report_591_HCES_2022-23New.pdf','hces_2022_23.pdf'),
        ('https://bmrc.co.in','bmrcl_home.html'),
    ]
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        records=list(pool.map(lambda s:fetch(*s), sources))
    LOG.write_text(json.dumps(records,indent=2),encoding='utf-8')
    for r in records:
        print(r['status'],r['path'],r.get('bytes',r.get('error')))
    for name in ['github_tree.json','opencity_census_metadata.json','opencity_wards_metadata.json','opencity_metro_metadata.json','worldpop_metadata.json']:
        path=RAW/name
        if not path.exists(): continue
        obj=json.loads(path.read_text(encoding='utf-8'))
        if name=='github_tree.json':
            print('GITHUB',[(x['path'],x.get('size')) for x in obj.get('tree',[]) if x['type']=='blob'][:100])
        elif 'opencity' in name:
            obj=obj.get('result',{})
            print(name,'LICENSE',obj.get('license_id'),obj.get('license_title'),'RESOURCES',[(x['id'],x['name'],x['url'],x.get('format')) for x in obj.get('resources',[])])
        else:
            print('WORLDPOP',str(obj)[:4000])

if __name__=='__main__': main()
