"""Синтетичний API-власник для transport/cache тестів; не схема продукту й не gold."""
import hashlib
import json

def байти(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def пакет_контракту():
    schema = {"type": "object", "additionalProperties": False}
    prompt = "FIXTURE ONLY: classify the supplied image; output JSON."
    taxonomy = {"dress_generic": "dress"}
    return dict(version="fixture-only", schema=schema, prompt=prompt, taxonomy=taxonomy,
        hashes={"schema_sha256": hashlib.sha256(байти(schema)).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "taxonomy_sha256": hashlib.sha256(байти(taxonomy)).hexdigest()})

def перевірити_відповідь(raw):
    try:
        x = json.loads(raw)
        assert set(x) == {"target", "item_type", "bbox", "reason"}
        assert x["item_type"] in ("dress_generic", "unknown")
        status = "classified" if x["item_type"] == "dress_generic" else "ambiguous" if x["target"] == "ambiguous" else "unknown"
        return dict(status=status, observation=x, errors=[])
    except (ValueError, AssertionError, TypeError):
        return dict(status="invalid", observation=None, errors=["fixture_invalid"])

def спостереження(raw, **metadata):
    return dict(version="fixture-only", **metadata, **перевірити_відповідь(raw))


def перевірити_кадри(manifest, receipt):
    return dict(status="verified", errors=[], records=manifest["records"])
