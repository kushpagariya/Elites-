# StoreScout Bengaluru dataset

Reference date: 2026-10-24. Read reports/completion_report.md first.
CSV is UTF-8 with a header row; an empty field is null. All monetary amounts
are INR. Costs and wallet prices have different explicitly recorded bases.
No model, labels, forecast, allocation or ranking is included.

Offline reproduction (Python 3.12):

    python -m pip install numpy rasterio shapely pyproj openpyxl pypdf pydantic
    python ml/bengaluru/inspect_data.py
    python ml/bengaluru/build.py
    python ml/bengaluru/validate.py

Run from the original repository root. Existing backend canonical schemas are
read for compatibility validation; they are not copied into this dataset ZIP.
The immutable raw snapshots and their SHA-256 hashes reproduce the dataset
offline. Re-fetching live OSM later can change inputs and requires a new snapshot.
The acquisition scripts preserve source files and failures. acquisition_files.csv
contains every original URL, exact retrieval time, size and hash.

The ZIP intentionally excludes the proprietary commercial-listing HTML and
Python caches. See reports/ATTRIBUTION_AND_LICENCES.md for component terms.
Git history and branches have not been modified. All additions are uncommitted.
