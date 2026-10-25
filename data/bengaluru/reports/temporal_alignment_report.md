# Temporal alignment report

| Source | Observation / reference period | Snapshot use |
|---|---|---|
| osm-pois | 2026-10-24 to 2026-10-24 | Crowdsourced mapped features, not a verified business census; attribution and share-alike apply. |
| osm-roads | 2026-10-24 to 2026-10-24 | Road access tags are retained; no ten-minute travel-time claim. |
| worldpop-2020 | 2020-01-01 to 2020-12-31 | Modelled population estimates, not measured 2026 Census counts. Original 1km product release date unverified. |
| metro-rti | 2025-08-01 to 2025-09-30 | GitHub asserts ODbL, OpenCity labels corresponding data non-commercial; do not assume commercial redistribution rights resolved. |
| census-2011 | 2011-01-01 to 2011-12-31 | Housing and assets fields are percentages, not household counts. Do not convert directly into households. |
| wards-2012 | 2012-01-01 to 2012-12-31 | Use geometry and ward codes only; embedded population differs from Census 2011 and is excluded. |
| wards-2025 | 2025-12-01 to 2025-12-31 | Administrative boundary vintage; embedded TOT_P year not independently verified and not used as current population. |
| hces-2023-24 | 2023-08-01 to 2024-07-31 | State/urban survey estimates in nominal survey-period INR; local transfer is an explicit assumption. |
| yellow-official | 2025-08-10 to 2025-08-10 | Inauguration date is verified; separate first commercial service date is not asserted. |
| blue-official |  to  | Reference publication 2025-26; exact status observation date unverified. Published completion programmes are not verified openings and may be superseded; OSM currently maps construction. |
| commercial-attempt | 2026-10-24 to 2026-10-24 | Asking listings include offices and distant promoted properties; no verified supermarket premises/lease or comparable benchmark obtained. |
| approved-weights | 2026-10-24 to 2026-10-24 | ASSUMED, not calibrated footfall. Values retained with duration handling documented. |
| assumptions | 2026-10-24 to 2026-10-24 | Never represent these records as real shops, financial actuals, or measured traffic. |
| package-config | 2026-10-24 to 2026-10-24 | Analyst-selected rectangular AOI is not an official jurisdiction. |

Source observation dates, release dates, exact retrieval timestamps, snapshot valuation date and monetary price bases are separate. Unknown release dates remain null. WorldPop 2020 is not grown to 2026. Census 2011 is not relabelled as a 2025 ward population.

Metro conversion reads original wide workbooks. August labels are preserved verbatim. H00-H23 September codes are recorded as reported clock hours; timestamps include +05:30 and timezone Asia/Kolkata. August 23:00 to last train has null end/duration and is excluded from hourly averages. August exits remain null. Derived origin-destination destination sums in the alternative processed CSV do not establish the clock time of station exits.

All master ridership averages use paired September 1-30, 2025 observations only: 22 weekdays and 8 weekend days per station, each with 24 observed clock intervals. These are historical proxies, not 2026 predictions. August/September coverage and all gaps across August 1-September 30 are explicit in metro_date_coverage.csv. No missing service day is filled with zero.

Six bins use starting local days. For example Saturday 02:00 belongs to Friday weekday_night; Monday 02:00 belongs to Sunday weekend_evening. Per-hour POI opportunity indices are kept separate from duration/frequency-weighted weekly exposures and shares. Measured metro counts are not added to the POI index.

Addressable grocery expenditure per person per month is INR 2974.915: sum of Karnataka urban HCES Statement 3U categories 1-13, plus 0.5 times category 14, plus toiletries (18) and household consumables (19). A twelve-month annualization is applied to source-estimated population. The 0.5 eligibility split and transfer of the Karnataka urban average to local residents are assumptions, not store capture rates.

wallet_price_year=2024 denotes nominal 2023-24 survey prices. Candidate cost assumptions use nominal INR at October 24, 2026. The mismatch is retained explicitly; no unverified inflation factor was applied. Later financial inference must resolve it or operate in a declared mismatch assumption mode.

Blue Line construction/alignment records and hypothetical 2027/2029 scenario dates never enter current baseline features. The 2026-12 published official programme is historical and not copied into verified_opening_date. Yellow Line inauguration is recorded separately from commercial opening.