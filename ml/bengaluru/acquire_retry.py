from acquire import *

def main():
    bbox='12.815,77.600,12.940,77.725'
    q=f'''[out:json][timeout:90];(nwr[shop~"supermarket|convenience|grocery|mall|department_store"]({bbox});nwr[office]({bbox});nwr[amenity~"school|college|university|kindergarten|hospital|clinic|doctors|pharmacy|bus_station|restaurant|cafe|fast_food|food_court|cinema|theatre"]({bbox});nwr[railway~"station|halt|subway_entrance"]({bbox});nwr[public_transport~"station|platform|stop_position"]({bbox});nwr[highway=bus_stop]({bbox});nwr[leisure]({bbox}););out center tags;'''
    roads=f'''[out:json][timeout:90];(way[highway~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|footway|pedestrian|path"]({bbox});way[railway~"subway|construction"]({bbox}););out tags geom;'''
    tasks=[
      ('https://overpass.kumi.systems/api/interpreter?data='+urllib.parse.quote(q),'osm_pois.json'),
      ('https://overpass-api.de/api/interpreter?data='+urllib.parse.quote(roads),'osm_roads.json'),
      ('https://english.bmrc.co.in/','bmrcl_home_alternative.html'),
      ('https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf','official_economic_survey_2025_26.pdf'),
      ('https://mospi.gov.in/sites/default/files/publication_reports/Report_592_HCES_2023-24.pdf','hces_2023_24_report.pdf'),
      ('https://esankhyiki.mospi.gov.in/datacatalogue/HCES/2023-24/Factsheet/Statement_4.xlsx','hces_statement_4.xlsx'),
      ('https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND','worldpop_1km_api.json'),
    ]
    (RAW/'osm_pois_query.overpassql').write_text(q)
    (RAW/'osm_roads_query.overpassql').write_text(roads)
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        records=list(pool.map(lambda t:fetch(*t,timeout=120),tasks))
    LOG.write_text(json.dumps(json.loads(LOG.read_text())+records,indent=2))
    for r in records: print(r['status'],r['path'],r.get('bytes',r.get('error')),flush=True)

if __name__=='__main__':main()
