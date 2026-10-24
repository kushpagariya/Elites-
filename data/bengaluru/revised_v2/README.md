# Bengaluru data integrity revision

This directory is an optional correction/enrichment layer over the frozen `../final/` dataset. It is not a new canonical master, a trained model, a ranking, or a set of sales labels. All pre-existing files, including the original 27 CSVs, source snapshots, scripts, audit, reports and root archive, are preserved. The baseline SHA-256 inventory is `baseline_hashes.json`.

Read `completion_report.md` for actual output dimensions, null counts, join coverage, test results, limitations and the complete file inventory. Machine-readable results are in `validation_report.json`. `CHANGELOG.md` records the corrections; `LICENSING_AND_DISTRIBUTION.md` records unresolved distribution rights.

## Dataset selection and joins

- `site_features_enriched.csv`: exactly ten candidate rows and 70 ordered fields. Fields 1–50 retain their original CSV strings and embedded v1 identities. Fields 51–70 reproduce the previously audited enrichment. Its relationship to revised provenance is explicit in `dataset_metadata.json`; do not change or misinterpret its retained v1 source-manifest identifier.
- `site_feature_schema.csv`: logical types, semantic units, origin classes and nullability for all 70 fields. CSV storage does not itself enforce these types. `field_lineage.csv` supplies 500 original-master cell records, 700 enriched cell records and wildcard field records for supporting tables. A wildcard documents column semantics and per-record source/assumption references; it does not assert every supporting value is observed.
- `assumption_registry.csv`: unique assumption IDs. `synthetic_assumptions.csv` retains every original record and adds provenance records for ten locality anchors, ten legacy 0.75 indicators and the existing uniform-within-pixel population method. No added record is a new observed premise or financial actual.
- The enrichment aggregates/pivots `daypart_profiles.csv`, `pois.csv`, `metro_station_lookup.csv`, `site_ward_lookup.csv` and `metro_activity_averages.csv` from frozen `../final/`, then joins by candidate or nearest-station key. All ten sites have POI/profile/metro coverage. Ward matches are available for eight; site-09 and site-10 remain unmatched in both vintages. No join expands candidate rows. Ward context never allocates 2011 ward population to candidates.
- Candidate coordinates and premises/financial inputs remain hypothetical. Derived features inherit this location dependence. Original population and wallet estimates are not recalculated, rounded again or inflated. Census totals, crosswalk matrices, road geometries, raw acquisitions and financial/scenario assumption records are not flattened into the site row.

The exact appended fields are the six `{bin}_weekly_exposure_share` fields in canonical order; four `daypart_*` support/fraction fields; three `mapped_*_count_1500m` competitor subtypes; `operational_metro_station_count_1500m`; two vintage ward IDs; and four September 2025 weekday/weekend observation-hour/day fields. `dataset_metadata.json` records their complete ordered names.

## Temporal and evidence semantics

WorldPop is a **2020 modelled, UN-adjusted, nominal 1 km** product, not current population or a 100 m product. Within-pixel uniform density is an explicit spatial assumption. HCES is Karnataka urban August 2023–July 2024 expenditure in nominal survey-period INR. `wallet_price_year=2024` denotes that period's ending year. Synthetic rent/opex/capex use the 24 October 2026 scenario basis. No inflation conversion or claim of comparable current prices is made.

The HCES detailed report release is corrected from the unsupported 31 January to **30 January 2025**, verified against archived official [MoSPI press evidence](https://www.mospi.gov.in/sites/default/files/press_release/HCES_Report202324_Press_Note_30012025.pdf) and [PIB release evidence](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097601&lang=2&reg=3). The factsheet was released on 27 December 2024. New verification acquisition times and hashes are in `source_verification/verification_log.json` and `source_acquisitions.csv`. Original acquisition records are retained unchanged; the legacy `retrieved_at_utc` field records request start, and historical response-completion times are unknown. Unknown product-release dates and fresh official project-status dates remain null. Valuation, retrieval, boundary vintage, reference year and measured service dates are separate concepts.

The revised HCES parser reads numbered multiline records and recovers item 24 (`consumer services excluding conveyance`, INR 404.46/person/30 days). All other 31 expenditure records and the grocery calculation **INR 2,974.915/person/month** remain unchanged. The latter uses items 1–13 + 0.5 × item 14 + items 18 and 19. No target is derived from this expenditure proxy.

## DaypartDNA supporting outputs

`daypart_site_support.csv` distinguishes nonempty original opening-hours tags from successfully parsed schedules. The exact audited `daypart_recorded_hours_support_count` and fraction mean **parsed recorded schedules**, as in the original profiles. `opening_hours_recorded_count` and its fraction include unsupported recorded syntax; unsupported or missing schedules use the pre-existing explicit assumptions. Each site support count is counted once, not summed six times.

`daypart_opportunity_shares.csv` retains six canonical bins and adds partial-support indicators. For bin b, weekly exposure = raw opportunity × duration hours × starting days/week; share = bin exposure / sum across six bins. These are representative-week POI opportunity proxies with assumed weights, availability and evidence factors. `observed_service_period_complete` is deliberately null: POI proxies have no observed service-period completeness claim. No observed metro counts enter this formula.

All times use Asia/Kolkata. Weekdays: 06–11, 11–15, 15–20, 20–next-day 06. Weekends: 06–18, 18–next-day 06. An overnight bin belongs to its **starting day**, so Saturday 02:00 belongs to Friday weekday-night and Monday 02:00 belongs to Sunday weekend-evening.

`metro_daypart_coverage.csv` reports both directions per station/starting-date/bin, including August 31's boundary and September 30's partial night. Only September service-date intervals with paired nonnegative integer entries/exits, actual 60-minute timestamps and valid station/timezone keys qualify. The aggregate `metro_daypart_rates.csv` includes complete bins whose starting day falls in September 2025. `site_metro_daypart_rates.csv` joins these rates to each candidate's nearest matched station. Rates divide observed counts by actual observed **clock hours**, including real night zeros; no missing count becomes zero. September 30 night has only four of ten hours and is excluded. September 1 00–06 belongs to August 31 and is also excluded from September-start aggregates. Full-month clock coverage and complete-bin coverage therefore differ.

`site_evidence_coverage.csv` reports actual site-specific counts/fractions and missing routing/household support. The unchanged 0.75 master value is a legacy literal 6/8 evidence-family indicator; it is neither prediction confidence nor observation reliability. Neither transit ridership nor POI opportunity is measured store footfall. OSM completeness and commercial suitability remain unverified.

## Sources and infrastructure

`source_manifest.csv` retains original source IDs/URLs, adds two official release-verification sources and explicit existing-project-fixture provenance, and corrects date semantics. It does not claim new acquisition of the historical datasets. Exact original downloads, failed attempts and checksums remain in the acquisition ledger. The full presentation source audit remains unchanged at `../reports/data_sources_for_presentation.md`; read it with this revision's change log for corrected metadata.

Yellow Line's archived 10 August 2025 inauguration evidence and September operational counts remain facts. A distinct first-commercial-service date and fresh official status observation remain unknown. Blue Line dates 1 July 2027 / 1 July 2029 and 10% uplift remain hypothetical assumptions, excluded from baseline operational infrastructure. The old scenario-as-status dates are retained only as explicitly labelled legacy metadata. No external source has verified the hypothetical opening or uplift.

## Reproduction

From the repository root, with Python 3.12 and `pyproj`, `shapely`, `pypdf` installed:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python data/bengaluru/revised_v2/scripts/build_revised.py
python data/bengaluru/revised_v2/scripts/validate_revised.py
```

Both scripts write only within this revision; the builder verifies the frozen inventory before and after processing. The validator is read-only against data and writes its reports here. It checks all original SHA-256 hashes and unchanged Git branch/HEAD. The separate `verify_hces_release.py` is an optional network acquisition script; the archived evidence already suffices for offline rebuilding. Running it again changes v2 retrieval times and may change snapshots; rebuild and revalidate afterward. No compiler caches or model artifacts are needed.

Frozen tables not copied here are referenced from `../final/`. The legacy `missing_fields.source_attempts` column may contain narrative locators, not source-ID foreign keys; it is not treated as an ID column. Actual `source_id(s)`, `status_source_id`, `release_evidence_source_ids` and `assumption_id(s)` are validated against their registries. Supporting generic assumption values remain strings because their units and origin vary per record.

## Next dependency

RetailIQ needs verified candidate premises, current commercial costs, explicit treatment of historical price bases, validated network-time catchments and an approved evaluation method before a ranking is meaningful. Supervised work requires genuine, consented sales/outcome targets with temporal and geographic holdouts; none are available here. DaypartDNA needs more supported opening schedules, longer measured transit series and independent store-visit validation/calibration. Resolve metro reuse rights before publishing or commercial redistribution. Stop here until further instruction; no training or engines are included.
