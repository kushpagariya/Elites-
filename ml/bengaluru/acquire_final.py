from acquire import *
import re

def main():
    q=(RAW/'osm_pois_query.overpassql').read_text()
    tasks=[
      ('https://overpass-api.de/api/interpreter?data='+urllib.parse.quote(q),'osm_pois_alternative.json'),
      ('https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf','hces_2023_24_full.pdf'),
      ('https://data.opencity.in/api/3/action/package_show?id=bengaluru-metro-phase-2a-documents','blue_dpr_metadata.json'),
      ('https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND','worldpop_1km_api_retry.json'),
    ]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(lambda t:fetch(*t,timeout=90),tasks))
    LOG.write_text(json.dumps(json.loads(LOG.read_text())+records,indent=2))
    for r in records:print(r['status'],r['path'],r.get('bytes',r.get('error')),flush=True)
    t=(RAW/'bmrcl_home_alternative.html').read_text(encoding='utf-8')
    print('BMRCL_LINKS',[x for x in re.findall('href=[\"\x27]([^\"\x27]+)',t) if any(v in x.lower() for v in ['project','dpr','phase'])])

if __name__=='__main__':main()
