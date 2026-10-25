from acquire import *

def main():
    tasks=[]
    tree=json.loads((RAW/'github_tree.json').read_text())
    revision=tree['sha']
    for path in ['data/station-hourly.csv.zip','data/station-hourly-exits.csv.zip','raw/station-codes.csv','raw/station-names.csv','raw/august/station-hourly.xlsx','raw/september/station-hourly.xlsx','parse.py','CITATION.cff']:
        tasks.append((f'https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/{revision}/{path}','metro/'+path.replace('/','_')))
    for meta,label in [('opencity_census_metadata.json','census'),('opencity_wards_metadata.json','wards')]:
        info=json.loads((RAW/meta).read_text())['result']
        for i,r in enumerate(info['resources']):
            if (label=='census' and r['format']=='CSV') or (label=='wards' and i in [0,1]):
                tasks.append((r['url'],f'{label}/{r["id"]}.{r["format"].lower()}'))
    tasks += [
        ('https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848','official_yellow_opening.html'),
        ('https://mospi.gov.in/sites/default/files/publication_reports/HCES%20FactSheet%202023-24.pdf','hces_2023_24_factsheet.pdf'),
        ('https://hub.worldpop.org/data/licence.txt','worldpop_licence.txt'),
        ('https://hub.worldpop.org/geodata/listing?id=64','worldpop_1km_metadata.html'),
        ('https://english.bmrc.co.in/project-status/','bmrcl_project_status.html'),
        ('https://english.bmrc.co.in/project-profile-phase-2a-and-phase-2b/','bmrcl_blue_profile.html'),
        ('https://www.openstreetmap.org/copyright','osm_copyright.html'),
        ('https://esankhyiki.mospi.gov.in','hces_portal.html'),
        ('https://censusindia.gov.in','census_portal.html'),
    ]
    bbox='12.815,77.600,12.940,77.725'
    query=f'''[out:json][timeout:150];(nwr[shop~"supermarket|convenience|grocery|mall|department_store"]({bbox});nwr[office]({bbox});nwr[amenity~"school|college|university|kindergarten|hospital|clinic|doctors|pharmacy|bus_station|restaurant|cafe|fast_food|food_court|cinema|theatre"]({bbox});nwr[railway~"station|halt|subway_entrance"]({bbox});nwr[public_transport~"station|platform|stop_position"]({bbox});nwr[highway=bus_stop]({bbox});nwr[leisure]({bbox});way[highway~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|footway|pedestrian|path"]({bbox});way[railway~"subway|construction"]({bbox}););out center tags geom;'''
    (RAW/'osm_query.overpassql').write_text(query)
    tasks += [('https://overpass-api.de/api/interpreter?data='+urllib.parse.quote(query),'osm_overpass.json')]
    with cf.ThreadPoolExecutor(max_workers=7) as pool:
        records=list(pool.map(lambda t: fetch(*t,timeout=180 if 'overpass' in t[1] else 70),tasks))
    prior=json.loads(LOG.read_text())
    LOG.write_text(json.dumps(prior+records,indent=2))
    for r in records:print(r['status'],r['path'],r.get('bytes',r.get('error')),flush=True)

if __name__=='__main__':main()
