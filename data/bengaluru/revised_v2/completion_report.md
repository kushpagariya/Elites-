# Bengaluru v2 integrity completion report

**DATA_INTEGRITY_READY_WITH_LIMITATIONS**

Validation: **27 tests, 27 passed, 0 failures, 0 errors, 0 skipped**. See `validation_report.json` for per-test results, nulls per column, unique keys, hashes and runtime versions. Validation completed at 2026-10-24T17:15:41.505132+00:00.

All **199 pre-existing files** were checked: **199 unchanged**. This includes every original 27 CSV, raw snapshot and existing archive. The canonical master remains **10 × 50, 20 nulls**; SHA-256 `766ba60f599277b70a810993088a27317154b5b10b561b7516d0cff602584868`.

Branch remains `ML`, HEAD `569f4f52f459ed09129c04a17ac97485601d7bb7`. No commit, push, branch switch, model training, label generation, analytical-engine implementation or backend/frontend change was performed.

## Actual CSV outputs

| File | Rows | Columns | Empty fields |
|---|---:|---:|---:|
| `assumption_registry.csv` | 48 | 7 | 0 |
| `daypart_opportunity_shares.csv` | 60 | 21 | 60 |
| `daypart_site_support.csv` | 10 | 14 | 0 |
| `expenditure_inputs.csv` | 32 | 13 | 0 |
| `field_lineage.csv` | 1,649 | 19 | 5,449 |
| `infrastructure.csv` | 2 | 27 | 10 |
| `infrastructure_scenarios.csv` | 3 | 10 | 3 |
| `metro_daypart_coverage.csv` | 2,756 | 18 | 52 |
| `metro_daypart_rates.csv` | 156 | 19 | 0 |
| `project_assumptions.csv` | 24 | 7 | 0 |
| `site_evidence_coverage.csv` | 10 | 24 | 0 |
| `site_feature_schema.csv` | 70 | 8 | 0 |
| `site_features_enriched.csv` | 10 | 70 | 24 |
| `site_metro_daypart_rates.csv` | 120 | 20 | 0 |
| `source_acquisitions.csv` | 59 | 13 | 175 |
| `source_manifest.csv` | 17 | 23 | 98 |
| `synthetic_assumptions.csv` | 56,256 | 15 | 112,709 |

An empty field is a preserved unknown or intentionally inapplicable metadata value; counts include metadata blanks. Explicit zero counts and False flags are populated observations/values. In the enriched file, nulls are exactly ten `population_10min_est`, ten `accessible_households_est`, two `ward_2011_id` and two `ward_2025_id`. The 60 POI service-period flags are inapplicable, not an imputed observed period. Metro coverage has 26 zero-support boundary rows with both count and rate left null (52 empty fields).

## Corrections and source verification

The 70-field view preserves every original 50-field value and appends the exact audited 20 fields. Semantic units/types, locality/fixture provenance, historical-period metadata, per-site evidence coverage, overnight metro denominators and HCES multiline extraction are repaired. See `CHANGELOG.md` and `README.md` for transformations and definitions. All fields have source/assumption lineage and foreign-key checks; the v1 embedded master IDs are retained and mapped to corrected v2 provenance externally.

The original master and source audit were not rewritten. Newly verified official [MoSPI](https://www.mospi.gov.in/sites/default/files/press_release/HCES_Report202324_Press_Note_30012025.pdf) and [PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097601&lang=2&reg=3) evidence establishes the detailed HCES report release as **30 January 2025**, superseding the unsupported 31 January metadata in v1. Factsheet release remains **27 December 2024**. The new source snapshots, exact URLs, request/completion times and hashes are archived under `source_verification/`; the other historical data were not reacquired. Item 24 adds INR **404.46** expenditure; grocery INR **2,974.915** is unchanged.

## Incorporated supporting tables and join coverage

| Frozen table used for enrichment | Use | Candidate coverage |
|---|---|---|
| `site_features.csv` | Unchanged 50-field candidate base | 10/10, one row each |
| `daypart_profiles.csv` | Pivot six weekly shares and three support counts; calculate parsed fraction | 10/10 × 6 bins |
| `pois.csv` | Geodesic 1,500 m subtype and opening-hours evidence counts | 10/10; mapped counts only |
| `metro_station_lookup.csv` | Operational station counts; retain nearest-station identity | 10/10; 13 matched stations |
| `site_ward_lookup.csv` | Separate-vintage point-in-polygon IDs | 8/10 per vintage; four ID nulls retained |
| `metro_activity_averages.csv` | September weekday/weekend observed hour/day support | 10/10 many-to-one station joins |

New separate metro rates additionally use `metro_hourly.csv`; tests independently reconcile them to service-date clocks. POI tests independently recompute opportunity/support using `poi_daypart_availability.csv`, `daypart_weights.csv` and source POIs. Ward tests recompute point containment from the frozen historical/2025 GeoJSON layers. Other unrelated tables are documented/referenced, not indiscriminately joined. Exactly ten site rows survive; no row multiplication, outcome leakage or invented targets.

## Metro aggregation denominators

| Canonical bin | Hours per bin | Complete starting days | Used clock hours per station/direction |
|---|---:|---:|---:|
| weekday_morning | 5 | 22 | 110 |
| weekday_lunch | 4 | 22 | 88 |
| weekday_evening | 5 | 22 | 110 |
| weekday_night | 10 | 21 | 210 |
| weekend_day | 12 | 8 | 96 |
| weekend_evening | 12 | 8 | 96 |

September has 9,360 valid paired hourly records across 13 stations (720 each); 2,616 August records are excluded. Full-month paired-clock coverage is 100%, but complete eligible starting-day bin coverage is **103/104** per station, because September 30 night lacks October 1 00–06. September 1 00–06 belongs to August 31 and is outside September-start bins. Together the six aggregates use 710 included clock hours per station/direction, distinct from the preserved 528 weekday + 192 weekend calendar-hour means. Counts are observed transit traffic; neither transit nor POI opportunity measures store footfall.

## Remaining limitations and next dependency

- BMRCL content copyright / GitHub ODbL / OpenCity cc-nc conflict is unresolved. Public and commercial redistribution is not cleared, including inherited metro-derived outputs. No new public package or workbook copies created.
- Original 10 candidates, 4 existing branches, premises economics and financial inputs remain synthetic or assumed; no verified premises, realised sales targets, trained predictions or calibrated rankings exist.
- WorldPop is a 2020 modelled 1 km population proxy; within-pixel density is assumed uniform. Exact product publication day is unknown. No current population projection applied.
- HCES is nominal August 2023-July 2024 Karnataka urban spending; local transfer/category choices are assumptions. Synthetic costs use 24 October 2026 nominal demo prices. No inflation adjustment or price-basis harmonisation applied.
- OSM is a partial mapped inventory with unknown completeness. Most opening schedules are absent or unsupported. Parsed and merely recorded counts differ; proxies are not measured store footfall.
- Metro is historical September 2025 station traffic. September-start complete-bin rates exclude the incomplete final overnight bin and prior-month starting-day boundary; they differ in window/denominator from preserved master day-type means.
- site-09 and site-10 have no matches in either municipal ward vintage. Four ward IDs, ten household estimates and ten network-time population estimates remain null. No validated routing or household denominator exists.
- A new official current infrastructure status observation and exact first-commercial-opening dates are not established. Blue dates and uplift remain hypothetical and excluded from operational baseline.
- Original 57 acquisition records preserve legacy request-start timestamps; response-completion timestamps cannot be reconstructed. Failed endpoints and unverified original RTI delivery chain remain documented in the frozen audit.

RetailIQ requires verified premises/costs, an explicit price-basis policy, validated routing and approved evaluation assumptions. Supervised prediction requires genuine outcome targets and temporal/spatial evaluation; none were created. DaypartDNA requires more verified opening schedules, longer observed series and independent store-visit calibration. Resolve metro reuse rights before any public/commercial distribution. No training or application implementation follows this correction task.

## Complete created-file inventory

All **34 files** are under `data/bengaluru/revised_v2/` (17 CSVs). No new raw metro workbook or ZIP is included. Paths below are relative to this directory. Machine-readable SHA-256 values are in `validation_report.json`; self-referential generated reports are explicitly excluded from hashing.

- `assumption_registry.csv`
- `baseline_hashes.json`
- `CHANGELOG.md`
- `completion_report.md`
- `dataset_metadata.json`
- `daypart_opportunity_shares.csv`
- `daypart_site_support.csv`
- `distribution_manifest.json`
- `expenditure_inputs.csv`
- `expenditure_processing.json`
- `field_lineage.csv`
- `infrastructure.csv`
- `infrastructure_scenarios.csv`
- `LICENSING_AND_DISTRIBUTION.md`
- `metro_aggregation_metadata.json`
- `metro_daypart_coverage.csv`
- `metro_daypart_rates.csv`
- `project_assumptions.csv`
- `README.md`
- `scripts/build_revised.py`
- `scripts/validate_revised.py`
- `scripts/verify_hces_release.py`
- `site_evidence_coverage.csv`
- `site_feature_schema.csv`
- `site_features_enriched.csv`
- `site_metro_daypart_rates.csv`
- `source_acquisitions.csv`
- `source_manifest.csv`
- `source_verification/hces_release_note.pdf`
- `source_verification/hces_release_pib.html`
- `source_verification/verification_log.json`
- `synthetic_assumptions.csv`
- `tests/test_integrity.py`
- `validation_report.json`

DATA_INTEGRITY_READY_WITH_LIMITATIONS
