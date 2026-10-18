#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Оцінити заморожений фото-пілот7483 без моделей, мережі й зміни продукту.

Gold надходить від незалежних очей на фактичних байтах. Синтетичні fixtures
перевіряють лише прилад і ніколи не дають фото-приймання або exit0.
"""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import слоти as СЛ

ПРОТОКОЛ = "photo-type-pilot-7483-v1"
ПІЛОТ = {"real": 100, "negative": 20}
СТАНИ_GOLD = {"resolved", "unknown", "ambiguous", "target_not_visible", "negative_coded_join_control"}


def _json(текст):
    """Не приймати повторні ключі або не-JSON числа у заморожених файлах."""
    def пари(значення):
        """Зберегти кожен ключ рівно один раз."""
        вихід = {}
        for ключ, значення in значення:
            if ключ in вихід:
                raise ValueError("duplicate_json_key:" + ключ)
            вихід[ключ] = значення
        return вихід
    def нечисло(значення):
        """Відхилити NaN та Infinity до обчислення будь-якої метрики."""
        raise ValueError("non_json_number:" + значення)
    return json.loads(текст, object_pairs_hook=пари, parse_constant=нечисло)


def sha256(байти):
    """Обчислити SHA фактичних байтів, а не текстового опису файлу."""
    return hashlib.sha256(байти).hexdigest()


def _індекс(рядки, назва, помилки, ключ="sample_id"):
    """Побудувати індекс без мовчазного перезапису повторних stable ID."""
    індекс = {}
    for р in рядки:
        ід = р.get(ключ) if isinstance(р, dict) else None
        if not isinstance(ід, str) or not ід.strip() or ід in індекс:
            помилки.append({"kind": "invalid_or_duplicate_id", "input": назва, "sample_id": ід})
            continue
        індекс[ід] = р
    return індекс


def _число(v):
    """Прийняти лише скінченне невід'ємне число, включно з нулем."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0


def _процентиль(значення, q):
    """Порахувати nearest-rank процентиль; порожня вибірка невідома."""
    return sorted(значення)[max(0, math.ceil(len(значення) * q) - 1)] if значення else None


def _час(значення):
    """Прочитати явний UTC timestamp без вгадування локальної зони."""
    if not isinstance(значення, str):
        return None
    try:
        час = datetime.fromisoformat(значення.replace("Z", "+00:00"))
        return час if час.tzinfo is not None and час.utcoffset().total_seconds() == 0 else None
    except ValueError:
        return None


def _збіг(м, р, поля, помилки, ід, джерело):
    """Перевірити точну прив'язку даних, не нормалізуючи іншу річ у цю."""
    for поле in поля:
        if поле not in м or р.get(поле) != м[поле]:
            помилки.append({"kind": "binding_mismatch", "input": джерело,
                            "sample_id": ід, "field": поле})


def _кошторис(рядки, ціни):
    """Порахувати фактичні запити й відомий usage; невідоме не стає нулем."""
    спроби, конфлікти = {}, []
    for р in рядки:
        if р.get("request_performed") is not True:
            continue
        ід = р.get("attempt_id")
        if not ід:
            конфлікти.append("missing_attempt_id")
            continue
        if ід in спроби and спроби[ід] != р:
            конфлікти.append("conflicting_attempt_id:" + ід)
        спроби.setdefault(ід, р)
    затримки = [р["latency_ms"] for р in спроби.values() if _число(р.get("latency_ms"))]
    вхід, вихід, відомі = 0, 0, 0
    for р in спроби.values():
        usage = р.get("usage") or {}
        if _число(usage.get("prompt_tokens")) and _число(usage.get("completion_tokens")):
            вхід += usage["prompt_tokens"]; вихід += usage["completion_tokens"]; відомі += 1
    повний = bool(спроби) and відомі == len(спроби)
    ціна = ((вхід * ціни[0] + вихід * ціни[1]) / 1_000_000
            if повний and ціни and all(_число(ц) for ц in ціни) else None)
    return dict(actual_q=len(спроби), reused_rows=sum(р.get("reused") is True for р in рядки),
                measured_latencies=len(затримки), latency_median_ms=statistics.median(затримки) if затримки else None,
                latency_p95_ms=_процентиль(затримки, .95), request_hours=sum(затримки) / 3_600_000 if затримки else None,
                usage_known_requests=відомі, input_tokens=вхід if повний else None,
                output_tokens=вихід if повний else None, observed_cost=ціна,
                cost_formula="(actual_input_tokens * input_rate_per_million + actual_output_tokens * output_rate_per_million) / 1000000",
                rates_per_million=ціни, errors=конфлікти)


def оцінити(маніфест, gold, результати, receipt, *, кадри, файли, база, ціни=None):
    """Звірити ланцюг, порахувати paired pilot і явний неповний/синтетичний стан."""
    from фото_тип_контракт import пакет_контракту, перевірити_кадри, перевірити_привязку, канонічні_байти
    if (not all(isinstance(р, list) and all(isinstance(x, dict) for x in р) for р in (маніфест, результати))
            or not all(isinstance(р, dict) for р in (gold, receipt, кадри, файли))
            or not isinstance(gold.get("annotations"), list)):
        raise ValueError("invalid_input_container")
    пакет = пакет_контракту()
    причини_невідомого = {п for варіант in пакет["schema"]["oneOf"]
        if варіант["properties"]["target"].get("enum") == ["unique"]
        and варіант["properties"]["item_type"].get("enum") == ["unknown"]
        for п in варіант["properties"]["reason"]["enum"]}
    помилки, неповне, ledger = [], [], []
    м = _індекс(маніфест, "manifest", помилки)
    blind = _індекс(gold.get("annotations", []), "gold_blind", помилки, ключ="blind_id")
    мапа = {р.get("blind_id"): ід for ід, р in м.items()}
    if len(мапа) != len(м) or None in мапа:
        помилки.append({"kind": "invalid_or_duplicate_blind_id"})
    з = {}
    for blind_id, р in blind.items():
        if blind_id not in мапа:
            помилки.append({"kind": "foreign_blind_id", "blind_id": blind_id})
        else:
            з[мапа[blind_id]] = р
    р = _індекс(результати, "results", помилки)
    receipt_рядки = _індекс(receipt.get("rows", []), "receipt", помилки)
    ролі = Counter(рядок.get("role") for рядок in м.values())
    if len(маніфест) != 120 or ролі != Counter(ПІЛОТ):
        помилки.append({"kind": "pilot_count", "actual": dict(ролі), "expected": ПІЛОТ})
    if sum(рядок.get("calibration") is True for рядок in м.values()) != 40:
        помилки.append({"kind": "calibration_count", "expected": 40})
    for назва, індекс in (("gold", з), ("results", р), ("receipt", receipt_рядки)):
        чужі = set(індекс) - set(м)
        if чужі:
            помилки.append({"kind": "foreign_ids", "input": назва, "sample_ids": sorted(чужі)})
        for ід in sorted(set(м) - set(індекс)):
            неповне.append({"kind": "missing_row", "input": назва, "sample_id": ід})
    for ключ in ("prepared_manifest_sha256", "gold_sha256"):
        if receipt.get(ключ) != файли.get(ключ) or not файли.get(ключ):
            помилки.append({"kind": "receipt_file_hash", "field": ключ})
    if receipt.get("blind") is not True or not receipt.get("eye_reviewer") or not receipt.get("evidence_commit"):
        помилки.append({"kind": "receipt_not_blind"})
    if gold.get("protocol") != ПРОТОКОЛ or receipt.get("protocol") != ПРОТОКОЛ:
        помилки.append({"kind": "protocol_mismatch"})
    синтетичне = gold.get("synthetic") is True
    if not синтетичне and any(рядок.get("synthetic") is True for рядок in м.values()):
        помилки.append({"kind": "synthetic_row_in_real_pilot"})
    if gold.get("synthetic") not in (True, False):
        помилки.append({"kind": "gold_synthetic_not_declared"})
    ланцюг = перевірити_кадри(кадри, receipt)
    if ланцюг["status"] != "verified":
        помилки.append({"kind": "capture_receipt", "errors": ланцюг["errors"]})
    if set(ланцюг["records"]) != set(м):
        помилки.append({"kind": "capture_ids_mismatch"})
    ланцюг_готовий = not помилки
    capture_sha = sha256(канонічні_байти(кадри))
    метрики = Counter({к: 0 for к in ("resolvable", "old_correct", "accepted", "correct", "old_correct_preserved", "wrong_accepted", "false_confirmation", "pilot_new_confirmed", "pilot_correct_new_confirmed")})
    переходи = Counter()
    for ід, оригінал in м.items():
        вхід = dict(оригінал, crop=оригінал.get("crop", (оригінал.get("target_binding") or {}).get("crop")))
        еталон, вихід = з.get(ід), р.get(ід)
        причина, код, правильний, старий_правильний = None, None, False, False
        frame_verified = False
        хибне_підтвердження = False
        підтверджено = False
        до = len(помилки)
        роль = вхід.get("role")
        if ((роль == "real" and not вхід.get("sku")) or not вхід.get("stratum") or вхід.get("protocol") != ПРОТОКОЛ
                or вхід.get("blind_id") != sha256(ід.encode())[:16]):
            помилки.append({"kind": "manifest_identity", "sample_id": ід})
        шлях = вхід.get("prepared_path")
        if вхід.get("prepare_status") != "ready" or not шлях:
            неповне.append({"kind": "frame_not_prepared", "sample_id": ід})
        else:
            файл = Path(шлях) if Path(шлях).is_absolute() else база / шлях
            try:
                if sha256(файл.read_bytes()) != вхід.get("image_sha256"):
                    помилки.append({"kind": "actual_image_hash", "sample_id": ід})
                else:
                    frame_verified = True
            except OSError:
                неповне.append({"kind": "actual_image_missing", "sample_id": ід})
        if receipt_рядки.get(ід, {}).get("image_sha256") != вхід.get("image_sha256"):
            помилки.append({"kind": "receipt_image_hash", "sample_id": ід})
        binding = перевірити_привязку(кадри, receipt, capture_id=ід, sku=вхід.get("sku"),
                                      image_url=вхід.get("image_url"), crop=вхід.get("crop"))
        if binding["status"] != "verified" or binding["image_sha256"] != вхід.get("image_sha256"):
            помилки.append({"kind": "capture_binding", "sample_id": ід, "errors": binding["errors"]})
        elif (ланцюг["records"][ід].get("source_kind") != вхід.get("source_kind")
                or ланцюг["records"][ід].get("source_id") != вхід.get("source_id")):
            помилки.append({"kind": "capture_source_identity", "sample_id": ід})
        розвязний = False
        if роль == "negative" and (вхід.get("source_kind") != "service_control" or not вхід.get("source_id") or вхід.get("sku") is not None):
            помилки.append({"kind": "negative_not_service_control", "sample_id": ід})
        if еталон is None or еталон.get("status") == "pending_eye_annotations":
            причина = "pending_eye_annotations"
            неповне.append({"kind": причина, "sample_id": ід})
        else:
            _збіг(вхід, еталон, ("image_sha256",), помилки, ід, "gold")
            reviewer = еталон.get("reviewer") or {}
            if any(к in еталон for к in ("sample_id", "sku", "role", "stratum", "known_old_metadata", "caption", "catalog_type_legacy", "model_response")):
                помилки.append({"kind": "gold_not_blind_payload", "sample_id": ід})
            if reviewer != receipt.get("eye_reviewer"):
                помилки.append({"kind": "gold_reviewer_receipt", "sample_id": ід})
            if (еталон.get("blind") is not True or еталон.get("actual_image_bytes_reviewed") is not True
                    or not all(reviewer.get(к) for к in ("id", "session_id", "model"))
                    or not еталон.get("evidence_id") or _час(еталон.get("reviewed_at_utc")) is None):
                помилки.append({"kind": "gold_not_independent_eye", "sample_id": ід})
            стан = еталон.get("status")
            if стан == "unknown" and еталон.get("reason") not in причини_невідомого:
                помилки.append({"kind": "gold_unknown_reason", "sample_id": ід})
            if стан not in СТАНИ_GOLD:
                помилки.append({"kind": "gold_status", "sample_id": ід})
            if стан == "negative_coded_join_control":
                if not синтетичне or роль != "negative" or еталон.get("synthetic_control") is not True or not еталон.get("expected_condition"):
                    помилки.append({"kind": "negative_without_explicit_condition", "sample_id": ід})
            elif роль == "negative" and стан not in ("ambiguous", "target_not_visible"):
                помилки.append({"kind": "negative_gold_not_negative", "sample_id": ід})
            розвязний = роль == "real" and стан == "resolved"
            if стан != "resolved" and not еталон.get("reason"):
                помилки.append({"kind": "gold_unknown_without_reason", "sample_id": ід})
            if not розвязний and еталон.get("item_type") is not None:
                помилки.append({"kind": "unresolved_gold_has_type", "sample_id": ід})
            if розвязний and еталон.get("item_type") not in СЛ.СЛОТ_ТИПУ:
                помилки.append({"kind": "gold_not_taxonomy_code", "sample_id": ід})
            if розвязний:
                метрики["resolvable"] += 1
            попередній = вхід.get("known_old_metadata") or {}
            старий_правильний = (розвязний and попередній.get("oldconfirmed") is True
                and попередній.get("old_photo_slot") == СЛ.КЛЮЧІ.get(СЛ.СЛОТ_ТИПУ.get(еталон.get("item_type"))))
            if старий_правильний:
                метрики["old_correct"] += 1
        if вихід is None:
            причина = причина or "pending_inference"
        else:
            _збіг(вхід, вихід, ("sample_id", "sku", "image_url", "image_sha256", "frame_target", "crop", "role", "stratum", "calibration", "source_kind", "source_id"), помилки, ід, "results")
            if вихід.get("protocol") != ПРОТОКОЛ or вихід.get("hashes") != пакет["hashes"]:
                помилки.append({"kind": "inference_contract_hash", "sample_id": ід})
            if вихід.get("gold_receipt_sha256") != файли.get("receipt_file_sha256") or not файли.get("receipt_file_sha256"):
                помилки.append({"kind": "inference_receipt_hash", "sample_id": ід})
            if вихід.get("capture") != {"id": ід, "manifest_sha256": capture_sha}:
                помилки.append({"kind": "inference_capture_reference", "sample_id": ід})
            model = вихід.get("model") or {}
            if (not вихід.get("run_id") or not вихід.get("invocation_id") or not вихід.get("primary_invocation_id")
                    or not model.get("id") or not model.get("revision")
                    or not вихід.get("cache_key") or not вихід.get("attempt_id")
                    or type(вихід.get("request_performed")) is not bool
                    or type(вихід.get("actual_request_count")) is not int
                    or вихід.get("actual_request_count") != int(вихід.get("request_performed") is True)
                    or type(вихід.get("reused")) is not bool):
                помилки.append({"kind": "model_identity", "sample_id": ід})
            початок, кінець = _час(вихід.get("wall_started_utc")), _час(вихід.get("wall_finished_utc"))
            око = _час((еталон or {}).get("reviewed_at_utc"))
            if вихід.get("status") == "error" and (not кінець or not _число(вихід.get("latency_ms"))):
                неповне.append({"kind": "interrupted_inference_timing", "sample_id": ід})
            elif not початок or not кінець or кінець < початок or (око and початок < око):
                помилки.append({"kind": "pipeline_time_order", "sample_id": ід})
            if вихід.get("status") != "error" and not _число(вихід.get("latency_ms")):
                помилки.append({"kind": "invalid_latency", "sample_id": ід})
            if reviewer := (еталон or {}).get("reviewer"):
                if reviewer.get("model") == model.get("id") or reviewer.get("session_id") == вихід.get("run_id"):
                    помилки.append({"kind": "gold_not_independent", "sample_id": ід})
            # producer повторно перевіряє raw-відповідь і весь ланцюг, без fallback з опису.
            код, причина = _код_результату(вихід, вхід, помилки, ід)
            cap = (вихід.get("contract_record") or {}).get("capture")
            if роль == "real" and вихід.get("status") != "error" and cap != {"id": ід, "manifest_sha256": capture_sha}:
                помилки.append({"kind": "inference_capture_reference", "sample_id": ід})
            if код is not None and len(помилки) == до and frame_verified and ланцюг_готовий:
                метрики["accepted"] += 1
                правильний = розвязний and еталон.get("item_type") == код
                if правильний:
                    метрики["correct"] += 1
                    if старий_правильний:
                        метрики["old_correct_preserved"] += 1
                elif еталон and еталон.get("status") != "pending_eye_annotations":
                    метрики["wrong_accepted"] += 1
                if роль == "negative":
                    хибне_підтвердження = True
                каталог = (вхід.get("known_old_metadata") or {}).get("catalog_slot")
                if роль == "real" and каталог == СЛ.КЛЮЧІ.get(СЛ.СЛОТ_ТИПУ.get(код)):
                    підтверджено = True
                    метрики["pilot_new_confirmed"] += 1
                    if правильний:
                        метрики["pilot_correct_new_confirmed"] += 1
                    elif еталон and еталон.get("status") != "pending_eye_annotations":
                        хибне_підтвердження = True
        if len(помилки) > до:
            if вихід and вихід.get("status") == "classified":
                хибне_підтвердження = True
            код = None; причина = "invalid_provenance_or_contract"
        if not ланцюг_готовий:
            код = None; причина = "receipt_not_verified"
            хибне_підтвердження = bool(вихід and вихід.get("status") == "classified")
        if not frame_verified:
            код = None; причина = "frame_not_verified"
        if хибне_підтвердження:
            метрики["false_confirmation"] += 1
        причина = причина or (None if код else "unknown")
        ledger.append(dict(sample_id=ід, sku=вхід.get("sku"), role=роль, status="coded" if код else "unknown",
                           item_type=код, unknown_reason=причина, gold_status=(еталон or {}).get("status"),
                           correct=правильний, old_correct=старий_правильний, preview_confirmed=підтверджено))
        if роль == "real":
            попередній = (вхід.get("known_old_metadata") or {}).get("oldconfirmed")
            переходи[f"old_{попередній}_to_" + ("confirmed" if підтверджено else "unknown_or_not_confirmed")] += 1
    відомі = sum(р["status"] == "coded" for р in ledger)
    покриття = метрики["correct"] / метрики["resolvable"] if метрики["resolvable"] else None
    збереження = метрики["old_correct_preserved"] / метрики["old_correct"] if метрики["old_correct"] else None
    критерії = dict(wrong_accepted_zero=метрики["wrong_accepted"] == 0,
                    false_confirmation_zero=метрики["false_confirmation"] == 0,
                    resolvable_coverage_95=покриття is not None and покриття >= .95,
                    old_correct_preserved_100=збереження == 1)
    кошторис = _кошторис(результати, ціни)
    кошторис["measurement_kind"] = "synthetic_unit_values" if синтетичне else "recorded_actual_requests"
    if синтетичне:
        кошторис["fixture_q"] = кошторис["actual_q"]
        кошторис["fixture_cost_formula_result"] = кошторис["observed_cost"]
        кошторис["actual_q"] = None
        кошторис["observed_cost"] = None
    кошторис["full_corpus_run"] = False
    кошторис["full_url_count_reference"] = 9486
    кошторис["projection_formula_only"] = "9486 * representative_mean_ms_per_actual_request / 3600000; same-work-mix assumption, not measured population time"
    помилки.extend({"kind": "timing_or_usage", "detail": е} for е in кошторис["errors"])
    not_evaluable = [к for к in ("resolvable", "old_correct") if not метрики[к]]
    стан = ("FAIL" if помилки else "INCOMPLETE" if неповне or not_evaluable else
            "FAIL" if not all(критерії.values()) else "SYNTHETIC_ONLY" if синтетичне else "PASS")
    return dict(protocol=ПРОТОКОЛ, evaluator_source_sha256=sha256(Path(__file__).read_bytes()),
                status=стан, photo_acceptance=стан == "PASS", synthetic=синтетичне,
                scope="pilot_only", population_precision_estimate=None, not_evaluable=not_evaluable, criteria=критерії, metrics=dict(метрики, coverage=покриття,
                precision=метрики["correct"] / метрики["accepted"] if метрики["accepted"] else None,
                old_correct_preservation=збереження),
                counts=dict(N=len(ledger), coded=відомі, unknown=len(ledger)-відомі, roles=dict(ролі),
                            unique_image_hashes=len({р.get("image_sha256") for р in м.values() if р.get("image_sha256")})),
                unknown_reasons=dict(Counter(р["unknown_reason"] for р in ledger if р["status"] == "unknown")),
                paired=dict(scope="observed_pilot_real_only", transitions=dict(переходи),
                    baseline_total_old_confirmed=8668,
                    pilot_old_confirmed=sum(р.get("role") == "real" and (р.get("known_old_metadata") or {}).get("oldconfirmed") is True for р in м.values()),
                    pilot_old_correct=метрики["old_correct"], pilot_new_confirmed=метрики["pilot_new_confirmed"],
                    pilot_correct_new_confirmed=метрики["pilot_correct_new_confirmed"],
                    population_after=None, population_after_status="not_measured"),
                activation="preview_only_no_photo_slot_overlay",
                denominators=dict(real=ролі["real"], negative=ролі["negative"],
                                  resolvable=метрики["resolvable"], old_correct=метрики["old_correct"], accepted=метрики["accepted"]),
                gold_statuses=dict(Counter(р.get("status") for р in з.values())),
                gold_unknown_reasons=dict(Counter(р.get("reason") or р.get("status") for р in з.values() if р.get("status") != "resolved")),
                result_statuses=dict(Counter(р.get("status") for р in результати)),
                non_projected_reasons=dict(Counter(р["unknown_reason"] for р in ledger if р["status"] == "unknown")),
                timings_and_cost=кошторис, hashes=пакет["hashes"], input_hashes=файли,
                errors=помилки, incomplete=неповне, ledger=ledger)


def _код_результату(результат, вхід, помилки, ід):
    """Використати producer як єдиного читача raw та доказу походження фото."""
    from фото_тип_контракт import проєкція, перевірити_відповідь
    if результат.get("status") == "error":
        if not результат.get("error"):
            помилки.append({"kind": "error_without_reason", "sample_id": ід})
        return None, "inference_error:" + str((результат.get("error") or {}).get("code", "unspecified"))
    запис = результат.get("contract_record")
    if вхід.get("role") == "negative":
        if запис is not None:
            помилки.append({"kind": "negative_must_not_be_sku_fact", "sample_id": ід})
        перевірка = перевірити_відповідь(результат.get("model_text"))
    else:
        перевірка = проєкція(запис, sku=вхід.get("sku"), image_sha256=вхід.get("image_sha256"),
                             image_url=вхід.get("image_url"), crop=вхід.get("crop"))
    raw_перевірка = перевірити_відповідь(результат.get("model_text"))
    invalid_schema = (перевірка["status"] == raw_перевірка["status"] == результат.get("status") == "invalid"
                      and перевірка["errors"] == raw_перевірка["errors"])
    if перевірка["status"] == "invalid" and not invalid_schema:
        помилки.append({"kind": "invalid_photo_record", "sample_id": ід, "errors": перевірка["errors"]})
        return None, "invalid_photo_record"
    raw = результат.get("raw_response")
    raw_text = результат.get("raw_response_text")
    try:
        raw_verified = (isinstance(raw_text, str)
            and sha256(raw_text.encode("utf-8")) == результат.get("raw_response_bytes_sha256")
            and _json(raw_text) == raw)
    except (ValueError, TypeError):
        raw_verified = False
    if not raw_verified:
        помилки.append({"kind": "http_raw_hash_or_json", "sample_id": ід})
    if not isinstance(raw, dict) or raw.get("model") != (результат.get("model") or {}).get("id"):
        помилки.append({"kind": "response_model_mismatch", "sample_id": ід})
    if isinstance(raw, dict) and raw.get("usage") != результат.get("usage"):
        помилки.append({"kind": "usage_raw_mismatch", "sample_id": ід})
    try:
        if raw["choices"][0].get("finish_reason") != "stop":
            помилки.append({"kind": "incomplete_model_output", "sample_id": ід})
        текст = raw["choices"][0]["message"]["content"]
    except (TypeError, KeyError, IndexError):
        текст = None
    observation = перевірка.get("observation") if вхід.get("role") == "negative" else запис["visible_item_type"]
    if (текст is None or текст != результат.get("model_text")
            or результат.get("observation") != observation
            or результат.get("status") != перевірка["status"]):
        помилки.append({"kind": "outer_raw_record_mismatch", "sample_id": ід})
        return None, "outer_raw_record_mismatch"
    if запис:
        автор = запис["producer"]
        if (текст != запис["raw_response"] or автор["model_id"] != (результат.get("model") or {}).get("id")
                or автор["model_revision"] != (результат.get("model") or {}).get("revision")):
            помилки.append({"kind": "outer_producer_mismatch", "sample_id": ід})
            return None, "outer_producer_mismatch"
    if перевірка["status"] == "classified":
        return observation["item_type"], None
    return None, "invalid_schema" if invalid_schema else observation["reason"]


def _читати_рядки(шлях):
    """Прочитати JSONL без відкидання невалідних рядків."""
    return [_json(рядок) for рядок in шлях.read_text().splitlines() if рядок.strip()]


def main():
    """Записати машинний звіт; лише реальне фото-приймання повертає exit0."""
    парсер = argparse.ArgumentParser(description=__doc__)
    for ім in ("manifest", "gold", "receipt", "results", "captures", "output"):
        парсер.add_argument("--" + ім, type=Path, required=True)
    парсер.add_argument("--input-per-million", type=float)
    парсер.add_argument("--output-per-million", type=float)
    args = парсер.parse_args()
    try:
        файли = {"prepared_manifest_sha256": sha256(args.manifest.read_bytes()),
                 "gold_sha256": sha256(args.gold.read_bytes()), "results_sha256": sha256(args.results.read_bytes()),
                 "capture_manifest_file_sha256": sha256(args.captures.read_bytes()),
                 "receipt_file_sha256": sha256(args.receipt.read_bytes())}
        ціни = [args.input_per_million, args.output_per_million] if args.input_per_million is not None and args.output_per_million is not None else None
        звіт = оцінити(_читати_рядки(args.manifest), _json(args.gold.read_text()),
                       _читати_рядки(args.results), _json(args.receipt.read_text()),
                       кадри=_json(args.captures.read_text()), файли=файли, база=args.manifest.resolve().parent, ціни=ціни)
    except (ValueError, TypeError, KeyError, OSError, ImportError) as помилка:
        звіт = dict(protocol=ПРОТОКОЛ, status="INCOMPLETE", photo_acceptance=False,
                    error=dict(kind=type(помилка).__name__, detail=str(помилка)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(звіт, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({к: звіт[к] for к in ("status", "photo_acceptance")}, ensure_ascii=False))
    return 0 if звіт["status"] == "PASS" else 2 if звіт["status"] in ("INCOMPLETE", "SYNTHETIC_ONLY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
