# StoreScout Bengaluru dataset completion report

Verdict: **DATASET_READY_WITH_LIMITATIONS**. 40 integrity checks passed; 0 failed.

## A. Acquisition and inspected fixtures

Actual public-source files are archived in raw/ and indexed with URLs, timestamps and hashes in final/acquisition_files.csv. See acquisition_report.md for every success, failed endpoint and alternative. Census 2011 tables, WorldPop India 2020 raster, BMRCL original hourly workbooks, OSM POIs/roads, historical and 2025 ward geometry, official HCES expenditure tables and official infrastructure documents were downloaded.

The six existing demo JSON fixtures were inspected (10 sites, 4 branches, 100 cells, 60 POIs, 1 event, six-bin assumed weight matrix) and remain byte-for-byte unchanged. Backend schemas and pipeline seams were inspected and unchanged.

## B. Output dimensions

**site_features.csv contains exactly 10 candidate rows and exactly 50 columns in the requested order.** CSV empty fields mean null, never implicit zero.

| Path | Rows | Columns | Null values | Validation |
|---|---:|---:|---:|---|
| data/bengaluru/final/acquisition_files.csv | 57 | 9 | 114 | PASS |
| data/bengaluru/final/candidate_sites.csv | 10 | 17 | 0 | PASS |
| data/bengaluru/final/census_2011_wards.csv | 198 | 15 | 0 | PASS |
| data/bengaluru/final/daypart_profiles.csv | 60 | 15 | 0 | PASS |
| data/bengaluru/final/daypart_weights.csv | 36 | 14 | 0 | PASS |
| data/bengaluru/final/existing_stores.csv | 4 | 10 | 0 | PASS |
| data/bengaluru/final/expenditure_inputs.csv | 31 | 13 | 0 | PASS |
| data/bengaluru/final/field_lineage.csv | 797 | 11 | 1,434 | PASS |
| data/bengaluru/final/infrastructure.csv | 2 | 18 | 6 | PASS |
| data/bengaluru/final/infrastructure_scenarios.csv | 3 | 10 | 3 | PASS |
| data/bengaluru/final/metro_activity_averages.csv | 26 | 11 | 0 | PASS |
| data/bengaluru/final/metro_date_coverage.csv | 793 | 7 | 0 | PASS |
| data/bengaluru/final/metro_daypart_coverage.csv | 3,526 | 11 | 796 | PASS |
| data/bengaluru/final/metro_hourly.csv | 11,976 | 17 | 5,450 | PASS |
| data/bengaluru/final/metro_station_lookup.csv | 13 | 14 | 0 | PASS |
| data/bengaluru/final/missing_fields.csv | 56,290 | 9 | 56,310 | PASS |
| data/bengaluru/final/poi_daypart_availability.csv | 28,656 | 8 | 27,030 | PASS |
| data/bengaluru/final/poi_deduplication.csv | 264 | 3 | 0 | PASS |
| data/bengaluru/final/pois.csv | 4,995 | 18 | 13,689 | PASS |
| data/bengaluru/final/project_assumptions.csv | 24 | 7 | 0 | PASS |
| data/bengaluru/final/schema_mapping.csv | 55 | 5 | 0 | PASS |
| data/bengaluru/final/site_features.csv | 10 | 50 | 20 | PASS |
| data/bengaluru/final/site_ward_lookup.csv | 10 | 8 | 8 | PASS |
| data/bengaluru/final/source_manifest.csv | 14 | 13 | 12 | PASS |
| data/bengaluru/final/spending_cells.csv | 100 | 17 | 100 | PASS |
| data/bengaluru/final/synthetic_assumptions.csv | 56,235 | 15 | 112,625 | PASS |
| data/bengaluru/final/ward_crosswalk.csv | 163 | 13 | 0 | PASS |

data_quality_report.json is supplied in both final/ and reports/. Geographic line/polygon records are GeoJSON, and the clipped population window is a GeoTIFF in processed/.

## C. Data origin

For the 500 master site-feature values: 400 derived (80%), 80 synthetic/assumed (16%), 20 unresolved nulls (4%), zero directly copied observed values, zero copied fixture values. Counts and station activity are derived from real records; derived values are not all purely observed because spending and opportunity depend on separately recorded assumptions. These counts include identifiers/status metadata and must not be interpreted as a market-evidence percentage.

Observed supporting evidence: 5,285 OSM records before filtering/deduplication, 4,995 retained POIs, 11,976 corridor metro interval records from original workbooks, 198 historical Census wards, and 256 clipped source-raster pixels. The six-bin fixture supplies 36 assumed weights; project budget, discount rate and horizon retain their approved fixture assumption status. synthetic_assumptions.csv supplies record-level generated values, units, reasons and low/base/high bounds where meaningful.

## D. Temporal integrity

See temporal_alignment_report.md. Metro source periods are August 1-18 and September 1-30, 2025; all master metro aggregates use September 2025 only. Population reference year 2020, Census 2011, boundaries 2012/December 2025, and expenditure August 2023-July 2024 remain separate. All interval timestamps use Asia/Kolkata (+05:30). Historical proxies are explicit. The 2024 wallet versus 2026 cost price mismatch remains documented.

## E. Data quality

264 same-name/category OSM duplicates were removed and logged; 16 boundary-intersecting elements with out-of-bound centres were excluded. No duplicate metro key is present. 8 source ward geometries required validity repair. Source IDs resolve and every master field has a lineage entry. Two Electronic City sites have no municipal ward join, without changing their valid corridor locations.

## F. StoreScout compatibility

- **reference_sales_training**: NOT_READY: no observed sales labels by design; no training or split performed
- **reference_sales_inference**: FEATURES_PREPARED_WITH_NULLS: needs later compatible trained artifact, missingness policy and feature contract
- **DaypartDNA**: READY_WITH_ASSUMPTIONS: 4995 mapped POIs before category filtering, 6 bins, weights, schedules, availability and evidence inputs
- **infrastructure_scenarios**: READY_FOR_ASSUMED_DEMO: current/opens/delayed inputs, no verified Blue opening date
- **Huff_cannibalisation**: INPUTS_PREPARED_WITH_ASSUMPTIONS: unique 100 cell wallets, 4 fictional branches, external competitors, attraction defaults; no allocation run
- **financial_calculations**: INPUTS_PREPARED_WITH_PRICE_MISMATCH: all required store financial fields and project assumptions; 2024 wallets versus 2026 demo costs need explicit later treatment
- **FailFast**: PARTIAL: financial inputs exist; critical demand/model evidence and routing/households remain unavailable; no viability calculated
- **sensitivity**: INPUTS_PREPARED: labelled low/base/high commercial assumptions, no forecasting performed
- **ranking_and_portfolio**: INPUTS_PREPARED_ONLY: 10 candidates and budget; awaits later evaluation/inference/network/finance; no ranking/optimization performed

The generated inputs validate against the existing canonical Project, Site and Store schemas after explicit column selection/renaming. No endpoint or schema was modified. The dataset is not automatically loaded into the Navi Mumbai demo; backend integration remains a later task.

## G. Final deliverables

- Master: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\final\site_features.csv`
- Supporting datasets, manifest and lineage: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\final`
- Quality report: `C:\Users\Office Pc\OneDrive\Documents\Elites-\data\bengaluru\reports\data_quality_report.json`
- ZIP: `C:\Users\Office Pc\OneDrive\Documents\Elites-\StoreScout_Bengaluru_Dataset.zip`

## H. Git confirmation

Branch: `ML`. Existing HEAD: `569f4f52f459ed09129c04a17ac97485601d7bb7`. No commits, pushes, branch switches or other Git state/history mutations were performed. Existing tracked code and fixtures are unchanged; all new files remain local and uncommitted.

## I. Limitations and next dependency

1. No measured sales labels or trained model exist. The 50-column file is a feature snapshot, not a supervised training dataset. Inference awaits a separately trained compatible model.
2. Population is a modelled 2020 WorldPop 1km estimate, carried as a historical proxy. Within-pixel density is assumed uniform; it is not a 2026 measurement or a 100m product.
3. Annual category wallets combine 2020 population with Karnataka urban HCES 2023-24 expenditure, 50% grocery eligibility for the processed-food/cooked-meal category, and a state-to-local transfer assumption. They are addressable category expenditure, not store sales.
4. Wallet price year is 2024 (2023-24 nominal survey prices); fictional rent, CAPEX and non-rent OPEX use a 2026-10-24 price basis. No inflation adjustment or matched-price economic forecast is claimed.
5. Ten-minute population and accessible households are null for all ten sites. No validated travel-time graph or local household denominator was obtained.
6. OSM is incomplete crowdsourced coverage. Counts of zero mean zero mapped records, not verified absence. Node/way centres, facility subdivisions and unrecorded shops can affect counts. Same-name/category duplicates within 40m are collapsed and logged.
7. Daypart weights and missing-hours availability/evidence weights are assumptions. Only a conservative opening-hours syntax subset is interpreted. Profiles are POI opportunity proxies, not measured store footfall. Metro traffic is kept separate.
8. Metro records cover August 1-18 and September 1-30, 2025 at network level. Corridor Yellow Line stations have later August coverage after launch. August exits are null because no exit-clock workbook was acquired; 23:00-to-last-train intervals have unknown duration. Master averages use September only and include observed night zeros.
9. Census 2011 remains historical. A 2012 198-ward geometry layer is joined by ward code to Census; geometry-only overlap crosswalks link it to December 2025 wards. Geometry repairs are recorded. Two Electronic City candidates lie outside available municipal ward polygons and retain null ward joins.
10. Yellow Line inauguration is verified as 2025-08-10; first commercial service date is not independently asserted. Blue Line official completion programmes are historical, not guaranteed openings. July 1, 2027 and the 24-month delayed July 1, 2029 date, plus a 10% illustrative effect, are explicitly assumed and excluded from baseline features. Blue geometry is an OSM partial alignment, not a verified official station-access map.
11. All candidate premises, areas, financials and existing company branches are synthetic. Public commercial listings were retrieved but mixed offices, asking prices and promoted distant properties do not verify available grocery premises or lease benchmarks.
12. Metro repository ODbL and OpenCity non-commercial metadata differ; BMRCL contents copyright is also stated. Rights for commercial redistribution remain unresolved. OSM ODbL, WorldPop CC-BY-4.0 and DataMeet CC-BY-SA-2.5-IN attribution/share-alike obligations are preserved.
13. Some original release dates are unverified and remain null. Retrieval times and file hashes are stored separately; retrieval is never substituted for observation or release date.
14. source_quality_score is 6/8 evidence-family availability, not a calibrated reliability measure, model confidence or prediction score. It does not measure source completeness within the corridor.

Next dependency: a separately authorised model-data/training instruction and a coordinated backend integration of this distinct feature snapshot. No domain engine, model, fitted artifact, training labels, split, API or frontend implementation was added. Stop after dataset creation, validation and reporting.