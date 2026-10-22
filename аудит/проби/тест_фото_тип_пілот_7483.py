"""Fake-local integration: справжні синтетичні PNG, жодної моделі/крамниці/gold-оцінки."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
import re
from pathlib import Path
import tempfile
import threading
import unittest

from PIL import Image
import фото_тип_пілот_7483 as Р

КОНТРАКТ = Path(__file__).parent / "фікстури_фото_тип_7483/контракт.py"


class Пілот(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.images = []
        for колір in range(5):
            buf = io.BytesIO()
            Image.new("RGB", (3, 3), (колір * 40, 0, 0)).save(buf, format="PNG")
            self.images.append(buf.getvalue())
        self.gets, self.posts, self.payloads = [], [], []
        тест = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                тест.gets.append(self.path)
                body = тест.images[int(self.path.rsplit("/", 1)[-1])] if self.path.startswith("/image/") else b"<html>not image</html>"
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                if self.path == "/redirect/v1/chat/completions":
                    self.send_response(302)
                    self.send_header("Location", "https://example.invalid/model")
                    self.end_headers()
                    return
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                тест.payloads.append(payload)
                data = base64.b64decode(payload["messages"][0]["content"][1]["image_url"]["url"].split(",", 1)[1])
                номер = тест.images.index(data)
                тест.posts.append(номер)
                content = {"target": "unique", "item_type": "dress_generic", "bbox": [0, 0, 1, 1], "reason": None}
                if номер == 1:
                    content.update(target="not_visible", item_type="unknown", bbox=None, reason="not_visible")
                elif номер == 2:
                    content.update(target="ambiguous", item_type="unknown", bbox=None, reason="multiple_objects")
                text = "bad JSON" if номер == 3 else json.dumps(content)
                out = {"model": getattr(тест, "response_model", payload["model"]), "choices": [{"message": {"content": text}, "finish_reason": "length" if номер == 4 else "stop"}]}
                if номер != 2:
                    out["usage"] = {"prompt_tokens": 12, "completion_tokens": 4}
                raw = json.dumps(out).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(raw)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d" % self.server.server_port
        self.selection = self.root / "selection.jsonl"
        rows = []
        for i in range(120):
            negative = i >= 100
            rows.append(dict(sample_id="fixture-%03d" % i, sku=None if negative else "SKU_SENTINEL_%03d" % i,
                role="negative" if negative else "real", source_kind="service_control" if negative else "product",
                source_id="fixture-service-%d" % i if negative else None, source_url=self.url + "/page/" + str(i),
                image_url=self.url + "/image/" + str(i % 5), ready_for_download=True,
                calibration=i < 33 or 100 <= i < 107, frame_target="form", source_sha="d" * 40,
                known_old_metadata={"catalog_type": "CATALOG_SENTINEL", "name": "NAME_SENTINEL"}))
        Р.jsonl(self.selection, rows)
        self.prepared = self.root / "selected.jsonl"
        Р.підготувати(self.selection, self.prepared)
        self.evidence = self.root / "evidence"
        Р.завантажити(self.prepared, self.evidence, "d" * 40)
        self.manifest = self.evidence / "prepared.jsonl"
        self.receipt = self.root / "receipt-fixture-not-photo-QA.json"
        self.make_receipt()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def make_receipt(self):
        # Лише транспортна фікстура, не справжня незалежна розмітка чи результат пілота.
        rows = Р.прочитати(self.manifest)
        capture = json.loads((self.evidence / "capture-manifest.json").read_text())
        value = dict(version="visible_item_capture_receipt.v1", protocol=Р.ПРОТОКОЛ, blind=True, reviewer="FIXTURE_NOT_QA", eye_reviewer={"id": "FIXTURE_NOT_QA", "session_id": "FIXTURE_SESSION_NOT_QA", "model": "fixture"},
            evidence_commit="f" * 40, gold_sha256="0" * 64,
            prepared_manifest_sha256=Р.хеш(self.manifest.read_bytes()),
            capture_manifest_sha256=Р.хеш(Р.канон(capture)), verified_capture_ids=[r["sample_id"] for r in rows],
            dataset_revision=capture["dataset_revision"], dataset_sha256=capture["dataset_sha256"],
            verification="actual_bytes_sha256", rows=[{"sample_id": r["sample_id"], "image_sha256": r.get("image_sha256")} for r in rows])
        Р.записати(self.receipt, value)

    def infer(self, **kwargs):
        return Р.виконати(self.manifest, self.receipt, kwargs.pop("contract", КОНТРАКТ),
            "fixture-local-model", kwargs.pop("revision", "fixture-revision-1"), self.url + "/v1",
            self.root / "inference", parallel=3, **kwargs)

    def test_dedup_resume_and_no_metadata_in_model_input(self):
        self.assertEqual(len(self.gets), 5)
        sha = Р.хеш(self.manifest.read_bytes())
        Р.завантажити(self.prepared, self.evidence, "d" * 40)
        self.assertEqual(Р.хеш(self.manifest.read_bytes()), sha)
        calibration = self.infer(phase="calibration")
        self.assertEqual((calibration["rows"], calibration["actual_requests"]), (40, 5))
        full = self.infer()
        self.assertEqual((full["rows"], full["actual_requests"]), (120, 0))
        self.assertEqual(len(self.posts), 5)
        self.assertEqual(len(list((self.root / "inference/runs").glob("*/run.json"))), 2)
        rows = [json.loads(x) for x in (self.root / "inference/results-all.jsonl").read_text().splitlines()]
        self.assertEqual(set(r["status"] for r in rows), {"classified", "unknown", "ambiguous", "invalid", "error"})
        self.assertTrue(all(r["contract_record"] is None for r in rows if r["role"] == "negative"))
        self.assertTrue(all(r["usage"] is None for r in rows if r["status"] == "ambiguous"))
        self.assertTrue(all(r["reused"] and not r["request_performed"] for r in rows))
        for r in rows:
            self.assertIsNotNone(r["latency_ms"])
            self.assertEqual(Р.хеш(r["raw_response_text"].encode()), r["raw_response_bytes_sha256"])
        for payload in self.payloads:
            wire = json.dumps(payload)
            self.assertNotIn("SKU_SENTINEL", wire)
            self.assertNotIn("CATALOG_SENTINEL", wire)
            self.assertNotIn("NAME_SENTINEL", wire)
            self.assertNotIn("gold", wire)
            self.assertEqual(len(payload["messages"][0]["content"]), 2)
            self.assertEqual(payload["response_format"]["type"], "json_schema")
        review = (self.evidence / "review-manifest.jsonl").read_text() + (self.evidence / "review.html").read_text()
        for marker in ("SKU_SENTINEL", "CATALOG_SENTINEL", "NAME_SENTINEL", self.url, '"role"'):
            self.assertNotIn(marker, review)
        self.assertEqual(self.infer(revision="fixture-revision-2")["actual_requests"], 5)

    def test_changed_prompt_invalidates_cache(self):
        self.infer()
        altered = self.root / "contract-changed.py"
        altered.write_text(КОНТРАКТ.read_text().replace("FIXTURE ONLY:", "FIXTURE CHANGED:"))
        self.assertEqual(self.infer(contract=altered)["actual_requests"], 5)

    def test_wrong_receipt_and_modified_bytes_block_before_requests(self):
        receipt = json.loads(self.receipt.read_text())
        receipt["prepared_manifest_sha256"] = "a" * 64
        Р.записати(self.receipt, receipt)
        with self.assertRaisesRegex(ValueError, "receipt"):
            self.infer()
        self.make_receipt()
        first = Р.прочитати(self.manifest)[0]
        (self.evidence / first["prepared_path"]).write_bytes(self.images[1])
        with self.assertRaisesRegex(ValueError, "changed"):
            self.infer()
        self.assertEqual(self.posts, [])

    def test_pending_and_oversized_manifest_not_inferred(self):
        with self.assertRaisesRegex(ValueError, "selection_manifest_hash"):
            Р.підготувати(self.selection, self.prepared, "0" * 64)
        rows = Р.прочитати(self.manifest)
        rows[-1]["prepare_status"] = "pending_input"
        Р.jsonl(self.manifest, rows)
        self.make_receipt()
        with self.assertRaisesRegex(ValueError, "not_ready"):
            self.infer()
        Р.jsonl(self.root / "too-many.jsonl", rows + [dict(rows[0], sample_id="extra")])
        with self.assertRaisesRegex(ValueError, "120"):
            Р.підготувати(self.root / "too-many.jsonl", self.root / "not-written.jsonl")
        self.assertEqual(self.posts, [])

    def test_independent_eye_identity_required_before_any_post(self):
        receipt = json.loads(self.receipt.read_text())
        invalid = [None, {}, "FIXTURE_NOT_QA"]
        for key in ("id", "session_id", "model"):
            invalid.append({k: v for k, v in receipt["eye_reviewer"].items() if k != key})
            invalid.extend({**receipt["eye_reviewer"], key: value} for value in (None, "", "   ", 1))
        invalid.append({**receipt["eye_reviewer"], "model": "fixture-local-model"})
        for eye in invalid:
            with self.subTest(eye=eye):
                Р.записати(self.receipt, {**receipt, "eye_reviewer": eye})
                with self.assertRaisesRegex(ValueError, "independent_eye"):
                    self.infer()
                self.assertEqual(self.posts, [])
        receipt.pop("eye_reviewer")
        Р.записати(self.receipt, receipt)
        with self.assertRaisesRegex(ValueError, "independent_eye"):
            self.infer()
        self.assertEqual(self.posts, [])

    def test_nonpixel_http200_rejected_and_no_proxy_or_redirect(self):
        rows = Р.прочитати(self.prepared)
        rows[0]["image_url"] = self.url + "/html"
        Р.jsonl(self.prepared, rows)
        Р.завантажити(self.prepared, self.evidence, "d" * 40)
        result = Р.прочитати(self.manifest)
        self.assertEqual(result[0]["prepare_status"], "error")
        for url in ("https://127.0.0.1:1234/v1", "http://example.invalid/v1", "http://user:secret@localhost/v1", "http://localhost/v1?x=1"):
            with self.assertRaises(ValueError):
                Р.локальна_адреса(url)
        with self.assertRaises(Exception):
            Р.http(self.url + "/redirect/v1/chat/completions", b"{}", переспрямування=False)
        self.assertEqual(self.posts, [])

    def test_blind_review_export_independent_directory(self):
        out = self.root / "blind-only"
        result = Р.експортувати_очам(self.manifest, out)
        self.assertEqual(result["ready"], 120)
        review = (out / "review-manifest.jsonl").read_text()
        self.assertNotIn("SKU_SENTINEL", review)
        self.assertNotIn("role", review)
        for row in [json.loads(line) for line in review.splitlines()]:
            self.assertEqual(Р.хеш((out / row["prepared_path"]).read_bytes()), row["image_sha256"])
        self.assertEqual(self.posts, [])

    def test_blind_export_order_does_not_reveal_source_groups(self):
        rows = Р.прочитати(self.manifest)
        out = self.root / "blind-sorted"
        Р.експортувати_очам(self.manifest, out)
        manifest_bytes = (out / "review-manifest.jsonl").read_bytes()
        html_bytes = (out / "review.html").read_bytes()
        ids = [r["blind_id"] for r in map(json.loads, manifest_bytes.splitlines())]
        self.assertEqual(ids, sorted(r["blind_id"] for r in rows))
        self.assertEqual(re.findall(r"<figcaption>(.*?)</figcaption>", html_bytes.decode()), ids)
        controls = {r["blind_id"] for r in rows if r["role"] == "negative"}
        self.assertNotEqual(set(ids[-20:]), controls)
        Р.jsonl(self.manifest, list(reversed(rows)))
        Р.експортувати_очам(self.manifest, out)
        self.assertEqual((out / "review-manifest.jsonl").read_bytes(), manifest_bytes)
        self.assertEqual((out / "review.html").read_bytes(), html_bytes)
        self.assertEqual(self.posts, [])

    def test_wrong_backend_model_never_produces_fact(self):
        self.response_model = "another-backend-model"
        result = self.infer()
        self.assertEqual(result["status_counts"]["error"], 120)
        rows = [json.loads(x) for x in (self.root / "inference/results-all.jsonl").read_text().splitlines()]
        self.assertTrue(all(r["contract_record"] is None for r in rows))
        self.assertTrue(all(r["error"]["code"] == "response_model_id_mismatch" for r in rows))

    @unittest.skipUnless(os.environ.get("PHOTO_TYPE_CONTRACT"), "окремий API власника не задано")
    def test_owner_contract_adapter(self):
        result = self.infer(contract=Path(os.environ["PHOTO_TYPE_CONTRACT"]))
        self.assertEqual(result["rows"], 120)
        rows = [json.loads(x) for x in (self.root / "inference/results-all.jsonl").read_text().splitlines()]
        classified = [r for r in rows if r["role"] == "real" and r["status"] == "classified"]
        self.assertTrue(classified)
        self.assertTrue(all(r["contract_record"]["capture"] == r["capture"] for r in classified))
        self.assertTrue(all(r["contract_record"] is None for r in rows if r["role"] == "negative"))

    def test_interrupted_claim_never_reissues_request(self):
        self.infer()
        cache = next((self.root / "inference/cache").glob("*.json"))
        value = json.loads(cache.read_text())
        Р.записати(cache, {k: value[k] for k in ("attempt_id", "cache_identity", "wall_started_utc")} | {"status": "in_progress"})
        count = len(self.posts)
        self.assertEqual(self.infer()["actual_requests"], 0)
        self.assertEqual(len(self.posts), count)
        rows = [json.loads(x) for x in (self.root / "inference/results-all.jsonl").read_text().splitlines()]
        self.assertTrue(any((r.get("error") or {}).get("code") == "interrupted_attempt_no_automatic_retry" for r in rows))


if __name__ == "__main__":
    unittest.main()
