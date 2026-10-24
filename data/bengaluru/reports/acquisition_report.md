# Bengaluru dataset acquisition report

Reference date: 2026-10-24. Sources were retrieved on October 24, 2026; exact UTC timestamps are in acquisition_files.csv.

All six canonical Navi Mumbai fixture files were inspected and preserved. Counts: 10 candidates, 4 fictional stores, 100 cells, 60 POIs, 1 hypothetical event and 36 assumed category/bin weights. No coordinates or financial actuals were copied from Navi Mumbai. The approved engineering weights and project-level budget/horizon/discount assumptions remain assumptions.

The first DataMeet candidate file (`raw/wards/BBMP_198.geojson`) is actually a **243-ward 2022 layer**, as its README makes clear. It is archived as an unused acquisition and is not used for Census joining. The separately acquired `BBMP_2012_198.geojson` contains the historical 198 wards.

| Status | Local file | Bytes | Source URL |
|---|---|---:|---|
| DOWNLOADED | data/bengaluru/raw/github_tree.json | 6206 | https://api.github.com/repos/Vonter/bmrcl-ridership-hourly/git/trees/main?recursive=1 |
| DOWNLOADED | data/bengaluru/raw/ridership_README.md | 3906 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/README.md |
| DOWNLOADED | data/bengaluru/raw/ridership_DATA.md | 5596 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/DATA.md |
| DOWNLOADED | data/bengaluru/raw/ridership_LICENSE.txt | 25279 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/LICENSE |
| DOWNLOADED | data/bengaluru/raw/opencity_metro_metadata.json | 6703 | https://data.opencity.in/api/3/action/package_show?id=bmrcl-station-wise-ridership-data |
| DOWNLOADED | data/bengaluru/raw/opencity_census_metadata.json | 9360 | https://data.opencity.in/api/3/action/package_show?id=bengaluru-census-2011 |
| DOWNLOADED | data/bengaluru/raw/opencity_wards_metadata.json | 22787 | https://data.opencity.in/api/3/action/package_show?id=gba-wards-delimitation-2025 |
| DOWNLOADED | data/bengaluru/raw/worldpop_metadata.json | 38419 | https://www.worldpop.org/rest/data/pop/wpgp?iso3=IND |
| DOWNLOADED | data/bengaluru/raw/population/ind_ppp_2020_1km_Aggregated_UNadj.tif | 18313124 | https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif |
| UNUSABLE_HTML_APP_SHELL | data/bengaluru/raw/hces_catalogue.html | 1198 | https://esankhyiki.mospi.gov.in/catalogue-main/catalogue?product=HCES |
| DOWNLOADED | data/bengaluru/raw/hces_related_materials.html | 88802 | https://microdata.gov.in/nada/index.php/catalog/237/related-materials |
| DOWNLOADED | data/bengaluru/raw/hces_2022_23.pdf | 7521404 | https://www.mospi.gov.in/sites/default/files/publication_reports/Report_591_HCES_2022-23New.pdf |
| FAILED | data/bengaluru/raw/bmrcl_home.html |  | https://bmrc.co.in |
| DOWNLOADED | data/bengaluru/raw/metro/data_station-hourly.csv.zip | 441150 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/data/station-hourly.csv.zip |
| DOWNLOADED | data/bengaluru/raw/metro/data_station-hourly-exits.csv.zip | 454867 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/data/station-hourly-exits.csv.zip |
| DOWNLOADED | data/bengaluru/raw/metro/raw_station-codes.csv | 2069 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/station-codes.csv |
| DOWNLOADED | data/bengaluru/raw/metro/raw_station-names.csv | 864 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/station-names.csv |
| DOWNLOADED | data/bengaluru/raw/metro/raw_august_station-hourly.xlsx | 244975 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/august/station-hourly.xlsx |
| DOWNLOADED | data/bengaluru/raw/metro/raw_september_station-hourly.xlsx | 714604 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/september/station-hourly.xlsx |
| DOWNLOADED | data/bengaluru/raw/metro/parse.py | 27155 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/parse.py |
| DOWNLOADED | data/bengaluru/raw/metro/CITATION.cff | 587 | https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/CITATION.cff |
| DOWNLOADED | data/bengaluru/raw/census/4efdf9f5-5790-41ca-ac68-13691b31f364.csv | 87969 | https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/4efdf9f5-5790-41ca-ac68-13691b31f364/download/a7c8acc4-6540-4152-9fee-aa084baac188.csv |
| DOWNLOADED | data/bengaluru/raw/census/4bd82527-84a1-45ae-b695-5ed0c0ecbd85.csv | 495686 | https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/4bd82527-84a1-45ae-b695-5ed0c0ecbd85/download/f00519ff-7932-4c94-ba8f-654978f1a03a.csv |
| DOWNLOADED | data/bengaluru/raw/census/269cdf01-dae5-4736-8f4d-72a8e57fa3a9.csv | 16236 | https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/269cdf01-dae5-4736-8f4d-72a8e57fa3a9/download/83390055-d933-420f-82b7-608e139336c2.csv |
| DOWNLOADED | data/bengaluru/raw/wards/9013d656-8051-4e2d-9648-46efd0d86d3d.kml | 4054904 | https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml |
| DOWNLOADED | data/bengaluru/raw/wards/dbe57ae6-a72f-426e-917b-e55b3b22a87b.kml | 3745694 | https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/dbe57ae6-a72f-426e-917b-e55b3b22a87b/download/1c5bbd4e-006c-4130-b278-fd6680fef91b.kml |
| DOWNLOADED | data/bengaluru/raw/official_yellow_opening.html | 189166 | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848 |
| DOWNLOADED | data/bengaluru/raw/hces_2023_24_factsheet.pdf | 2615083 | https://mospi.gov.in/sites/default/files/publication_reports/HCES%20FactSheet%202023-24.pdf |
| DOWNLOADED | data/bengaluru/raw/worldpop_licence.txt | 19271 | https://hub.worldpop.org/data/licence.txt |
| DOWNLOADED | data/bengaluru/raw/worldpop_1km_metadata.html | 21087 | https://hub.worldpop.org/geodata/listing?id=64 |
| FAILED | data/bengaluru/raw/bmrcl_project_status.html |  | https://english.bmrc.co.in/project-status/ |
| FAILED | data/bengaluru/raw/bmrcl_blue_profile.html |  | https://english.bmrc.co.in/project-profile-phase-2a-and-phase-2b/ |
| DOWNLOADED | data/bengaluru/raw/osm_copyright.html | 21314 | https://www.openstreetmap.org/copyright |
| UNUSABLE_HTML_APP_SHELL | data/bengaluru/raw/hces_portal.html | 1198 | https://esankhyiki.mospi.gov.in |
| FAILED | data/bengaluru/raw/census_portal.html |  | https://censusindia.gov.in |
| FAILED | data/bengaluru/raw/osm_overpass.json |  | https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A150%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Bhighway~%22motorway%7Ctrunk%7Cprimary%7Csecondary%7Ctertiary%7Cresidential%7Cunclassified%7Cservice%7Cfootway%7Cpedestrian%7Cpath%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Brailway~%22subway%7Cconstruction%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%20geom%3B |
| FAILED | data/bengaluru/raw/osm_pois.json |  | https://overpass.kumi.systems/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%3B |
| DOWNLOADED | data/bengaluru/raw/osm_roads.json | 14210526 | https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28way%5Bhighway~%22motorway%7Ctrunk%7Cprimary%7Csecondary%7Ctertiary%7Cresidential%7Cunclassified%7Cservice%7Cfootway%7Cpedestrian%7Cpath%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Brailway~%22subway%7Cconstruction%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20tags%20geom%3B |
| DOWNLOADED | data/bengaluru/raw/bmrcl_home_alternative.html | 52097 | https://english.bmrc.co.in/ |
| DOWNLOADED | data/bengaluru/raw/official_economic_survey_2025_26.pdf | 15118530 | https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf |
| FAILED | data/bengaluru/raw/hces_2023_24_report.pdf |  | https://mospi.gov.in/sites/default/files/publication_reports/Report_592_HCES_2023-24.pdf |
| UNUSABLE_HTML_APP_SHELL | data/bengaluru/raw/hces_statement_4.xlsx | 1198 | https://esankhyiki.mospi.gov.in/datacatalogue/HCES/2023-24/Factsheet/Statement_4.xlsx |
| FAILED | data/bengaluru/raw/worldpop_1km_api.json |  | https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND |
| DOWNLOADED | data/bengaluru/raw/osm_pois_alternative.json | 1424360 | https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%3B |
| DOWNLOADED | data/bengaluru/raw/hces_2023_24_full.pdf | 11737505 | https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf |
| DOWNLOADED | data/bengaluru/raw/blue_dpr_metadata.json | 20416 | https://data.opencity.in/api/3/action/package_show?id=bengaluru-metro-phase-2a-documents |
| FAILED | data/bengaluru/raw/worldpop_1km_api_retry.json |  | https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND |
| DOWNLOADED | data/bengaluru/raw/osm_shops.json | 407463 | https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A60%5D%3Bnwr%5Bshop%5D%2812.815%2C77.60%2C12.94%2C77.725%29%3Bout%20center%20tags%3B |
| DOWNLOADED | data/bengaluru/raw/commercial_rent_attempt.html | 1056789 | https://www.magicbricks.com/commercial-property-for-rent-in-electronic-city-bangalore-pppfr |
| DOWNLOADED | data/bengaluru/raw/bmrcl_upcoming.html | 23353 | https://english.bmrc.co.in/upcoming-projects/ |
| DOWNLOADED | data/bengaluru/raw/bmrcl_progress.html | 22562 | https://english.bmrc.co.in/dpr-project-progress/ |
| DOWNLOADED | data/bengaluru/raw/old_ward_search.json | 105607 | https://data.opencity.in/api/3/action/package_search?q=bbmp%20ward%20boundaries |
| DOWNLOADED | data/bengaluru/raw/old_ward_github.json | 3758 | https://api.github.com/repos/datameet/Municipal_Spatial_Data/contents/Bangalore |
| DOWNLOADED | data/bengaluru/raw/wards/BBMP_198.geojson | 2103364 | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP.geojson |
| DOWNLOADED | data/bengaluru/raw/wards/datameet_Readme.md | 580 | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/Readme.md |
| FAILED | data/bengaluru/raw/datameet_LICENSE |  | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/LICENSE |
| DOWNLOADED | data/bengaluru/raw/wards/BBMP_2012_198.geojson | 1881095 | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP_oldWards.geojson |

Failed endpoints have legitimate alternatives archived above. eSankhyiki HTTP 200 app shells are not counted as downloaded statistical records. The official full NSS report supplies the expenditure observations instead. Census portal TLS validation was not bypassed; OpenCity CSVs supply the historical records. The proprietary commercial HTML is retained locally only and excluded from the deliverable ZIP.

All raw files have exact URLs, retrieval times and SHA-256 hashes in acquisition_files.csv. Downloading a document does not imply that all its contents were used. Upstream parse.py is archived for inspection only, never executed.