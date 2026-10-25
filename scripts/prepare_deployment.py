"""Fail the build if the approved model or inference snapshot cannot be loaded.

Run from repository root after installing backend/requirements.txt.
Does not retrain, access accounts, or create workspace databases.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.services import sources, showcase

if __name__ == '__main__':
    bundle = sources.restore_packaged_model()
    preview = showcase.load()
    assert len(preview['dayparts']) == 6
    assert preview['model_artifact_id'] == bundle['card']['model_artifact_id']
    print(json.dumps(dict(status='ready', model_artifact_id=preview['model_artifact_id'],
                          method_mode=preview['method_mode'], daypart_count=len(preview['dayparts']),
                          artifact_sha256=bundle['artifact_sha256'])))
