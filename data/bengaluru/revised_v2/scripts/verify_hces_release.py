"""Archive official release evidence inside v2 only; never alter baseline sources."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import urllib.request

V2 = Path(__file__).resolve().parents[1]
SOURCES = [
    ('hces-release-note', 'https://www.mospi.gov.in/sites/default/files/press_release/HCES_Report202324_Press_Note_30012025.pdf', 'hces_release_note.pdf'),
    ('hces-release-pib', 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097601&lang=2&reg=3', 'hces_release_pib.html'),
]

def main():
    evidence = V2 / 'source_verification'
    evidence.mkdir(exist_ok=True)
    results = []
    for sid, url, filename in SOURCES:
        row = dict(source_id=sid, url=url, request_started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'StoreScout-data-integrity/2'}), timeout=60) as response:
                body = response.read()
                row['content_type'] = response.headers.get('Content-Type')
            path = evidence / filename
            path.write_bytes(body)
            row.update(status='DOWNLOADED', local_path=path.relative_to(V2).as_posix(), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body), response_completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
            if filename.endswith('.pdf'):
                from pypdf import PdfReader
                text = ' '.join(page.extract_text() for page in PdfReader(path).pages)
                normalized = re.sub(r'\s+', ' ', text).lower()
                row['date_and_release_statement_verified'] = bool(re.search(r'30\s*(?:th)?\s*january\s*2025', normalized)) and 'being released now' in normalized
            else:
                normalized = re.sub(r'\s+', ' ', body.decode('utf-8', errors='replace')).lower()
                row['date_and_release_statement_verified'] = '30 jan 2025' in normalized and bool(re.search(r'being\s+released\s+now', normalized))
            row['verified_release_date'] = '2025-01-30' if row['date_and_release_statement_verified'] else None
        except Exception as exc:
            row.update(status='FAILED', error=str(exc), verified_release_date=None)
        results.append(row)
    (evidence / 'verification_log.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps([{k:v for k,v in row.items() if k not in ['content_type']} for row in results], indent=2))

if __name__ == '__main__':
    main()
