"""7533: actual runner capture writer → fixture receipt → optional reader; мережа замкнена."""
from фото_тип_синтетика import *
import importlib.util
from unittest.mock import patch


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "аудит/проби/фото_тип_пілот_7483.py"
    spec = importlib.util.spec_from_file_location("synthetic_photo_runner", path)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    original, _, receipt = fixture()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        selection = td / "selection.jsonl"
        runner.jsonl(selection, [dict(sample_id="fixture", sku="synthetic", role="real", calibration=False, image_url=original["image"]["url"])])
        runner.підготувати(selection, td / "selected.jsonl")
        with patch.object(runner, "http", lambda url, **kw: (b"synthetic-not-photo", url)), patch.object(runner, "кадр", lambda data: (1, 1, "image/png")), patch.object(runner, "експортувати_очам", lambda *a: {"ready": 1}):
            runner.завантажити(td / "selected.jsonl", td, "b" * 40)
        manifest = json.loads((td / "capture-manifest.json").read_text())
        frame = manifest["records"]["fixture"]
        receipt.update(capture_manifest_sha256=sha(manifest), dataset_sha256=manifest["dataset_sha256"])
        assert Ф.перевірити_кадри(manifest, receipt)["status"] == "verified"
        record = Ф.спостереження(original["raw_response"], sku=frame["sku"], image_sha256=frame["image_sha256"], image_url=frame["image_url"], crop=None, model_id="synthetic", model_revision="fixture", capture_id="fixture", capture_manifest_sha256=sha(manifest))
        for name, value in zip(Ф.ФАЙЛИ, (dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[record]), manifest, receipt)):
            (td / name).write_bytes(Ф.канонічні_байти(value))
        assert З.читати_фото_тип(str(td))["records"]["synthetic"]["item_type"] == "shirt"
        crop = dict(bbox=[0, 0, 1000, 1000], source="independent_visual_target", source_image_sha256="a" * 64)
        cropped = Ф.спостереження(original["raw_response"], sku=frame["sku"], image_sha256=frame["image_sha256"], image_url=frame["image_url"], crop=crop, model_id="synthetic", model_revision="fixture")
        assert Ф.перевірити_запис(cropped)["status"] == "classified"
    print("SYNTHETIC_ONLY actual capture writer/receipt/reader + validated external crop API: PASS; photos/models/HTTP=0")
