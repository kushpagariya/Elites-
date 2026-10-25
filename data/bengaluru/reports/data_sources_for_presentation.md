# Bengaluru data sources for presentation and site-feature audit

Repository: StoreScout. The recommendations also address the RetailIQ site-ranking and DaypartDNA components named in the request.

**Scope:** this is an audit of the existing frozen files. The final instruction limits changes to this report. No enriched CSV, modified master, modified lineage, modified completion report, refreshed source data, updated ZIP, training labels, model or ranking is produced. The enrichment result below is an in-memory feasibility check, not an exported dataset.

**Existing package:** 10 candidate rows × 50 master columns; 20 master nulls; 27 CSV tables. Branch `ML`; existing HEAD `569f4f52f459ed09129c04a17ac97485601d7bb7`. The existing quality report records 40 passed checks and no failed checks. This audit also identifies provenance and metadata gaps that those checks did not test.

## 1. Presentation-ready source summary

| Source/Organization | Data Used | Reference Year | Collection Method | Dataset Contribution | Source URL |
|---|---|---|---|---|---|
| OpenStreetMap contributors / Overpass | Mapped POIs, grocery competition, stations, roads and construction rail segments | Extracted 24 October 2026; individual feature survey/edit dates unknown | Overpass JSON API; geographic filtering | POI counts, competition, nearest metro and POI opportunity; transport geometry separately | [Overpass endpoint](https://overpass-api.de/api/interpreter); exact query URLs in Appendix A |
| WorldPop / University of Southampton and collaborators | India aggregated, UN-adjusted 1km population raster | Modelled population year 2020; exact release unverified | Direct GeoTIFF download; metric pixel intersections | Population, weighted distance, spending-cell population and wallet population input | [Actual raster download](https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif) |
| BMRCL, published through Vonter; OpenCity metadata cross-check | Original station-hour workbooks | 1–18 August and 1–30 September 2025; master uses September only | Commit-pinned GitHub downloads; workbook extraction | Hourly traffic, station/coverage tables and four master historical traffic averages | [Dataset repository](https://github.com/Vonter/bmrcl-ridership-hourly) |
| Census of India / ORGI via OpenCity | Historical ward counts; housing and asset percentages | 2011 | CKAN catalogue API and three CSV downloads | Historical Census and ward context; not current master population | [Actual metadata request](https://data.opencity.in/api/3/action/package_show?id=bengaluru-census-2011) |
| DataMeet municipal spatial repository | Historical 198-ward geometry | Map vintage 2012 per README; exact release unknown | GeoJSON download and polygon processing | Historical geometry, ward crosswalk and site ward lookup | [Actual historical geometry](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP_oldWards.geojson) |
| Greater Bengaluru Authority, through OpenCity | Final 369-ward KML | December 2025 boundary vintage | CKAN API, KML download and XML/geospatial processing | New ward geometry, site ward lookup and overlap crosswalk | [Actual KML download](https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml) |
| MoSPI / National Statistics Office | HCES Report 592, Karnataka urban expenditure, Statement 3U, column 14 | August 2023–July 2024; nominal survey prices | Official PDF download and text extraction | Expenditure inputs and assumed category basket transferred locally into wallets | [Actual report download](https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf) |
| Prime Minister Office / Press Information Bureau | Yellow Line inauguration statement | 10 August 2025 | Official HTML download | Operational-baseline context and infrastructure metadata, not measured ridership | [Actual official statement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848) |
| Government of Karnataka, Economic Survey through OpenCity | Phase 2A/2B descriptions and historical completion programmes | Report 2025–26; exact status observation date unknown | Mirrored government PDF download and extraction | Future infrastructure context; no Blue Line uplift in baseline master | [Actual mirrored PDF](https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf) |

The Overpass URL is abbreviated in this summary for slide readability. Appendix A preserves every exact requested URL, including query parameters and the source request timestamp. A dataset discovery page, the actual download endpoint and the original issuing authority are distinguished throughout this report.

### Paragraph for the presentation

We prepared a reproducible Bengaluru retail feature package for the Central Silk Board–Bommanahalli–Electronic City corridor using publicly downloaded OpenStreetMap records, WorldPop 2020 population estimates, BMRCL 2025 hourly ridership workbooks, Karnataka urban HCES 2023–24 expenditure, and historical and current ward boundaries. We cleaned mapped POIs, computed geographic catchment features and retained historical measurement dates. Ten candidate stores, four existing branches and unavailable commercial inputs are explicitly synthetic or assumed. The resulting 10-site feature snapshot includes documented POI-based DaypartDNA proxies; it contains no observed sales labels or trained predictions.

**Claims supported by this package:** source evidence was downloaded and archived; source years and assumptions are retained; the output is a site-feature/demo package. Do not describe it as measured 2026 local demand, observed store footfall, a 100m population product, verified available commercial premises, validated sales predictions or a trained retail-ranking system.

## 2. Collection evidence and terminology

The acquisition log contains **57 attempts: 44 `DOWNLOADED`, 3 `UNUSABLE_HTML_APP_SHELL`, 10 `FAILED`**. All **47 archived responses with recorded SHA-256 values** match the local files, including the three unusable responses. A successful response can be metadata or an unused alternative; it does not automatically become a statistical input.

All logged local acquisitions occurred on **2026-10-24**. In `acquire.py`, `retrieved_at_utc` is set **before the request starts**. It is therefore a request-start timestamp, not a verified response-completion timestamp. Source observation/reference periods, publication dates, catalogue update dates, local acquisition, and the feature snapshot date are different concepts.

“Observed source record” means an actual downloaded record, not an independently ground-verified shop. WorldPop is a published **modelled** estimate. Census and metro data are historical reported statistics. Synthetic premises and financial inputs are neither observed records nor calibrated predictions.

The AOI is an analyst-selected rectangle, not an official administrative boundary: west **77.600**, south **12.815**, east **77.725**, north **12.940**. Coordinates are WGS84/EPSG:4326; metric polygon operations use EPSG:32643; point distances use the WGS84 ellipsoid. Local timestamps use Asia/Kolkata, UTC+05:30. Money is INR.

## 3. External source details

### 3.1 OpenStreetMap: POIs, competition, metro geography and roads

- **Provider:** OpenStreetMap contributors; collection service Overpass API. Manifest IDs: `osm-pois`, `osm-roads`.
- **Actually used requests:** the exact successful API URLs associated with `raw/osm_pois_alternative.json` and `raw/osm_roads.json` in Appendix A. Query text is preserved in `raw/osm_pois_query.overpassql` and `raw/osm_roads_query.overpassql`. The broader initial request failed HTTP 502; the Kumi POI alternative timed out. A later shop-only query succeeded into `osm_shops.json`, but the build does not read it.
- **Collected data:** 5,285 POI elements before filtering; 4,995 retained POIs. Retained categories: **219 competitors, 692 offices, 413 education, 449 healthcare, 397 transit, 34 shopping, 2,791 food/leisure**. Transport JSON contains 27,764 line records. IDs, source tags, available opening hours and coordinates are retained.
- **Reference times:** POI database snapshot `2026-10-24T14:23:01Z`; road database snapshot `2026-10-24T14:20:56Z`; unused shop-only snapshot `2026-10-24T14:24:00Z`. Individual feature survey/edit dates were not collected: the queries request tags/centres/geometry, not per-object metadata.
- **Processing:** category precedence in `category()`; use node coordinates or returned way/relation bounding-box centres; reject centres outside the AOI; collapse same normalized name/category within 40m, preferring nodes by sort order. **264** duplicate records are logged; **16** outside-centre elements are excluded; **10** queried elements have no accepted category. Aggregate retained POIs within 1,500m geodesically. Grocery, convenience and supermarket records form external competition; malls/department stores form the separate shopping category.
- **Master usage:** competitor count/index/distance; six category counts; nearest metro ID/distance through the lookup; six Daypart raw values through schedule and weight transformations. Supporting tables include `pois`, `poi_deduplication`, `poi_daypart_availability`, `daypart_profiles`, `metro_station_lookup`; transport geometry and partial Blue alignment are separate GeoJSON outputs.
- **Limits/verification:** this is incomplete crowdsourced coverage, not a business census. Transit stops/platforms/entrances can refer to the same physical hub. Name-based deduplication is not general polygon-overlap deduplication; unnamed, non-Latin-only or differently named overlapping records can remain. Opening-hours coverage is limited. Roads do not establish travel times. OSM ODbL attribution is recorded in `raw/osm_copyright.html`.

### 3.2 WorldPop: population, not expenditure

- **Provider:** WorldPop, University of Southampton and collaborators. Manifest ID: `worldpop-2020`.
- **Actual underlying file:** [India 2020 aggregated UN-adjusted GeoTIFF](https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif), archived as `raw/population/ind_ppp_2020_1km_Aggregated_UNadj.tif`. This is the **1km aggregated** product, with recorded resolution 0.0083333333 degrees, not 100m.
- **Metadata:** the successful [wpgp API request](https://www.worldpop.org/rest/data/pop/wpgp?iso3=IND) describes a related underlying 100m series. Both requests to `wpgpunadj1km?iso3=IND` failed HTTP 500. The generic listing page is archived, but the exact release of the downloaded aggregated raster remains unverified. Do not copy the related product’s release date or resolution into this product’s metadata.
- **Reference:** population model year **2020**; local acquisition **2026-10-24**; exact raster release day unknown.
- **Processing:** read the overlapping 16×16 raster window; intersect pixels with the AOI in a metric CRS; assume uniform density within each source pixel. Allocate clipped population once to a non-overlapping 10×10 grid, normalizing each source-pixel partition to conserve population. For master population and weighted distance, intersect source pixels **directly** with each 1,500m circle. The master is not calculated by summing spending-cell centroids.
- **Usage:** `population_1500m_est`, `mean_wallet_weighted_distance_m`, population input to `annual_wallet_inr`, and `spending_cells.csv`. The clipped raster and processing metadata are in `processed/`.
- **Limits/verification:** historical modelled population, not measured 2026 Census counts. No growth adjustment was made. Constant within-pixel density and intersection-centroid distance are approximations. The archived [WorldPop licence text](https://hub.worldpop.org/data/licence.txt) explicitly states CC-BY-4.0. Population itself is not household expenditure.

### 3.3 BMRCL hourly ridership through Vonter and OpenCity

- **Authority/provider:** Bangalore Metro Rail Corporation Limited, described by the GitHub publisher as RTI-supplied data. Immediate download publisher: **Vonter on GitHub**. OpenCity supplies archived catalogue metadata for cross-checking. The raw workbooks used here were not downloaded directly from an operator API.
- **Dataset:** [Vonter/bmrcl-ridership-hourly](https://github.com/Vonter/bmrcl-ridership-hourly). Revision from the archived GitHub tree: **`6c44579b5ff3428a88bddc44baf84e436a940612`**.
- **Actual workbooks:** [August station-hourly workbook](https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/august/station-hourly.xlsx) and [September station-hourly workbook](https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/september/station-hourly.xlsx). Exact alias/code CSV and processed ZIP URLs are also in Appendix A.
- **Reference coverage:** source network data covers **1–18 August and 1–30 September 2025**. Yellow Line stations have later August coverage following launch. The September workbook has separate Entry and Exit sheets. Final corridor output has **11,976** station-date-hour records for **13** stations; the full processed network has 92,280 intervals for 83 stations.
- **Collection/processing:** direct commit-pinned downloads; `openpyxl` extraction of the original wide workbooks. Preserve raw row/column locators. Construct IDs from original station label codes; use known aliases and exact normalized station-name joins to OSM. The alpha station-code CSV and processed ZIPs are archived, but do not drive the final original-workbook hourly parser. August 23:00-to-last-train retains null duration/end; August exits remain null. Missing dates are not filled with zeros. September H00–H23 are treated as reported 60-minute clock intervals; explicit night zeros remain observations.
- **Usage:** `metro_hourly`, station lookup, activity averages, date/daypart coverage. Master uses nearest-station **September 2025 only**: 22 weekdays × 24 = **528** clock hours; 8 weekend days × 24 = **192** clock hours per station. These are not projected 2026 values.
- **Limits/verification:** workbook integrity and publisher-described RTI provenance are verified locally; a certified RTI response chain or original first-party workbook delivery URL is not archived. The alternative processed data may fill missing values or derive destination sums, so it is not treated as authoritative exit-clock measurement. GitHub states ODbL, OpenCity metadata states `cc-nc`, and BMRCL content copyright is noted. Commercial redistribution rights remain unresolved.

### 3.4 Census of India 2011 through OpenCity

- **Provider/authority:** Office of the Registrar General & Census Commissioner, India, as identified in the archived OpenCity organization metadata; catalogue author `opencity`. Manifest ID: `census-2011`.
- **Dataset page:** [Bengaluru Census 2011](https://data.opencity.in/dataset/bengaluru-census-2011). **Actual discovery request:** [CKAN package_show](https://data.opencity.in/api/3/action/package_show?id=bengaluru-census-2011). Three exact CSV downloads are recorded in Appendix A, corresponding to ward statistics, housing/houselisting, and household assets.
- **Data/reference:** **198 historical ward records** with population, male/female and SC/ST reported counts; housing and assets CSVs contain percentages. All remain **2011** observations. Catalogue creation/modification dates are not Census observation dates.
- **Processing:** preserve ward data in `census_2011_wards.csv` with reference/source metadata; join to historical geometry using ward number. Discard embedded population values in the geometry file rather than mixing those values with the Census table.
- **Usage:** historical supporting table, ward crosswalk and site context. **No current master population or wallet value is calculated from Census counts.** Housing/asset percentages are archived but not incorporated into the master.
- **Limits/verification:** the official Census portal request failed TLS certificate verification; it was not bypassed. Mirror tables were not reconciled against a newly downloaded first-party publication. Exact original official data-file URL and exact release day are not captured. OpenCity lists Other (Public Domain), which is catalogue metadata. Percentages cannot be used as household counts, and 2011 ward totals cannot be called current catchment population.

### 3.5 DataMeet historical ward geometry

- **Provider:** DataMeet Municipal_Spatial_Data repository. Manifest ID: `wards-2012`.
- **Actually used:** [BBMP_oldWards.geojson](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP_oldWards.geojson), archived as `raw/wards/BBMP_2012_198.geojson`; [README](https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/Readme.md) supplies vintage/licence information.
- **Reference:** README identifies the historical layer as Bangalore Ward Maps **2012**. The used layer contains 198 features. Its exact release date and original authority-hosted data-file URL are unverified. The download URL uses mutable `master`; frozen snapshots and hashes preserve the acquired version.
- **Processing/usage:** validate/repair geometries, subset to the AOI, discard embedded population, join Census ward codes, and compute **geometry-only** old/new ward overlaps in EPSG:32643. Outputs: historical ward GeoJSON, `ward_crosswalk`, `site_ward_lookup`. It is not a population source for the master catchments.
- **Discrepancy:** `raw/wards/BBMP_198.geojson` was downloaded from current `BBMP.geojson`, but actually has **243 wards of 2022 vintage** according to README. It is an unused acquisition. The builder correctly selects the separately acquired historical file. No silent renaming or correction was performed in this audit.
- **Licence:** README states CC-BY-SA-2.5-IN. Root LICENSE request returned 404, so the available licence evidence is the archived README.

### 3.6 GBA final 2025 wards through OpenCity

- **Provider/authority:** Greater Bengaluru Authority, as named in OpenCity organization metadata; catalogue author `Vaidya R`. Manifest ID: `wards-2025`.
- **Actual catalogue request:** [GBA CKAN metadata](https://data.opencity.in/api/3/action/package_show?id=gba-wards-delimitation-2025). **Used file:** [final December 2025 369-ward KML](https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml). A second KML was downloaded but is not selected by `build_geography()`.
- **Reference:** resource title/file identify **December 2025** boundary vintage. Exact original GBA download URL and exact publication day are not captured; the verified transport URL is the OpenCity mirror.
- **Processing/usage:** KML XML polygon extraction, validity repair, AOI intersection, site point-in-polygon lookup and overlap with historical wards. **50** newer wards and **24** historical wards intersect the AOI. Eight candidate sites match each vintage; two Electronic City candidates retain unknown ward IDs. No demographic counts are apportioned through this geometric crosswalk.
- **Limits:** embedded `TOT_P` reference year is unverified and excluded. New ward IDs are not equivalent to Census IDs. Catalogue licence is Other (Public Domain). No current master feature depends numerically on the ward tables.

### 3.7 MoSPI HCES consumption expenditure

- **Provider:** Government of India, Ministry of Statistics & Programme Implementation, National Statistics Office. Manifest ID: `hces-2023-24`.
- **Actually used:** [NSS Report 592, HCES 2023–24](https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf). [Official factsheet](https://mospi.gov.in/sites/default/files/publication_reports/HCES%20FactSheet%202023-24.pdf) is archived for cross-checking. The 2022–23 report was downloaded as an alternative but does not supply the final basket.
- **Source locator/reference:** physical PDF page **90**, printed page **S11**, **Statement 3U, column 14, Karnataka Urban**. Survey reference **August 2023–July 2024**. Table values are INR per person per 30 days, without social-transfer imputation as labelled by the extraction. Total urban Karnataka MPCE is **INR 8,075.62**; food total **INR 3,041.91**. These are state survey estimates, not local grocery sales.
- **Processing:** `pypdf` extraction; parse final Karnataka numeric column; preserve item IDs, reference period, nominal price basis and table locator. The local category spending rate is items **1–13 + assumed 50% of item 14 + items 18 and 19 = INR 2,974.915/person/month**. Item 14 includes purchased cooked meals; items 18/19 are toiletries/household consumables. Transfer of the state urban mean to the corridor is also assumed. Annualize with ×12 and multiply by modelled catchment population.
- **Usage:** `expenditure_inputs`, grocery project assumption, spending-cell wallets, master `annual_wallet_inr` and `wallet_price_year`. State all-item MPCE is not copied directly as site demand. Price year 2024 denotes the ending year of nominal 2023–24 survey prices. Fictional costs are at a 2026 basis; no inflation factor was applied.
- **Failed/unused alternatives:** eSankhyiki catalogue, portal and alleged `Statement_4.xlsx` each returned a **1,198-byte HTML/JavaScript application shell**, supplying no numeric statistical records. The supposed XLSX is not a workbook. Microdata related-materials HTML supplied discovery information, not household microdata. The unsuccessful `Report_592_HCES_2023-24.pdf` path was replaced by the actual `Final_Report...` path.
- **Discrepancies:** the output has **31 rows rather than all 32 Statement 3U item numbers**. Multiline item **24**, consumer services excluding conveyance, was skipped by the line regex. Current grocery calculations do not use item 24, so the basket is unaffected; future all-item analysis must not assume a complete extract. Manifest release day **2025-01-31** is hardcoded and not established by an archived successful release-page record. PDF creation metadata says **2025-01-30**, which is not a publication date. Exact public-release day remains **unverified**.

### 3.8 Yellow Line official infrastructure evidence

- **Provider:** Prime Minister Office / Press Information Bureau, Government of India. Manifest ID: `yellow-official`.
- **Actual source:** [PIB statement PRID 2154848](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848), archived as `raw/official_yellow_opening.html`.
- **Reference:** official statement dated **2025-08-10** documents inauguration. It does not independently establish a separate first commercial passenger-service date; that field remains null.
- **Processing/usage:** preserve inauguration/status evidence and combine with historical station observations and OSM locations. Yellow is included in the current infrastructure baseline; nearest-metro provenance refers to this evidence through the station lookup. The HTML supplies neither station-hour traffic nor the station geometry.
- **Limits:** this is not measured retail uplift or verification of every access entrance at the 2026 snapshot. The build assigns `OPERATIONAL`/Yellow labels to matched corridor stations; no first-party operational GIS was downloaded. Inauguration evidence must not be presented as a newly observed commercial opening or demand measurement.

### 3.9 Blue Line government report and future scenario

- **Issuer:** Government of Karnataka, Economic Survey 2025–26. Immediate download provider: OpenCity mirror. Manifest ID: `blue-official`.
- **Actual document:** [archived Economic Survey download](https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf). Relevant locator: physical PDF page **181**, section **5.10.2**. Exact original issuer-hosted PDF URL and precise status observation date are not captured.
- **Collected:** Phase 2A/2B project descriptions, construction context and historical completion programmes, including a December 2026 Phase 2A programme. This is not a verified opening date or current commissioning certificate.
- **Processing/usage:** extract government text; keep project facts separate from partial OSM Phase 2A line segments. `infrastructure.csv` and `infrastructure_scenarios.csv` carry an **assumed** opening **2027-07-01**, a +24-month **2029-07-01** delay, and assumed **0.10** demand effect. None is applied to current baseline master features.
- **Additional discoveries:** actual operator homepage/upcoming/project-progress HTML and an OpenCity Phase 2A DPR catalogue were downloaded. DPR documents themselves were not fetched from that catalogue and must not be described as reviewed alignment documents. Initial operator paths returned 404.
- **Limits:** `status_reference_date=2026-10-24` in the output is a build snapshot date, partly contextualized by OSM construction tags, not a newly dated official government observation. Commercial opening remains unknown. Geometry is partial OSM alignment, not an official station-access map. Future dates/effects are assumptions, not official facts.

### 3.10 Magicbricks: retrieved, but no final financial benchmark

- **Provider:** Magicbricks commercial-property website. Manifest ID: `commercial-attempt`.
- **Actual page:** [Electronic City commercial rental listings](https://www.magicbricks.com/commercial-property-for-rent-in-electronic-city-bangalore-pppfr), archived locally as `raw/commercial_rent_attempt.html`.
- **Collection/reference:** HTML acquired **2026-10-24** and inspected for suitability. It contains mixed offices and distant/promoted listings. Verified available grocery premises, executed leases, candidate premises coordinates and comparable financial benchmarks were not established. Listing observation/availability dates remain unknown.
- **Final usage:** acquisition evidence only; **no numeric candidate/master rent, CAPEX, OPEX, margin or area is derived from these listings**. Those values remain engineering assumptions. No listing table was redistributed; proprietary HTML was excluded from the existing ZIP.

## 4. Internal assumptions and derived information

| Internal source ID | Origin | Use | Qualification |
|---|---|---|---|
| `approved-weights` | Existing `data/demo/weights.json` | 36 category/bin weights; six bins; 1,500m radius and 750m decay | Assumed engineering weights, not calibrated visitation |
| `assumptions` | User permission and literal/seeded builder choices | Hypothetical candidates/branches, financials, grocery eligibility/local transfer, missing hours/evidence, competitor unit mass, future dates/effects | Not an external empirical source |
| `package-config` | User-fixed configuration and builder metadata | IDs, snapshot date, Bengaluru/supermarket configuration, AOI, statuses and literal 6/8 score | Metadata/configuration, not measurements |

These three internal entries are not external data providers. The 14-row manifest therefore does not represent 14 independent external datasets. All nine external source groups in the summary supplied used data/context; Magicbricks is a separate unused commercial-data attempt. OSM POIs and roads are separate manifest IDs but one provider.

Business generation uses seed **20261024**; locality/coordinate anchors are fixed in `build_sites()`. Candidate area is seeded. Rent = area × **700 INR/sqm/month**, CAPEX = area × **18,000 INR/sqm**, annual OPEX excluding rent/COGS = area × **7,200 INR/sqm/year**, margin = **0.22**. These rates are uniform assumptions, not sourced benchmarks. Existing branches are fictional, with assumed attraction and contribution parameters.

Approved budget, projection horizon and discount defaults originate in `data/demo/project.json`; the output labels them as existing fixture assumptions but uses a generic assumptions source ID rather than a dedicated approved-project source. This is a provenance-detail gap, not independent financial evidence.

Daypart opportunity is:

`sum(category_weight × exp(-distance_metres/750) × availability × evidence_weight)` within 1,500m.

Recorded hours are conservatively parsed when supported; otherwise availability **0.5** and evidence **0.5** are assumed. Even the evidence weight for parsed schedules is an engineering choice, not a calibrated accuracy probability. Missing original opening hours remain null. Metro traffic is kept separate from the POI opportunity index.

## 5. All 50 master columns

**Origin legend:** D = derived from actual source records; D/modelled = derived from a published modelled population surface; A = assumed; S = synthetic demo; M = configuration/provenance metadata; U = unknown. D+A combines public inputs and assumptions. No column is an observed sales label.

CSV itself has no enforced storage types; populated values were checked against the logical types below. All other null counts are zero except the two explicitly unknown columns. This dictionary states meaningful units even where the existing lineage incorrectly says `text`; no original units/lineage were silently changed.

| # | Column | Meaning and source | Units | Logical type | Origin | Nulls / 10 |
|---:|---|---|---|---|---|---:|
| 1 | `site_id` | Stable candidate join key, site-01 through site-10; package-config. Keep as ID, not learned predictor. | identifier | string | M | 0 |
| 2 | `feature_snapshot_id` | Version of this prepared feature view; not a claim of simultaneous observations; package-config. | identifier | string | M | 0 |
| 3 | `snapshot_as_of_date` | User-fixed 2026-10-24 snapshot/valuation date; package-config. | ISO date | date | M | 0 |
| 4 | `city` | Configured Bengaluru geography; package-config. | city label | string | M | 0 |
| 5 | `locality` | Analyst-selected anchor label, not a verified shop address; assumptions/build_sites. | place label | string | S | 0 |
| 6 | `latitude` | Hypothetical candidate latitude selected in code, not surveyed premises GPS; assumptions. | decimal degrees WGS84 | float64 | S | 0 |
| 7 | `longitude` | Hypothetical candidate longitude selected in code; assumptions. | decimal degrees WGS84 | float64 | S | 0 |
| 8 | `store_format` | Configured supermarket format; package-config. | format label | category/string | M | 0 |
| 9 | `source_manifest_id` | Source manifest version/join ID, not an evidence score; package-config. | identifier | string | M | 0 |
| 10 | `store_size_sqm` | Seeded hypothetical area, 350–650 in 25 sqm increments; assumptions, seed 20261024. | sqm | float64 | S | 0 |
| 11 | `population_1500m_est` | 2020 WorldPop modelled population in metric circle via pixel area intersections and within-pixel uniform density; worldpop-2020. | estimated persons | float64 | D/modelled | 0 |
| 12 | `population_10min_est` | Intended network-time catchment population; no validated routing obtained. | estimated persons | nullable float64 | U | 10 |
| 13 | `accessible_households_est` | Intended accessible households; no defensible local persons-per-household denominator. | estimated households | nullable float64 | U | 10 |
| 14 | `annual_wallet_inr` | Unrounded population × INR 2,974.915/person/month ×12; WorldPop + HCES + grocery/local-transfer assumptions. Addressable category spending, not sales. | INR/year, nominal 2023–24 prices | float64 | D+A | 0 |
| 15 | `wallet_price_year` | 2024 encodes ending year of 2023–24 expenditure price period, not inflation adjustment; hces-2023-24. | year | int64 | D/M | 0 |
| 16 | `mean_wallet_weighted_distance_m` | Approximate population/wallet-weighted ellipsoidal distance to pixel/catchment-intersection centroids; worldpop-2020. Uniform spending makes weights proportional. Not road distance or exact within-pixel mean. | metres | float64 | D/modelled | 0 |
| 17 | `travel_time_method` | Explicit unavailable-routing label; circular catchment used; package-config. | method/status label | string | M | 0 |
| 18 | `competitor_count_1500m` | Retained mapped supermarkets, convenience and grocery competitors within 1,500m; osm-pois. Mapped zero is not verified absence. | mapped POI count | int64 | D | 0 |
| 19 | `competitor_attraction_index` | sum(exp(-geodesic distance/750)) over those competitors; equal unit attraction assumed; osm-pois + assumptions. No size/brand/sales calibration. | dimensionless relative index | float64 | D+A | 0 |
| 20 | `nearest_competitor_distance_m` | Minimum mapped competitor distance **inside 1,500m**, not unrestricted citywide nearest-shop search; osm-pois. | metres | nullable float64 | D | 0 |
| 21 | `office_poi_count_1500m` | Office-category mapped records; not employees/floor area; osm-pois. | mapped POI count | int64 | D | 0 |
| 22 | `education_poi_count_1500m` | Schools, colleges, universities and kindergartens; not students; osm-pois. | mapped POI count | int64 | D | 0 |
| 23 | `healthcare_poi_count_1500m` | Hospitals, clinics, doctors and pharmacies; not beds or distinct campuses; osm-pois. | mapped POI count | int64 | D | 0 |
| 24 | `transit_poi_count_1500m` | Stations, stops, platforms, entrances and stop positions; not deduplicated physical hubs; osm-pois. | mapped POI count | int64 | D | 0 |
| 25 | `shopping_poi_count_1500m` | Malls/department-store category; grocery competitors are separate; osm-pois. | mapped POI count | int64 | D | 0 |
| 26 | `food_leisure_poi_count_1500m` | Restaurants, cafes, fast food, food courts, cinema/theatre and leisure-tagged features; osm-pois. | mapped POI count | int64 | D | 0 |
| 27 | `weekday_morning_raw` | Monday–Friday starting 06:00–11:00, 5h, POI opportunity formula; osm-pois + approved-weights + assumed availability/evidence. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 28 | `weekday_lunch_raw` | Monday–Friday 11:00–15:00, 4h; same source/formula. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 29 | `weekday_evening_raw` | Monday–Friday 15:00–20:00, 5h; same source/formula. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 30 | `weekday_night_raw` | Monday–Friday starting 20:00, ending next day 06:00, 10h; same sources. Overnight belongs to starting day. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 31 | `weekend_day_raw` | Saturday–Sunday 06:00–18:00, 12h; same source/formula. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 32 | `weekend_evening_raw` | Saturday–Sunday starting 18:00, ending next day 06:00, 12h; same sources. | relative opportunity per nominal hour | float64 | D+A | 0 |
| 33 | `nearest_metro_station_id` | Nearest matched operational corridor station ID; osm-pois + metro-rti + yellow-official. Join key, not learned location outcome. | identifier | string | D | 0 |
| 34 | `nearest_metro_distance_m` | Ellipsoidal WGS84 distance to that station point, not walking time/entrance routing; same sources. | metres | float64 | D | 0 |
| 35 | `metro_weekday_entries_per_hour` | Nearest-station September 2025 mean entries over 528 observed clock hours on 22 weekdays; night zeros retained; metro-rti. | reported passengers/observed clock hour | float64 | D/historical | 0 |
| 36 | `metro_weekday_exits_per_hour` | September 2025 exit mean over same paired valid weekday intervals; metro-rti. | reported passengers/observed clock hour | float64 | D/historical | 0 |
| 37 | `metro_weekend_entries_per_hour` | September 2025 entry mean over 192 observed clock hours on 8 weekend days; metro-rti. | reported passengers/observed clock hour | float64 | D/historical | 0 |
| 38 | `metro_weekend_exits_per_hour` | September 2025 exit mean over same paired valid weekend intervals; metro-rti. | reported passengers/observed clock hour | float64 | D/historical | 0 |
| 39 | `metro_measurement_start_date` | Full aggregate window begins 2025-09-01; day-type-specific observed dates remain in supporting averages; metro-rti. | ISO date | date | D/M | 0 |
| 40 | `metro_measurement_end_date` | Full window ends 2025-09-30; not a current traffic/retrieval date; metro-rti. | ISO date | date | D/M | 0 |
| 41 | `daypart_data_status` | DERIVED_ASSUMED_OPPORTUNITY_PROXY; not measured footfall; package-config. | status label | category/string | M | 0 |
| 42 | `poi_data_status` | OSM_PARTIAL_COVERAGE_MAPPED_COUNTS; completeness unverified; package-config. | status label | category/string | M | 0 |
| 43 | `population_data_status` | HISTORICAL_MODELLED_PROXY_2020; text, not a persons quantity; package-config. | status label | category/string | M | 0 |
| 44 | `ridership_data_status` | HISTORICAL_PROXY_2025_09; no fabricated 2026 traffic; package-config. | status label | category/string | M | 0 |
| 45 | `comp_data_status` | Partial coverage, mapped-zero semantics and equal-attraction assumption; package-config. | status label | string | M | 0 |
| 46 | `monthly_rent_inr` | Synthetic area × INR 700/sqm/month; not a verified lease/comparable; assumptions. | INR/month, 2026-10-24 demo basis | float64 | S/A | 0 |
| 47 | `capex_inr` | Synthetic area × INR 18,000/sqm upfront; assumptions. | INR upfront, 2026-10-24 demo basis | float64 | S/A | 0 |
| 48 | `annual_opex_excl_rent_inr` | Synthetic area × INR 7,200/sqm/year, excluding rent and COGS; assumptions. | INR/year, 2026-10-24 demo basis | float64 | S/A | 0 |
| 49 | `gross_margin_fraction` | Assumed 0.22 at all sites, a fraction, not 22 or net margin; assumptions. | fraction 0–1 | float64 | A | 0 |
| 50 | `source_quality_score` | Literal 6/8 = 0.75 for every site, described as evidence-family availability. Not dynamically computed per site or calibrated confidence; package-config. | fraction 0–1 | float64 | A/M; lineage says D | 0 |

Persisted lineage counts **400 DERIVED, 80 SYNTHETIC_ASSUMED, 20 UNRESOLVED_MISSING** of 500 cells. The 400 category includes metadata and derived-with-assumptions values; it is not an 80% observed-data claim. This dictionary refines interpretation without rewriting the original lineage.

## 6. Relationship of all 27 CSV tables to the master

The code calls `build_master(sites, pixels, pois, stations, averages, raws, grocery)` using **in-memory objects**. It does not read/join all 27 output CSVs. “Direct-equivalent” below means an exported view of objects directly used, rather than a claim that the CSV was loaded back as an input.

| CSV under data/bengaluru/final/ | Shape | Relationship | Actual contribution / safe treatment |
|---|---:|---|---|
| `acquisition_files.csv` | 57 × 9 | Audit only | URLs, status, request time and hashes; not predictors |
| `candidate_sites.csv` | 10 × 17 | Direct-equivalent | Candidate identity/coordinates/locality, area and synthetic costs/margin |
| `census_2011_wards.csv` | 198 × 15 | Historical context only | Historical ward statistics, not master catchment population |
| `daypart_profiles.csv` | 60 × 15 | Direct-equivalent | Six raw values; current master omits shares, exposures and support counts |
| `daypart_weights.csv` | 36 × 14 | Indirect | Approved assumed matrix and bin definitions used in opportunity |
| `existing_stores.csv` | 4 × 10 | Separate downstream network | Fictional company branches excluded from baseline reference-demand features |
| `expenditure_inputs.csv` | 31 × 13 | Indirect | HCES values used for grocery spending rate, not observed site spending |
| `field_lineage.csv` | 797 × 11 | Audit only | 500 master field entries and supporting wildcard entries |
| `infrastructure.csv` | 2 × 18 | Separate scenario/context | Yellow operational context; Blue future assumptions not numeric baseline features |
| `infrastructure_scenarios.csv` | 3 × 10 | Separate scenario axis | Current/opens/delayed are not extra independent training examples |
| `metro_activity_averages.csv` | 26 × 11 | Direct-equivalent | Four nearest-station day-type means; source denominators currently omitted |
| `metro_date_coverage.csv` | 793 × 7 | QC, not yet incorporated | Calendar/measurement coverage; unreported dates are not zero traffic |
| `metro_daypart_coverage.csv` | 3,526 × 11 | Not yet incorporated | Potential historical bin-specific traffic and complete-bin support |
| `metro_hourly.csv` | 11,976 × 17 | Indirect | Observations underpin averages/coverage; do not join individual hours directly into site rows |
| `metro_station_lookup.csv` | 13 × 14 | Direct-equivalent | Operational coordinates/IDs for nearest assignment and traffic joins |
| `missing_fields.csv` | 56,290 × 9 | Audit only | Generation/null classification and reasons |
| `poi_daypart_availability.csv` | 28,656 × 8 | Indirect | Recorded/assumed schedule availability and evidence weights |
| `poi_deduplication.csv` | 264 × 3 | Cleaning audit | Already reflected in retained POIs; do not count dropped records again |
| `pois.csv` | 4,995 × 18 | Direct and indirect | Counts/competition, station matching and opportunity input |
| `project_assumptions.csv` | 24 × 7 | Parameter/context view | Corresponding builder values govern parameters; exported CSV is not read by build_master |
| `schema_mapping.csv` | 55 × 5 | Integration metadata | Canonical names/units, not observations |
| `site_features.csv` | 10 × 50 | Master output | Not another independent input source |
| `site_ward_lookup.csv` | 10 × 8 | Not yet incorporated | All site keys present; ward attributes populated for only 8/10 sites |
| `source_manifest.csv` | 14 × 13 | Provenance/version | Source declarations/manifest ID; score 6/8 is not calculated from manifest rows |
| `spending_cells.csv` | 100 × 17 | Parallel output / network | Shares raw raster/spending transformations; master population uses pixels directly. Keep each network wallet once |
| `synthetic_assumptions.csv` | 56,235 × 15 | Assumption register | Generated values/ranges are not independent empirical training cases |
| `ward_crosswalk.csv` | 163 × 13 | Historical context | Geometry overlap only; not validated population redistribution |

GeoTIFF and GeoJSON/KML layers retain spatial relationships that a CSV-only flattening would lose. The pixel raster supports catchment geometry; ward polygons support vintage-specific lookup; transport lines support future geometry-derived descriptors.

## 7. Consolidated site-level enrichment: feasible, not exported

A single versioned **site-feature view** can be created with one row per candidate after aggregating/pivoting relevant supporting data to `(site_id, feature_snapshot_id)` and joining nearest-station summaries many-to-one. It remains a feature/demo inference package, **not** a supervised learning dataset: no valid sales targets exist, and the ten candidate locations are hypothetical.

A concrete **in-memory** check retained every original field and produced **10 × 70 with 24 nulls**: the original 20 unknowns plus four missing ward IDs for site-09 and site-10. No file was exported. `data/bengaluru/final/site_features_enriched.csv` is a possible future output path and **was not created** under this report-only instruction.

| Additional proposed features | Count | Transformation and sources | Join coverage / safeguards |
|---|---:|---|---|
| `{bin}_weekly_exposure_share` for all six canonical bins | 6 | Pivot daypart_profiles; raw × duration × starting days / total weekly exposure | 10/10 sites; float fractions sum to 1; retain assumed-proxy status |
| `daypart_poi_support_count`, `daypart_recorded_hours_support_count`, `daypart_assumed_hours_support_count` | 3 | Select common profile support count after equality check across six bins; do not sum across bins | 10/10; integer; recorded + assumed = total |
| `daypart_recorded_hours_fraction` | 1 | Recorded-hours support / total supporting POIs | 10/10 have support; float fraction; otherwise null, not confidence |
| `mapped_supermarket_count_1500m`, `mapped_convenience_count_1500m`, `mapped_grocery_count_1500m` | 3 | Reaggregate deduplicated competitor POIs by shop tag within geodesic 1,500m | 10/10; counts sum to current competitor count; mapped zero remains qualified |
| `operational_metro_station_count_1500m` | 1 | Count matched operational station points within geodesic 1,500m | 10/10; do not count individual entrances/platforms as stations |
| `ward_2011_id`, `ward_2025_id` | 2 | Left join site_ward_lookup; preserve different vintages | 8/10 populated per field; categorical IDs, four missing cells preserved |
| `metro_sep2025_weekday_observation_hours`, `metro_sep2025_weekday_observed_days`, `metro_sep2025_weekend_observation_hours`, `metro_sep2025_weekend_observed_days` | 4 | Pivot metro_activity_averages by day_type, then join nearest station | 10/10; integers; 528/22 and 192/8 are constant coverage metadata, not useful learned predictors here |

The six share prefixes expand to `weekday_morning`, `weekday_lunch`, `weekday_evening`, `weekday_night`, `weekend_day`, `weekend_evening`. The 20 additions use existing records and arithmetic; they introduce no target, future uplift, new commercial assumption, or duplicate location.

### Further useful information not incorporated

- **Metro activity by daypart:** aggregate September `metro_daypart_coverage` separately for entries/exits using only complete paired bins: sum observed counts / sum observed hours, retaining complete-bin counts. Overnight bins use starting local dates; partial end-of-month nights must not become complete observations. This could supply 12 direction/bin rates with coverage, but was not materialized here.
- **Weekly opportunity exposure:** six `weekly_opportunity_exposure` values can support display/comparison. These are deterministic rescalings of raw values, not independent evidence. Account for unequal bin lengths and five weekday versus two weekend starting days.
- **Schedule/source coverage and category mix:** availability and original OSM tags support parsed-versus-assumed coverage by category/bin, food/leisure subcategories and distance-decayed support. Some counts are algebraically related to existing features.
- **Transport geometry:** clipped road/footway length or intersection descriptors may be useful after access, direction, overlap and topology checks. Such geometry is not validated ten-minute routing; do not invent speeds/travel-time catchments.
- **Historical demographics:** keep 2011 housing/assets and ward statistics with explicit historical/ward-scale labels and validated code correspondence. Do not copy whole-ward population or SC/ST counts into site catchment demand, derive households from percentage tables, or treat geometry overlap as a calibrated population crosswalk.
- **Provenance descriptors:** original population year, price period, raster resolution and extraction times improve reproducibility. Most are constant metadata. New smaller-radius population measures require source-pixel intersections, not arbitrary fractions of the 1,500m circle.

Do not flatten source logs, source-manifest rows, every POI/hour, 100 network wallets, fictional branches or three infrastructure states into repeated site rows. Keep scenario and network relationships separate. Own-branch proximity belongs to the later network engine under the approved architecture, not baseline reference-sales predictors. Hypothetical Blue effects cannot be current observations.

## 8. Audit outcomes and discrepancies

### Verified outcomes

- Master: **10 unique site IDs, 10 distinct coordinate pairs, 50 columns, 20 nulls**. Candidate IDs/coordinates match candidate_sites.
- Populated numeric cells parse as finite numbers; count/year columns are integral; date columns are ISO dates. Financial amounts are nonnegative and margins bounded. Unknowns are preserved, not replaced by zero.
- All sites and full 1,500m metric catchments lie within the analyst AOI. All nearest-station assignments were recomputed geodesically and match; **9 distinct stations** are used by the ten sites.
- All **27 CSVs** match saved quality-report dimensions, null counts and SHA-256 hashes. All **47 archived responses with recorded hashes** match. Checksums establish snapshot integrity, not ground truth.
- All **500** master field/record lineage entries exist uniquely, and all lineage **source IDs** resolve.
- Each site has exactly six profile bins; the daypart pivot covers 10/10. Station lookup/day-type joins cover 10/10. Site ward keys cover 10/10, but ward attributes match only **8/10** for each vintage.
- In-memory enrichment is **10 × 70, 24 nulls**, with no duplicate IDs, no multiplication of sites, six shares summing to one, and competitor subcounts matching existing totals. No enriched CSV was written.

### Discrepancies flagged without rewriting existing artifacts

1. **Lineage units are not consistently semantic.** Count columns, six numeric raw opportunity columns, wallet_price_year and accessible_households_est are labelled text in the master lineage; population_data_status is incorrectly labelled persons. The dictionary above documents meaningful units/types. No silent repair was applied.
2. **Locality assumption reference is missing.** All ten locality lineage entries reference `candidate-locality`, which is absent from both synthetic_assumptions and project_assumptions. Fixed locality anchors are inspectable in build_sites, but the register linkage is incomplete. The previous source-ID test does not check this assumption foreign key.
3. **HCES item 24 is skipped.** The 31-row extract omits the multiline consumer-services item. This does not affect the current grocery basket, but matters before reusing the output as a complete expenditure table.
4. **HCES exact release day is not verified.** The manifest’s 2025-01-31 is a builder constant. Archived successful statistical PDFs and failed app-shell alternatives do not establish the exact public-release day. PDF creation metadata is not public release. Preserve this as unresolved, rather than guessing a replacement.
5. **WorldPop metadata is for a related product.** The successful API describes 100m data; the used TIFF is aggregated 1km. Year, file, resolution and licence are inspectable; exact aggregated-product release is not.
6. **A newer ward file has a misleading local filename.** BBMP_198.geojson contains the unused 243-ward layer. The actual historical input is the separately acquired BBMP_2012_198.geojson, as confirmed by README and the selected build path.
7. **Official status and processing dates differ.** The Blue output’s snapshot/status-verification date is not a fresh official commissioning observation. Government historical context, OSM construction geometry, assumed scenario dates and verified openings remain separate. Yellow inauguration is not independently verified first commercial service.
8. **Source quality is fixed metadata.** The literal 0.75 does not measure site-specific schedule coverage, licensing certainty or accuracy. It must not be called 75% confidence, 75% observed evidence or used as a calibrated ranking metric.
9. **Derived-value counts are not observation percentages.** The old 400/80/20 counts include metadata and assumed transformations within DERIVED. WorldPop is itself modelled, and mapped POIs are not verified premises. Supporting wildcard lineage is coarser than full cell-level provenance.
10. **Saved acquisition scripts do not cover every request.** Core download/retry stages are scripted. Additional successful requests, including historical DataMeet files, discovered operator pages, shop-only query and commercial page, are logged and archived but not all implemented in the saved acquisition-stage scripts. Frozen-source offline reproduction is supported; complete one-command live refresh is not demonstrated.
11. **Acquisition timestamps and catalogue dates need correct interpretation.** Request-start time is not completion; metadata-created/modified or Last-Modified is not necessarily release; full-calendar-year ranges can be reference-year placeholders rather than exact observation dates.
12. **Original delivery chains and usage terms have gaps.** Known mirror/repository URLs are listed honestly; missing original government/RTI delivery URLs are not guessed. Metro ODbL versus non-commercial metadata is unresolved. Download integrity alone does not resolve terms or original authority verification.

### Daypart source coverage at each site

| Site | Supporting POIs | Recorded-hours support | Assumed-hours support | Recorded-hours fraction |
|---|---:|---:|---:|---:|
| site-01 | 544 | 24 | 520 | 4.41% |
| site-02 | 441 | 20 | 421 | 4.54% |
| site-03 | 462 | 27 | 435 | 5.84% |
| site-04 | 284 | 19 | 265 | 6.69% |
| site-05 | 124 | 4 | 120 | 3.23% |
| site-06 | 128 | 6 | 122 | 4.69% |
| site-07 | 122 | 3 | 119 | 2.46% |
| site-08 | 131 | 5 | 126 | 3.82% |
| site-09 | 249 | 20 | 229 | 8.03% |
| site-10 | 206 | 19 | 187 | 9.22% |

Only about **2.46%–9.22%** of each site’s supporting POIs have schedules parsed from recorded hours, so the opportunity profile materially depends on assumed hours/evidence. Financial amounts are exact area multiples; annual_wallet is proportional to population under one uniform spending rate. **18 master columns are constant**, including two wholly null columns. Fifty or seventy columns are not fifty or seventy independent empirical signals. The 11,976 metro intervals are not independent retail-sales-labelled site examples.

## 9. Next steps for RetailIQ site ranking and DaypartDNA

1. **Resolve provenance in a separately authorized revision:** verify the HCES release record, register locality assumptions, correct lineage units, explicitly identify approved-project defaults, and restore the skipped multiline HCES item. Preserve this snapshot’s evidence rather than silently replacing it.
2. **Define a versioned site-feature view:** use candidate/snapshot identity as the spine, validate cardinality before joining, pivot validated six-bin profiles, attach coverage and historical periods, and preserve nulls. The tested 20 additions are a concrete option; categorical IDs, constant QC fields and algebraically redundant rescalings need not be learned predictors.
3. **Build DaypartDNA as a disclosed opportunity component:** show six raw values alongside duration/frequency-weighted shares, category contributors and parsed-versus-assumed coverage. Test Friday/Saturday and Sunday/Monday overnight boundaries. Keep historical metro traffic in a separate evidence channel and use complete-bin denominator accounting. Do not label the POI proxy measured footfall.
4. **Obtain permissioned outcomes before supervised learning:** collect comparable store sales with exact measurement periods, format/area, openings and geographic context aligned to feature snapshots. Do not synthesize sales targets, use category wallets as sales labels, treat hypothetical candidates as observed outcomes, or train on these ten rows. Only after valid outcomes exist should a target and spatial/time/group validation design be established.
5. **Integrate ranking through the approved pipeline later:** exclude own-branch proximity and post-opening outcomes from reference-demand inference; retain one copy of each cell wallet for the network engine; keep future scenarios dated/separate; align 2023–24 wallets with 2026 costs using verified indices or explicit mismatch mode. Economic ranking awaits the actual demand/network/finance stages; synthetic costs and source-quality metadata do not establish real investment returns.
6. **Improve material source coverage:** obtain validated routing, a defensible household denominator, verified grocery premises/commercial inputs, and better facility/entrance deduplication. Resolve metro commercial terms where relevant. Each new source needs an exact URL, original observation/reference period, retrieval evidence, licence and transformation lineage.

## Appendix A. Exact acquisition ledger

The following ledger is generated from the existing acquisition_log.json, not from guessed citations. It includes successes, unused alternatives, metadata-only records, unusable HTTP 200 responses and failures. Exact query parameters are retained. Local paths are relative to the repository root, `C:\Users\Office Pc\OneDrive\Documents\Elites-`.

| Status | Local raw path | Request start UTC | Exact requested URL | Outcome / usage note |
|---|---|---|---|---|
| DOWNLOADED | `data/bengaluru/raw/github_tree.json` | 2026-10-24T14:14:25.677016+00:00 | [Exact URL](<https://api.github.com/repos/Vonter/bmrcl-ridership-hourly/git/trees/main?recursive=1>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/ridership_README.md` | 2026-10-24T14:14:25.679957+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/README.md>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/ridership_DATA.md` | 2026-10-24T14:14:25.681951+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/DATA.md>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/ridership_LICENSE.txt` | 2026-10-24T14:14:25.683956+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/main/LICENSE>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/opencity_metro_metadata.json` | 2026-10-24T14:14:25.684956+00:00 | [Exact URL](<https://data.opencity.in/api/3/action/package_show?id=bmrcl-station-wise-ridership-data>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/opencity_census_metadata.json` | 2026-10-24T14:14:25.700045+00:00 | [Exact URL](<https://data.opencity.in/api/3/action/package_show?id=bengaluru-census-2011>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/opencity_wards_metadata.json` | 2026-10-24T14:14:26.157103+00:00 | [Exact URL](<https://data.opencity.in/api/3/action/package_show?id=gba-wards-delimitation-2025>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/worldpop_metadata.json` | 2026-10-24T14:14:26.170008+00:00 | [Exact URL](<https://www.worldpop.org/rest/data/pop/wpgp?iso3=IND>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/population/ind_ppp_2020_1km_Aggregated_UNadj.tif` | 2026-10-24T14:14:26.288791+00:00 | [Exact URL](<https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif>) | Archived; actual use described in source detail |
| UNUSABLE_HTML_APP_SHELL | `data/bengaluru/raw/hces_catalogue.html` | 2026-10-24T14:14:26.300480+00:00 | [Exact URL](<https://esankhyiki.mospi.gov.in/catalogue-main/catalogue?product=HCES>) | HTTP 200 returned a 1198-byte JS application shell, not a data table. |
| DOWNLOADED | `data/bengaluru/raw/hces_related_materials.html` | 2026-10-24T14:14:26.306482+00:00 | [Exact URL](<https://microdata.gov.in/nada/index.php/catalog/237/related-materials>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/hces_2022_23.pdf` | 2026-10-24T14:14:26.317465+00:00 | [Exact URL](<https://www.mospi.gov.in/sites/default/files/publication_reports/Report_591_HCES_2022-23New.pdf>) | Discovery, metadata or unused alternative; see source detail |
| FAILED | `data/bengaluru/raw/bmrcl_home.html` | 2026-10-24T14:14:26.381202+00:00 | [Exact URL](<https://bmrc.co.in>) | HTTP Error 404: Not Found |
| DOWNLOADED | `data/bengaluru/raw/metro/data_station-hourly.csv.zip` | 2026-10-24T14:15:43.407433+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/data/station-hourly.csv.zip>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/data_station-hourly-exits.csv.zip` | 2026-10-24T14:15:43.408819+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/data/station-hourly-exits.csv.zip>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/raw_station-codes.csv` | 2026-10-24T14:15:43.410838+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/station-codes.csv>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/raw_station-names.csv` | 2026-10-24T14:15:43.411827+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/station-names.csv>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/raw_august_station-hourly.xlsx` | 2026-10-24T14:15:43.412830+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/august/station-hourly.xlsx>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/raw_september_station-hourly.xlsx` | 2026-10-24T14:15:43.485366+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/raw/september/station-hourly.xlsx>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/parse.py` | 2026-10-24T14:15:43.548043+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/parse.py>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/metro/CITATION.cff` | 2026-10-24T14:15:43.961825+00:00 | [Exact URL](<https://raw.githubusercontent.com/Vonter/bmrcl-ridership-hourly/6c44579b5ff3428a88bddc44baf84e436a940612/CITATION.cff>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/census/4efdf9f5-5790-41ca-ac68-13691b31f364.csv` | 2026-10-24T14:15:43.977870+00:00 | [Exact URL](<https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/4efdf9f5-5790-41ca-ac68-13691b31f364/download/a7c8acc4-6540-4152-9fee-aa084baac188.csv>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/census/4bd82527-84a1-45ae-b695-5ed0c0ecbd85.csv` | 2026-10-24T14:15:43.997833+00:00 | [Exact URL](<https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/4bd82527-84a1-45ae-b695-5ed0c0ecbd85/download/f00519ff-7932-4c94-ba8f-654978f1a03a.csv>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/census/269cdf01-dae5-4736-8f4d-72a8e57fa3a9.csv` | 2026-10-24T14:15:44.092957+00:00 | [Exact URL](<https://data.opencity.in/dataset/023a1c0c-1901-4eb1-b1bf-66a900485099/resource/269cdf01-dae5-4736-8f4d-72a8e57fa3a9/download/83390055-d933-420f-82b7-608e139336c2.csv>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/wards/9013d656-8051-4e2d-9648-46efd0d86d3d.kml` | 2026-10-24T14:15:44.098951+00:00 | [Exact URL](<https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/wards/dbe57ae6-a72f-426e-917b-e55b3b22a87b.kml` | 2026-10-24T14:15:44.102967+00:00 | [Exact URL](<https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/dbe57ae6-a72f-426e-917b-e55b3b22a87b/download/1c5bbd4e-006c-4130-b278-fd6680fef91b.kml>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/official_yellow_opening.html` | 2026-10-24T14:15:44.160978+00:00 | [Exact URL](<https://www.pib.gov.in/PressReleasePage.aspx?PRID=2154848>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/hces_2023_24_factsheet.pdf` | 2026-10-24T14:15:44.253944+00:00 | [Exact URL](<https://mospi.gov.in/sites/default/files/publication_reports/HCES%20FactSheet%202023-24.pdf>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/worldpop_licence.txt` | 2026-10-24T14:15:44.324943+00:00 | [Exact URL](<https://hub.worldpop.org/data/licence.txt>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/worldpop_1km_metadata.html` | 2026-10-24T14:15:44.442496+00:00 | [Exact URL](<https://hub.worldpop.org/geodata/listing?id=64>) | Discovery, metadata or unused alternative; see source detail |
| FAILED | `data/bengaluru/raw/bmrcl_project_status.html` | 2026-10-24T14:15:44.539039+00:00 | [Exact URL](<https://english.bmrc.co.in/project-status/>) | HTTP Error 404: Not Found |
| FAILED | `data/bengaluru/raw/bmrcl_blue_profile.html` | 2026-10-24T14:15:44.732072+00:00 | [Exact URL](<https://english.bmrc.co.in/project-profile-phase-2a-and-phase-2b/>) | HTTP Error 404: Not Found |
| DOWNLOADED | `data/bengaluru/raw/osm_copyright.html` | 2026-10-24T14:15:44.879015+00:00 | [Exact URL](<https://www.openstreetmap.org/copyright>) | Archived; actual use described in source detail |
| UNUSABLE_HTML_APP_SHELL | `data/bengaluru/raw/hces_portal.html` | 2026-10-24T14:15:44.952520+00:00 | [Exact URL](<https://esankhyiki.mospi.gov.in>) | HTTP 200 returned a 1198-byte JS application shell, not a data table. |
| FAILED | `data/bengaluru/raw/census_portal.html` | 2026-10-24T14:15:44.955524+00:00 | [Exact URL](<https://censusindia.gov.in>) | <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)> |
| FAILED | `data/bengaluru/raw/osm_overpass.json` | 2026-10-24T14:15:45.010694+00:00 | [Exact URL](<https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A150%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Bhighway~%22motorway%7Ctrunk%7Cprimary%7Csecondary%7Ctertiary%7Cresidential%7Cunclassified%7Cservice%7Cfootway%7Cpedestrian%7Cpath%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Brailway~%22subway%7Cconstruction%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%20geom%3B>) | HTTP Error 502: Bad Gateway |
| FAILED | `data/bengaluru/raw/osm_pois.json` | 2026-10-24T14:21:54.931507+00:00 | [Exact URL](<https://overpass.kumi.systems/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%3B>) | The read operation timed out |
| DOWNLOADED | `data/bengaluru/raw/osm_roads.json` | 2026-10-24T14:21:54.934455+00:00 | [Exact URL](<https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28way%5Bhighway~%22motorway%7Ctrunk%7Cprimary%7Csecondary%7Ctertiary%7Cresidential%7Cunclassified%7Cservice%7Cfootway%7Cpedestrian%7Cpath%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bway%5Brailway~%22subway%7Cconstruction%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20tags%20geom%3B>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/bmrcl_home_alternative.html` | 2026-10-24T14:21:54.935453+00:00 | [Exact URL](<https://english.bmrc.co.in/>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/official_economic_survey_2025_26.pdf` | 2026-10-24T14:21:54.936452+00:00 | [Exact URL](<https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf>) | Archived; actual use described in source detail |
| FAILED | `data/bengaluru/raw/hces_2023_24_report.pdf` | 2026-10-24T14:21:55.029894+00:00 | [Exact URL](<https://mospi.gov.in/sites/default/files/publication_reports/Report_592_HCES_2023-24.pdf>) | HTTP Error 404: Not Found |
| UNUSABLE_HTML_APP_SHELL | `data/bengaluru/raw/hces_statement_4.xlsx` | 2026-10-24T14:21:55.053001+00:00 | [Exact URL](<https://esankhyiki.mospi.gov.in/datacatalogue/HCES/2023-24/Factsheet/Statement_4.xlsx>) | HTTP 200 returned a 1198-byte JS application shell, not a data table. |
| FAILED | `data/bengaluru/raw/worldpop_1km_api.json` | 2026-10-24T14:21:55.254658+00:00 | [Exact URL](<https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND>) | HTTP Error 500: Internal Server Error |
| DOWNLOADED | `data/bengaluru/raw/osm_pois_alternative.json` | 2026-10-24T14:24:05.354417+00:00 | [Exact URL](<https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A90%5D%3B%28nwr%5Bshop~%22supermarket%7Cconvenience%7Cgrocery%7Cmall%7Cdepartment_store%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Boffice%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bamenity~%22school%7Ccollege%7Cuniversity%7Ckindergarten%7Chospital%7Cclinic%7Cdoctors%7Cpharmacy%7Cbus_station%7Crestaurant%7Ccafe%7Cfast_food%7Cfood_court%7Ccinema%7Ctheatre%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Brailway~%22station%7Chalt%7Csubway_entrance%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bpublic_transport~%22station%7Cplatform%7Cstop_position%22%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bhighway%3Dbus_stop%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3Bnwr%5Bleisure%5D%2812.815%2C77.600%2C12.940%2C77.725%29%3B%29%3Bout%20center%20tags%3B>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/hces_2023_24_full.pdf` | 2026-10-24T14:24:05.357409+00:00 | [Exact URL](<https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf>) | Archived; actual use described in source detail |
| DOWNLOADED | `data/bengaluru/raw/blue_dpr_metadata.json` | 2026-10-24T14:24:05.357409+00:00 | [Exact URL](<https://data.opencity.in/api/3/action/package_show?id=bengaluru-metro-phase-2a-documents>) | Discovery, metadata or unused alternative; see source detail |
| FAILED | `data/bengaluru/raw/worldpop_1km_api_retry.json` | 2026-10-24T14:24:05.360943+00:00 | [Exact URL](<https://www.worldpop.org/rest/data/pop/wpgpunadj1km?iso3=IND>) | HTTP Error 500: Internal Server Error |
| DOWNLOADED | `data/bengaluru/raw/osm_shops.json` | 2026-10-24T14:25:08.060680+00:00 | [Exact URL](<https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A60%5D%3Bnwr%5Bshop%5D%2812.815%2C77.60%2C12.94%2C77.725%29%3Bout%20center%20tags%3B>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/commercial_rent_attempt.html` | 2026-10-24T14:25:08.062679+00:00 | [Exact URL](<https://www.magicbricks.com/commercial-property-for-rent-in-electronic-city-bangalore-pppfr>) | Retrieved but no verified grocery premise or benchmark; no financial values used; excluded from old ZIP |
| DOWNLOADED | `data/bengaluru/raw/bmrcl_upcoming.html` | 2026-10-24T14:25:45.837768+00:00 | [Exact URL](<https://english.bmrc.co.in/upcoming-projects/>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/bmrcl_progress.html` | 2026-10-24T14:25:45.840754+00:00 | [Exact URL](<https://english.bmrc.co.in/dpr-project-progress/>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/old_ward_search.json` | 2026-10-24T14:26:26.075019+00:00 | [Exact URL](<https://data.opencity.in/api/3/action/package_search?q=bbmp%20ward%20boundaries>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/old_ward_github.json` | 2026-10-24T14:26:26.447641+00:00 | [Exact URL](<https://api.github.com/repos/datameet/Municipal_Spatial_Data/contents/Bangalore>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/wards/BBMP_198.geojson` | 2026-10-24T14:27:20.700348+00:00 | [Exact URL](<https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP.geojson>) | Discovery, metadata or unused alternative; see source detail |
| DOWNLOADED | `data/bengaluru/raw/wards/datameet_Readme.md` | 2026-10-24T14:27:20.701344+00:00 | [Exact URL](<https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/Readme.md>) | Archived; actual use described in source detail |
| FAILED | `data/bengaluru/raw/datameet_LICENSE` | 2026-10-24T14:27:20.703341+00:00 | [Exact URL](<https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/LICENSE>) | HTTP Error 404: Not Found |
| DOWNLOADED | `data/bengaluru/raw/wards/BBMP_2012_198.geojson` | 2026-10-24T14:27:47.504553+00:00 | [Exact URL](<https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP_oldWards.geojson>) | Archived; actual use described in source detail |

## Appendix B. Original URLs and dates that remain unverified

- **Census:** original first-party data-file URL and release day are not captured; actual OpenCity CSV/API URLs are known.
- **GBA:** original authority-hosted KML URL and exact publication day are not captured; actual mirror and December 2025 resource vintage are known.
- **Karnataka Economic Survey:** original issuer-hosted PDF URL and precise project status observation date are not captured; actual mirrored PDF and report identity are known.
- **BMRCL:** certified original RTI delivery URL and response-chain dates are not captured; actual GitHub revision/workbooks, publisher-described provenance and measured service dates are known.
- **WorldPop:** exact aggregated-product release day is unverified; downloaded TIFF URL, model year, grid, licence text and hash are known. Related 100m metadata does not resolve this.
- **DataMeet:** historic layer’s exact release day and original authority file URL are unverified; repository input and README vintage/licence are known.
- **HCES:** manifest’s exact 2025-01-31 public-release day is not independently established by archived successful records. Survey period and actual official PDF URL are verified; file creation is not release.
- **OSM:** individual feature survey/edit dates were not collected; database snapshot times are known.
- **Magicbricks:** individual listing observation/availability dates are unverified. Acquisition date does not establish availability.
- **Synthetic assumptions/fixtures:** these have no external observation date or external empirical URL. User specification/repository fixture is the honest origin.

## Appendix C. Reproducibility and unchanged outputs

Inspected: source_manifest, all 797 lineage entries, completion/quality reports, all 27 CSVs, original acquisition log, every archived response with a recorded checksum, source metadata/README/licences, workbook/PDF-derived records, build configuration and seven source scripts. `build.py` and `validate.py` were not rerun because they rewrite existing deliverables.

Source scripts: `ml/bengaluru/acquire.py`, `acquire_detail.py`, `acquire_retry.py`, `acquire_final.py`, `inspect_data.py`, `build.py`, `validate.py`. The acquire stages download records, inspect_data extracts PDF text, build prepares features/assumptions/lineage, and validate creates the original quality report/ZIP. Appendix A identifies actual requests even where the saved scripts lack a corresponding fetch step.

**Only new output:** `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\reports\data_sources_for_presentation.md`.

Existing outputs, unchanged:

- Master: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\final\site_features.csv`, **10 × 50, 20 nulls**.
- Lineage: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\final\field_lineage.csv`, **797 × 11**.
- Completion: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\reports\completion_report.md`.
- Quality: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\reports\data_quality_report.json`.
- Existing ZIP: `C:\Users\Office Pc\OneDrive\Documents\Elites-\StoreScout_Bengaluru_Dataset.zip`; this new report is not added to that ZIP.

**No enriched CSV was created and no additional features were incorporated into stored tables.** The 10 × 70 / 24-null result is the in-memory design in section 7. Original master SHA-256: `766ba60f599277b70a810993088a27317154b5b10b561b7516d0cff602584868`.

No commits, pushes, branch changes, staging, model training or target generation were performed. Changes remain local and uncommitted. Branch remains `ML` at the existing commit recorded above.

### Checks executed for this report

| Check | Result | Exact outcome |
|---|---|---|
| Exact master shape | PASS | 10 rows x 50 columns |
| Candidate keys and coordinates | PASS | 10 unique IDs and coordinate pairs; candidate records agree |
| Master missing values | PASS | 20 nulls retained, exactly 10 per unsupported field |
| Logical types | PASS | All populated numerics finite; count/year values integral; all-null intended numeric fields remain nullable |
| Dates and fractions | PASS | ISO dates valid and historical; gross-margin fractions bounded |
| Nonnegative financial inputs | PASS | INR monthly rent versus annual OPEX kept separate |
| Geographic consistency | PASS | 10/10 sites and complete 1500m metric circles within AOI |
| Nearest station assignments | PASS | 10/10 match geodesic recomputation; 9 distinct nearest station IDs |
| Saved inventory and hashes | PASS | All 27 CSV dimensions/null counts/hashes match saved quality report |
| Archived source hashes | PASS | 47/47 responses match, including the 3 unusable app shells |
| Master lineage and source IDs | PASS | 500 unique master record/field entries; source IDs resolve; unresolved locality assumption ID is separately flagged |
| Aggregation and one-row-per-site joins | PASS | In-memory only: 10 x 70; six-bin pivot, station summaries and spatial POI counts preserve row cardinality |
| Join coverage and missingness | PASS | Daypart/station joins 10/10; ward attributes 8/10; original 20 nulls plus 4 missing ward IDs |
| Report coverage | PASS | 50 column definitions and every one of the 27 CSV tables documented |

These read-only checks were rerun against existing files. The original 40-check validation report was inspected, not overwritten. Provenance discrepancies remain explicitly documented in section 8.

### Source-script hashes at audit

| Script | SHA-256 |
|---|---|
| `ml/bengaluru/acquire.py` | `79241908db504629d7c054c9cfa261fb525d587727508d8104821e5843e4ac2d` |
| `ml/bengaluru/acquire_detail.py` | `6a4b231335e98df8e56d96a8f76dd2d9ad0a0b783a253cfe6bc01302f98834e5` |
| `ml/bengaluru/acquire_final.py` | `aec5bfc3e3fa924f81acaa740a3dcbe5c1e9aba6e5a2251a75502add83378023` |
| `ml/bengaluru/acquire_retry.py` | `bde96754cf9d078481337f594476fb94409b4904ad895e33e31119adfd777793` |
| `ml/bengaluru/build.py` | `69b9b7aab714c35d8f19f9fe19cbca9931cc7a3ddeb76854e655884da91883c9` |
| `ml/bengaluru/inspect_data.py` | `0fba970aba55f1c2143dedbfb54e0a8fce62e9a11aca800bc7ec6d020349baf1` |
| `ml/bengaluru/validate.py` | `673d0e6b9a85d6c1d24511f0fbfa78c9b3f5103085d752aad1d324c50f429a26` |
