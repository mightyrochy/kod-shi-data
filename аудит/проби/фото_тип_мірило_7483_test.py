"""Тільки синтетичні unit-перевірки evaluator7483; це не приймання фотографій."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

import фото_тип_мірило_7483 as М
from фото_тип_контракт import пакет_контракту, спостереження, перевірити_відповідь, канонічні_байти


class МірилоПілота(unittest.TestCase):
    """Перевірити відмови на підміні походження, хибному типі й неповній вибірці."""

    def setUp(self):
        """Побудувати120 явно синтетичних рядків без реальних фото чи моделей."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.manifest, self.results, annotations = [], [], []
        self.reviewer = dict(id="synthetic-unit-reviewer", session_id="synthetic-eye-session", model="synthetic-eye-model")
        for i in range(120):
            real = i < 100
            sample_id = f"synthetic-unit-{i:03d}"
            frame = ("NOT A PHOTO; SYNTHETIC UNIT FIXTURE " + sample_id).encode()
            filename = f"{i}.synthetic"
            (self.base / filename).write_bytes(frame)
            row = dict(protocol=М.ПРОТОКОЛ, synthetic=True, sample_id=sample_id,
                blind_id=М.sha256(sample_id.encode())[:16], sku=f"unit-sku-{i}" if real else None,
                source_id=f"synthetic-service-{i}" if not real else None,
                source_kind="product" if real else "service_control",
                role="real" if real else "negative", stratum="synthetic_unit", calibration=i<40,
                frame_target="form", crop=None, image_url=f"https://synthetic.invalid/{i}.png",
                image_sha256=М.sha256(frame), prepared_path=filename, prepare_status="ready",
                known_old_metadata=dict(oldconfirmed=i<30, old_photo_slot="пояс", catalog_slot="пояс"))
            self.manifest.append(row)
            annotations.append(dict(blind_id=row["blind_id"], image_sha256=row["image_sha256"],
                status="resolved" if real else "target_not_visible", item_type="belt" if real else None,
                reason=None if real else "not_visible", reviewer=deepcopy(self.reviewer), blind=True,
                actual_image_bytes_reviewed=True, evidence_id="SYNTHETIC-NOT-REAL-EYE",
                reviewed_at_utc="2026-10-18T00:00:00Z"))
            self.results.append(self.result(row, "belt" if real else None))
        self.gold = json.loads((Path(__file__).with_name("фото_тип_7483_fixtures") / "gold-template.json").read_text())
        self.gold["annotations"] = annotations
        self.hashes = dict(prepared_manifest_sha256="1"*64, gold_sha256="2"*64)
        self.captures = dict(version="visible_item_capture.v1", dataset_revision="0"*40,
            dataset_sha256="4"*64, selection_manifest_sha256="5"*64, records={row["sample_id"]:dict(
                **{k:row[k] for k in ("sku","source_id","source_kind","image_sha256","image_url","crop")},
                bytes_sha256=row["image_sha256"]) for row in self.manifest})
        self.capture_hash = М.sha256(канонічні_байти(self.captures))
        self.receipt = dict(protocol=М.ПРОТОКОЛ, **self.hashes, blind=True, reviewer="synthetic-root",
            eye_reviewer=deepcopy(self.reviewer), evidence_commit="0"*40, version="visible_item_capture_receipt.v1",
            dataset_revision=self.captures["dataset_revision"], dataset_sha256=self.captures["dataset_sha256"],
            capture_manifest_sha256=self.capture_hash, verification="actual_bytes_sha256",
            verified_capture_ids=[r["sample_id"] for r in self.manifest],
            rows=[dict(sample_id=r["sample_id"], image_sha256=r["image_sha256"]) for r in self.manifest])
        self.hashes["receipt_file_sha256"] = М.sha256(json.dumps(self.receipt).encode())
        for row, result in zip(self.manifest, self.results):
            result["gold_receipt_sha256"] = self.hashes["receipt_file_sha256"]
            result["capture"] = dict(id=row["sample_id"], manifest_sha256=self.capture_hash)
            if result["contract_record"]:
                result["contract_record"]["capture"] = dict(id=row["sample_id"], manifest_sha256=self.capture_hash)

    def result(self, row, code, unknown_reason=None):
        """Створити raw/обгортку спільним producer, не дублюючи його перевірку."""
        observation = (dict(target="unique", item_type=code, bbox=[0,0,1000,1000], reason=None)
                       if code else dict(target="unique",item_type="unknown",bbox=[0,0,1000,1000],reason=unknown_reason)
                       if unknown_reason else dict(target="not_visible", item_type="unknown", bbox=None, reason="not_visible"))
        raw = json.dumps(observation)
        record = (спостереження(raw, sku=row["sku"], image_sha256=row["image_sha256"], image_url=row["image_url"],
                  crop=None, model_id="synthetic-qwen", model_revision="synthetic-revision",
                  capture_id=row["sample_id"] if hasattr(self,"capture_hash") else None,
                  capture_manifest_sha256=getattr(self,"capture_hash",None)) if row["role"] == "real" else None)
        body = dict(model="synthetic-qwen", usage=dict(prompt_tokens=100,completion_tokens=5),
                    choices=[dict(message=dict(content=raw),finish_reason="stop")])
        body_text = json.dumps(body)
        return dict(**{k: row[k] for k in ("protocol","sample_id","sku","image_url","image_sha256","frame_target","crop","role","stratum","calibration","source_kind","source_id")},
            gold_receipt_sha256=getattr(self,"hashes",{}).get("receipt_file_sha256"),
            capture=dict(id=row["sample_id"],manifest_sha256=getattr(self,"capture_hash",None)),
            run_id="synthetic-run", invocation_id="synthetic-invocation", primary_invocation_id="synthetic-invocation", model=dict(id="synthetic-qwen", revision="synthetic-revision"),
            hashes=пакет_контракту()["hashes"], cache_key=row["sample_id"], attempt_id=row["sample_id"],
            request_performed=True, actual_request_count=1, status=перевірити_відповідь(raw)["status"],
            observation=observation, contract_record=record, raw_response=body, raw_response_text=body_text,raw_response_bytes_sha256=М.sha256(body_text.encode()),
            model_text=raw, usage=dict(prompt_tokens=100, completion_tokens=5), latency_ms=1000,
            wall_started_utc="2026-10-18T00:01:00Z", wall_finished_utc="2026-10-18T00:01:01Z", error=None, reused=False)

    def evaluate(self):
        """Оцінити саме fixture; photo_acceptance ніколи не може бути true."""
        report = М.оцінити(self.manifest, self.gold, self.results, self.receipt,
                          кадри=self.captures, файли=self.hashes, база=self.base, ціни=[2, 4])
        self.assertFalse(report["photo_acceptance"])
        return report

    def kinds(self, report):
        """Повернути класи реальних відмов приладу для прицільної звірки."""
        return {e["kind"] for e in report["errors"]}

    def test_perfect_unit_never_photo_acceptance(self):
        r = self.evaluate()
        self.assertEqual(r["status"], "SYNTHETIC_ONLY")
        self.assertTrue(all(r["criteria"].values()))
        self.assertEqual((r["counts"]["N"],r["counts"]["coded"],r["counts"]["unknown"]),(120,100,20))
        self.assertIsNone(r["paired"]["population_after"])
        self.assertEqual(r["timings_and_cost"]["fixture_q"],120)
        self.assertAlmostEqual(r["timings_and_cost"]["fixture_cost_formula_result"], .0264)

    def test_wrong_accepted_type_is_not_hidden_by_catalogue(self):
        self.results[40] = self.result(self.manifest[40], "sneakers")
        r=self.evaluate(); self.assertEqual(r["status"],"FAIL")
        self.assertEqual(r["metrics"]["wrong_accepted"],1)

    def test_catalogue_record_cannot_impersonate_photo(self):
        self.results[40]["contract_record"]["producer"]["kind"]="catalogue"
        r=self.evaluate(); self.assertIn("invalid_photo_record",self.kinds(r))
        self.assertEqual(r["counts"]["coded"],99)

    def test_service_control_never_creates_sku_overlay(self):
        self.results[100]=self.result(self.manifest[100],"belt")
        r=self.evaluate(); self.assertEqual(r["metrics"]["false_confirmation"],1)
        self.assertEqual(r["status"],"FAIL")
        self.assertIsNone(self.results[100]["contract_record"])

    def test_missing_or_pending_gold_is_incomplete(self):
        self.gold["annotations"].pop()
        self.assertEqual(self.evaluate()["status"],"INCOMPLETE")
        self.gold["annotations"][0]["status"]="pending_eye_annotations"
        r=self.evaluate();self.assertEqual(r["status"],"INCOMPLETE")

    def test_actual_bytes_not_self_asserted_hash(self):
        (self.base/self.manifest[0]["prepared_path"]).write_bytes(b"REPLACED")
        r=self.evaluate();self.assertIn("actual_image_hash",self.kinds(r))
        self.assertEqual(r["status"],"FAIL")

    def test_receipt_must_match_frozen_gold_file(self):
        self.receipt["gold_sha256"]="3"*64
        self.assertIn("receipt_file_hash",self.kinds(self.evaluate()))

    def test_coverage_boundary_and_old_correct_are_separate(self):
        for i in range(40,45):self.results[i]=self.result(self.manifest[i],None)
        r=self.evaluate();self.assertTrue(r["criteria"]["resolvable_coverage_95"])
        self.results[45]=self.result(self.manifest[45],None)
        self.assertFalse(self.evaluate()["criteria"]["resolvable_coverage_95"])
        self.results=[self.result(row,"belt" if i<100 else None) for i,row in enumerate(self.manifest)]
        self.results[0]=self.result(self.manifest[0],None)
        r=self.evaluate();self.assertTrue(r["criteria"]["resolvable_coverage_95"])
        self.assertFalse(r["criteria"]["old_correct_preserved_100"])

    def test_zero_old_correct_is_not_evaluable(self):
        for row in self.manifest:row["known_old_metadata"]["oldconfirmed"]=False
        r=self.evaluate();self.assertEqual(r["status"],"INCOMPLETE")
        self.assertIn("old_correct",r["not_evaluable"])
        self.assertIsNone(r["metrics"]["old_correct_preservation"])

    def test_duplicate_ids_and_blind_leak_fail(self):
        self.gold["annotations"][0]["sku"]="leaked-catalogue-sku"
        self.assertIn("gold_not_blind_payload",self.kinds(self.evaluate()))
        self.manifest[-1]=deepcopy(self.manifest[-2])
        self.assertIn("invalid_or_duplicate_id",self.kinds(self.evaluate()))

    def test_replay_and_unknown_usage_are_not_zero_token_measurement(self):
        self.results[0].update(reused=True,request_performed=False,actual_request_count=0)
        self.results[1]["usage"]=None
        self.results[1]["raw_response"]["usage"]=None
        self.results[1]["raw_response_text"]=json.dumps(self.results[1]["raw_response"])
        self.results[1]["raw_response_bytes_sha256"]=М.sha256(self.results[1]["raw_response_text"].encode())
        r=self.evaluate()["timings_and_cost"]
        self.assertEqual(r["fixture_q"],119);self.assertIsNone(r["input_tokens"])
        self.assertIsNone(r["observed_cost"])

    def test_raw_metadata_tampering_and_infer_before_eye_fail(self):
        self.results[0]["raw_response"]["choices"][0]["message"]["content"]="{}"
        self.assertIn("outer_raw_record_mismatch",self.kinds(self.evaluate()))
        self.results[1]["wall_started_utc"]="2026-10-17T23:00:00Z"
        self.assertIn("pipeline_time_order",self.kinds(self.evaluate()))

    def test_zero_resolvable_and_no_old_correct_cannot_pass(self):
        for i in range(100):
            self.gold["annotations"][i].update(status="ambiguous", item_type=None, reason="multiple_objects")
            self.results[i]=self.result(self.manifest[i],None)
        r=self.evaluate();self.assertEqual(r["status"],"INCOMPLETE")
        self.assertIn("resolvable",r["not_evaluable"])
        self.assertIsNone(r["metrics"]["coverage"])

    def test_capture_receipt_and_exact_image_join_are_required(self):
        self.receipt["capture_manifest_sha256"]="0"*64
        r=self.evaluate();self.assertIn("capture_receipt",self.kinds(r))
        self.assertEqual(r["counts"]["coded"],0)
        self.assertEqual(r["unknown_reasons"]["receipt_not_verified"],120)

    def test_schema_invalid_output_is_explicit_unknown_not_confirmation(self):
        r=self.results[40];raw="not json"
        r.update(status="invalid",observation=None,model_text=raw,
                 raw_response=dict(model="synthetic-qwen",usage=dict(prompt_tokens=100,completion_tokens=5),choices=[dict(message=dict(content=raw),finish_reason="stop")]))
        r["raw_response_text"]=json.dumps(r["raw_response"])
        r["raw_response_bytes_sha256"]=М.sha256(r["raw_response_text"].encode())
        row=self.manifest[40]
        r["contract_record"]=спостереження(raw,sku=row["sku"],image_sha256=row["image_sha256"],
            image_url=row["image_url"],crop=None,model_id="synthetic-qwen",model_revision="synthetic-revision",
            capture_id=row["sample_id"],capture_manifest_sha256=self.capture_hash)
        result=self.evaluate();self.assertEqual(result["status"],"SYNTHETIC_ONLY")
        self.assertEqual(result["unknown_reasons"]["invalid_schema"],1)
        self.assertEqual(result["metrics"]["false_confirmation"],0)

    def test_missing_model_revision_and_contract_hash_fail(self):
        self.results[0]["model"]["revision"]=""
        self.results[1]["hashes"]["schema_sha256"]="0"*64
        r=self.evaluate();self.assertIn("model_identity",self.kinds(r))
        self.assertIn("inference_contract_hash",self.kinds(r))

    def test_cli_frozen_files_and_synthetic_nonzero_exit(self):
        paths={k:self.base/(k+".json") for k in ("manifest","gold","receipt","captures","results","output")}
        for key,rows in (("manifest",self.manifest),("results",self.results)):
            paths[key].write_text("".join(json.dumps(r)+"\n" for r in rows))
        paths["gold"].write_text(json.dumps(self.gold))
        paths["captures"].write_text(json.dumps(self.captures))
        self.receipt.update(prepared_manifest_sha256=М.sha256(paths["manifest"].read_bytes()),
                            gold_sha256=М.sha256(paths["gold"].read_bytes()))
        paths["receipt"].write_text(json.dumps(self.receipt))
        for row in self.results:row["gold_receipt_sha256"]=М.sha256(paths["receipt"].read_bytes())
        paths["results"].write_text("".join(json.dumps(r)+"\n" for r in self.results))
        args=[sys.executable,str(Path(М.__file__).resolve())]
        for key,path in paths.items():args.extend(["--"+key,str(path)])
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,2,run.stderr)
        report=json.loads(paths["output"].read_text())
        self.assertEqual(report["status"],"SYNTHETIC_ONLY");self.assertFalse(report["photo_acceptance"])
        paths["gold"].write_text(paths["gold"].read_text()+"\n")
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,1,run.stderr)
        self.assertIn("receipt_file_hash",self.kinds(json.loads(paths["output"].read_text())))

    def test_duplicate_json_keys_and_nan_do_not_silently_parse(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.assertRaises(ValueError):М._json(raw)

    def test_correct_photo_is_not_necessarily_catalogue_confirmation(self):
        self.manifest[40]["known_old_metadata"]["catalog_slot"]="взуття"
        r=self.evaluate()
        confirmed=sum(n for key,n in r["paired"]["transitions"].items() if key.endswith("_to_confirmed"))
        self.assertEqual(r["metrics"]["correct"],100)
        self.assertEqual(r["paired"]["pilot_new_confirmed"],99)
        self.assertEqual(confirmed,99)
        self.assertTrue(r["ledger"][40]["correct"])
        self.assertFalse(r["ledger"][40]["preview_confirmed"])
        self.assertEqual(r["metrics"]["false_confirmation"],0)

    def test_matching_wrong_catalogue_is_a_false_confirmation(self):
        self.manifest[40]["known_old_metadata"]["catalog_slot"]="взуття"
        self.results[40]=self.result(self.manifest[40],"sneakers")
        r=self.evaluate()
        confirmed=sum(n for key,n in r["paired"]["transitions"].items() if key.endswith("_to_confirmed"))
        self.assertEqual(r["metrics"]["correct"],99)
        self.assertEqual(r["paired"]["pilot_new_confirmed"],confirmed)
        self.assertEqual(confirmed,100)
        self.assertEqual(r["metrics"]["false_confirmation"],1)
        self.assertEqual(r["status"],"FAIL")

    def test_blind_gold_does_not_need_hidden_source_target(self):
        for row,result in zip(self.manifest,self.results):
            if row["role"] == "negative":
                row["frame_target"]="service_candidate"
                result["frame_target"]="service_candidate"
        self.assertTrue(all("frame_target" not in annotation for annotation in self.gold["annotations"]))
        r=self.evaluate();self.assertEqual(r["status"],"SYNTHETIC_ONLY")
        self.assertTrue(all(r["criteria"].values()))
        self.assertEqual(r["counts"]["coded"],100)

    def test_source_target_manifest_result_binding_stays_strict(self):
        self.manifest[100]["frame_target"]="service_candidate"
        self.results[100]["frame_target"]="form"
        r=self.evaluate();self.assertEqual(r["status"],"FAIL")
        errors=[e for e in r["errors"] if e["kind"] == "binding_mismatch"]
        self.assertTrue(any(e["input"] == "results" and e["field"] == "frame_target" for e in errors))

    def test_unique_unknown_gold_is_not_in_resolvable_denominator(self):
        for i,reason in zip((40,41,42),("occluded","too_small","taxonomy_gap")):
            self.gold["annotations"][i].update(status="unknown",item_type=None,reason=reason)
            self.results[i]=self.result(self.manifest[i],None,unknown_reason=reason)
        r=self.evaluate();self.assertEqual(r["status"],"SYNTHETIC_ONLY")
        self.assertEqual(r["denominators"]["resolvable"],97)
        self.assertEqual(r["metrics"]["coverage"],1)
        self.assertEqual(r["metrics"]["wrong_accepted"],0)
        self.assertEqual(r["gold_statuses"]["unknown"],3)
        for reason in ("occluded","too_small","taxonomy_gap"):
            self.assertEqual(r["unknown_reasons"][reason],1)

    def test_accepted_code_on_unknown_gold_is_still_wrong(self):
        self.gold["annotations"][40].update(status="unknown",item_type=None,reason="too_small")
        r=self.evaluate();self.assertEqual(r["status"],"FAIL")
        self.assertEqual(r["metrics"]["wrong_accepted"],1)
        self.assertEqual(r["metrics"]["false_confirmation"],1)

    def test_unique_unknown_does_not_relax_negative_cohort(self):
        self.gold["annotations"][100].update(status="unknown",item_type=None,reason="occluded")
        self.results[100]=self.result(self.manifest[100],None,unknown_reason="occluded")
        r=self.evaluate();self.assertEqual(r["status"],"FAIL")
        self.assertIn("negative_gold_not_negative",self.kinds(r))

    def test_unknown_gold_reason_comes_from_producer_schema(self):
        self.gold["annotations"][40].update(status="unknown",item_type=None,reason="unproven_guess")
        r=self.evaluate();self.assertEqual(r["status"],"FAIL")
        self.assertIn("gold_unknown_reason",self.kinds(r))


if __name__ == "__main__":
    unittest.main()
