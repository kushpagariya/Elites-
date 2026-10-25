"""Portable selected-model bundle for a future branch upload (no raw sources).

Create: python -m ml.decision_engine.package
Restore: python -m ml.decision_engine.package --install
Existing differing artifacts are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'ml/evaluation/decision_engine_v1'
ARTIFACTS = ROOT/'ml/artifacts/reference_sales_v2'
ALLOWED = {'manifest.json', 'catboost.joblib', 'feature_schema.json', 'support.json', 'MODEL_CARD.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def create_bundle():
    OUT.mkdir(parents=True, exist_ok=True)
    contents = {name:(ARTIFACTS/name).read_bytes() for name in sorted(ALLOWED)}
    bundle = OUT/'reference_sales_v2_artifacts.zip'
    with ZipFile(bundle, 'w', ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    record = dict(bundle_sha256=sha(bundle.read_bytes()), files={name:sha(data) for name,data in contents.items()},
                  purpose='Selected fitted model only; excludes restricted raw workbooks, source snapshots and personal data',
                  model_artifact_id=json.loads(contents['manifest.json'])['model_artifact_id'])
    (OUT/'artifact_bundle_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record


def install_bundle(destination=ARTIFACTS):
    destination=Path(destination).resolve()
    record=json.loads((OUT/'artifact_bundle_manifest.json').read_text(encoding='utf-8'))
    bundle=OUT/'reference_sales_v2_artifacts.zip'
    if sha(bundle.read_bytes())!=record['bundle_sha256'] or set(record['files'])!=ALLOWED:
        raise ValueError('Artifact bundle manifest/hash mismatch')
    with ZipFile(bundle) as archive:
        names=archive.namelist()
        if len(names)!=len(ALLOWED) or set(names)!=ALLOWED:
            raise ValueError('Unexpected/duplicate archive members')
        contents={name:archive.read(name) for name in names}
    for name,data in contents.items():
        path=destination/name
        if path.resolve().parent!=destination or sha(data)!=record['files'][name]:
            raise ValueError('Unsafe artifact path or hash mismatch')
        if path.exists() and path.read_bytes()!=data:
            raise ValueError(f'Refusing to overwrite different artifact: {name}')
    # All entries checked before any writes; this restores only the allowlist.
    destination.mkdir(parents=True,exist_ok=True)
    for name,data in contents.items():
        path=destination/name
        if not path.exists(): path.write_bytes(data)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    print(json.dumps(install_bundle() if args.install else create_bundle(),indent=2))
