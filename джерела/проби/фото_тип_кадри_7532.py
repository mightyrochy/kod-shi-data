"""7532: explicit sku:null обов'язковий; пропуск відхиляється без KeyError."""
from фото_тип_синтетика import *


if __name__ == "__main__":
    record, original, receipt = fixture()
    fields = ("sku", "source_kind", "source_id", "image_sha256", "bytes_sha256", "image_url", "crop")
    for kind in ("product", "service_control"):
        manifest = copy.deepcopy(original)
        frame = manifest["records"]["fixture"]
        frame.update(source_kind=kind, sku="synthetic" if kind == "product" else None)
        accepted = dict(receipt, capture_manifest_sha256=sha(manifest))
        assert Ф.перевірити_кадри(manifest, accepted)["status"] == "verified"
        assert Ф.перевірити_привязку(manifest, accepted, capture_id="fixture", sku=frame["sku"], image_url=frame["image_url"])["status"] == "verified"
        for field in fields:
            bad = copy.deepcopy(manifest)
            del bad["records"]["fixture"][field]
            seal = dict(receipt, capture_manifest_sha256=sha(bad))
            assert Ф.перевірити_кадри(bad, seal)["errors"] == ["invalid_capture_record"]
            bound = Ф.перевірити_привязку(bad, seal, capture_id="fixture", sku=frame["sku"], image_url=frame["image_url"])
            assert bound["status"] == "invalid" and bound["image_sha256"] is None
    print("SYNTHETIC_ONLY 7532: 14 missing required fields refused; explicit control sku:null verified; PASS")
