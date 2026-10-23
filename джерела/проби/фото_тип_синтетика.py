"""Синтетичні свідки договору #1450; не фото-приймання й не пілот7483."""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import photo_type as Ф
import фід_збагачення as З
import build_артефакт as Б


def sha(value):
    return hashlib.sha256(Ф.канонічні_байти(value)).hexdigest()


def fixture():
    raw = json.dumps(dict(target="unique", item_type="shirt", bbox=[0, 0, 1000, 1000], reason=None))
    frame = dict(sku="synthetic", source_kind="product", source_id="synthetic", image_sha256="a" * 64,
                 bytes_sha256="a" * 64, image_url="https://example.invalid/frame.jpg", crop=None)
    manifest = dict(version="visible_item_capture.v1", dataset_revision="b" * 40, dataset_sha256="c" * 64,
                    selection_manifest_sha256="d" * 64, records={"fixture": frame})
    receipt = dict(version="visible_item_capture_receipt.v1", capture_manifest_sha256=sha(manifest),
                   dataset_revision=manifest["dataset_revision"], dataset_sha256=manifest["dataset_sha256"],
                   verification="actual_bytes_sha256", reviewer="synthetic-only", evidence_commit="e" * 40,
                   verified_capture_ids=["fixture"])
    record = Ф.спостереження(raw, sku=frame["sku"], image_sha256=frame["image_sha256"], image_url=frame["image_url"],
                            crop=None, model_id="synthetic", model_revision="fixture", capture_id="fixture",
                            capture_manifest_sha256=sha(manifest))
    return record, manifest, receipt


if __name__ == "__main__":
    print("Синтетична фікстура, не фото-приймання")
