"""Product та valid raw control експортуються без підробленого SKU для control."""
from фото_тип_синтетика import *
import subprocess


if __name__ == "__main__":
    record, manifest, receipt = fixture()
    frame = dict(manifest["records"]["fixture"], sku=None, source_kind="service_control", source_id="synthetic-control")
    manifest["records"]["control"] = frame
    digest = sha(manifest)
    record["capture"]["manifest_sha256"] = digest
    receipt.update(capture_manifest_sha256=digest, verified_capture_ids=["fixture", "control"])
    raw = json.dumps(dict(target="not_visible", item_type="unknown", bbox=None, reason="not_visible"))
    assert Ф.перевірити_відповідь(raw)["status"] == "unknown"
    rows = [dict(contract_record=record), dict(contract_record=None, source_kind="service_control", sku=None, model_text=raw)]
    with tempfile.TemporaryDirectory() as td:
        for name, value in (("capture", manifest), ("receipt", receipt)):
            Path(td, name + ".json").write_bytes(Ф.канонічні_байти(value))
        Path(td, "results.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
        output = Path(td, "overlay.json")
        run = subprocess.run([sys.executable, Ф.__file__, "--overlay", str(Path(td, "results.jsonl")),
                              "--captures", str(Path(td, "capture.json")), "--receipt", str(Path(td, "receipt.json")),
                              "--output", str(output)], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        got = json.loads(output.read_text())
        assert got["records"] == [record]
        assert json.loads(run.stdout)["unprojected"] == 0
    print("SYNTHETIC_ONLY 7532: product+null control CLI→1 product overlay, zero unprojected; PASS")
