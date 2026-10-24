"""Freeze local inputs and verify model identity without estimating anything."""
import hashlib
import json
import os
from pathlib import Path

from ..repositories.store import fingerprint
from .errors import ServiceError

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "data" / "demo"
VALUATION_DATE = "2026-10-24"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def model_bundle():
    directory = Path(os.getenv("STORESCOUT_MODEL_DIR", str(ROOT / "ml" / "artifacts"))).resolve()
    card_path = directory / "model_card.json"
    if not card_path.is_file():
        return None
    try:
        card = read_json(card_path)
        artifact = (directory / card["artifact_file"]).resolve()
        if not artifact.is_relative_to(directory) or not artifact.is_file():
            raise ValueError("Artifact must be a local file within the model directory")
        if not card.get("model_artifact_id") or card.get("method_mode") not in {"model_simulated", "model_real_evaluated"}:
            raise ValueError("Model card must identify model and method")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if card.get("artifact_sha256") not in {None, digest}:
            raise ValueError("Artifact hash does not match model card")
        return {"card": card, "artifact_sha256": digest, "card_sha256": hashlib.sha256(card_path.read_bytes()).hexdigest(), "artifact_path": str(artifact)}
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise ServiceError(503, "MODEL_UNAVAILABLE", "Installed model bundle is invalid; check its card and artifact.") from exc


def engine_identity():
    directory = ROOT / "backend" / "app" / "domain"
    return fingerprint({str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob("*.py"))})


def load_snapshot(feature_snapshot_id):
    try:
        names = ("project", "cells", "pois", "infrastructure", "weights", "source_manifest")
        contents = {name: (DATA_ROOT / f"{name}.json").read_bytes() for name in names}
        values = {name: json.loads(body.decode("utf-8-sig")) for name, body in contents.items()}
    except (OSError, ValueError) as exc:
        raise ServiceError(503, "SOURCE_UNAVAILABLE", "The local source snapshot is missing or invalid.") from exc
    if not isinstance(values["source_manifest"], dict) or not values["source_manifest"].get("feature_snapshot_id"):
        raise ServiceError(503, "SOURCE_UNAVAILABLE", "Source manifest must identify its feature snapshot.")
    if feature_snapshot_id != values["source_manifest"]["feature_snapshot_id"]:
        raise ServiceError(409, "STALE_SNAPSHOT", "Feature snapshot does not match the installed project sources.")
    if not isinstance(values["cells"], list) or not isinstance(values["pois"], list) or not isinstance(values["source_manifest"].get("source_ids"), list):
        raise ServiceError(503, "SOURCE_UNAVAILABLE", "Source records or source IDs are invalid.")
    if len(values["cells"]) > 2000 or len(values["pois"]) > 10000:
        raise ServiceError(422, "INPUT_CAP_EXCEEDED", "Source snapshot exceeds prototype input caps.")
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in contents.items()}
    return {**values, "feature_snapshot_id": feature_snapshot_id, "snapshot_hash": fingerprint(hashes), "source_hashes": hashes, "valuation_date": VALUATION_DATE}


def installed_snapshot():
    try:
        identity = read_json(DATA_ROOT / "source_manifest.json")["feature_snapshot_id"]
    except (OSError, ValueError, KeyError) as exc:
        raise ServiceError(503, "SOURCE_UNAVAILABLE", "Source manifest is unavailable.") from exc
    return load_snapshot(identity)
