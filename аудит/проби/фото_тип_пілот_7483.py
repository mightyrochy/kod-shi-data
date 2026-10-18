"""Пілот 7483: prepare → download → blind gold → infer (40, потім ті самі 120).

Працює лише з окремим маніфестом пілота, не пише каталог чи продукт.
Для download/infer потрібен Pillow; inference — лише вже завантажена модель
LM Studio на localhost. Не керує моделями й не читає незалежних gold-міток.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ПРОТОКОЛ = "photo-type-pilot-7483-v1"
МАКС_КАДРІВ = 120
МАКС_БАЙТІВ = 20 * 1024 * 1024
КЛАСИ = {"classified", "unknown", "ambiguous", "invalid"}


def канон(значення):
    """Однозначний JSON для хешів контракту й ключа повторного використання."""
    return json.dumps(значення, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def хеш(байти):
    """SHA256 точних байтів, а не URL чи давнього запису каталогу."""
    return hashlib.sha256(байти).hexdigest()


def зараз():
    """UTC момент фактичної операції."""
    return datetime.now(timezone.utc).isoformat()


def записати(шлях, значення):
    """Атомарний JSON: перерваний запис не стає придатним кешем."""
    шлях = Path(шлях)
    шлях.parent.mkdir(parents=True, exist_ok=True)
    тимчасовий = шлях.with_suffix(шлях.suffix + ".tmp")
    тимчасовий.write_bytes(канон(значення) + b"\n")
    тимчасовий.replace(шлях)


def jsonl(шлях, рядки):
    """Детермінований маніфест із фактичних рядків."""
    шлях = Path(шлях)
    шлях.parent.mkdir(parents=True, exist_ok=True)
    шлях.write_bytes(b"".join(канон(р) + b"\n" for р in рядки))


def прочитати(шлях):
    """Не більше 120 різних sample_id; метадані залишаються поза запитом VLM."""
    рядки = [json.loads(л) for л in Path(шлях).read_text(encoding="utf-8").splitlines() if л.strip()]
    if not 1 <= len(рядки) <= МАКС_КАДРІВ:
        raise ValueError("manifest_count_outside_1_120")
    імена = set()
    for р in рядки:
        ім = р.get("sample_id") or р.get("id")
        if not isinstance(ім, str) or not ім or ім in імена or ("id" in р and р["id"] != ім):
            raise ValueError("missing_or_duplicate_sample_id")
        імена.add(ім)
        р["protocol"] = ПРОТОКОЛ
        р["crop"] = None
        р.setdefault("source_kind", "product" if р.get("role") == "real" else "service_control")
        р.setdefault("source_id", ім)
        р["sample_id"] = ім
        р["blind_id"] = хеш(ім.encode("utf-8"))[:16]
        if р.get("role") not in ("real", "negative") or type(р.get("calibration")) is not bool:
            raise ValueError("manifest_role_or_calibration_missing")
        if р.get("target_binding", {"kind": "full_frame", "crop": None}) != {"kind": "full_frame", "crop": None}:
            raise ValueError("only_exact_full_frame_supported")
    return рядки


def підготувати(маніфест, вихід, expected_selection_sha256=None):
    """Фіксує до 120 вибраних записів; pending negative не стає вигаданим кадром."""
    if expected_selection_sha256 is not None and хеш(Path(маніфест).read_bytes()) != expected_selection_sha256:
        raise ValueError("selection_manifest_hash_mismatch")
    сирі = [json.loads(л) for л in Path(маніфест).read_text(encoding="utf-8").splitlines() if л.strip()]
    dataset_sha = хеш(канон(сирі))
    рядки = прочитати(маніфест)
    for р in рядки:
        р["dataset_sha256"] = dataset_sha
        р["selection_manifest_sha256"] = хеш(Path(маніфест).read_bytes())
        р["prepare_status"] = "selected" if р.get("image_url") and р.get("ready_for_download", True) else "pending_input"
    jsonl(вихід, рядки)
    return {"rows": len(рядки), "pending": sum(р["prepare_status"] == "pending_input" for р in рядки)}


class БезПереспрямувань(urllib.request.HTTPRedirectHandler):
    """Запит з image data не можна переспрямувати з localhost на інший сервер."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http(адреса, дані=None, таймаут=60, межа=МАКС_БАЙТІВ, переспрямування=True):
    """Прямий HTTP без env-проксі; для LM Studio переспрямування заборонені."""
    розбір = urllib.parse.urlsplit(адреса)
    if розбір.scheme not in ("http", "https") or розбір.username or розбір.password:
        raise ValueError("invalid_http_url")
    обробники = [urllib.request.ProxyHandler({})]
    if not переспрямування:
        обробники.append(БезПереспрямувань())
    запит = urllib.request.Request(адреса, data=дані, headers={"Content-Type": "application/json"} if дані is not None else {})
    with urllib.request.build_opener(*обробники).open(запит, timeout=таймаут) as відповідь:
        байти = відповідь.read(межа + 1)
        if len(байти) > межа:
            raise ValueError("http_body_too_large")
        return байти, відповідь.geturl()


def кадр(байти):
    """Декодує справжні пікселі PNG/JPEG/WebP, зберігаючи початкові байти для VLM."""
    from PIL import Image
    with Image.open(io.BytesIO(байти)) as зображення:
        if зображення.format not in ("PNG", "JPEG", "WEBP"):
            raise ValueError("unsupported_image_format")
        ш, в = зображення.size
        if not 1 <= ш <= 8192 or not 1 <= в <= 8192 or getattr(зображення, "is_animated", False):
            raise ValueError("invalid_image_dimensions_or_animation")
        зображення.load()
        mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[зображення.format]
    return ш, в, mime


def завантажити(маніфест, тека, dataset_revision, таймаут=60):
    """Завантажує лише exact URL маніфесту; видає кадри та аркуш без старих міток."""
    if len(dataset_revision) != 40 or any(с not in "0123456789abcdef" for с in dataset_revision):
        raise ValueError("explicit_frozen_dataset_revision_required")
    тека = Path(тека).resolve()
    тека.mkdir(parents=True, exist_ok=True)
    рядки = прочитати(маніфест)
    dataset_hashes = {р.get("dataset_sha256") for р in рядки}
    selection_hashes = {р.get("selection_manifest_sha256") for р in рядки}
    if len(dataset_hashes) != 1 or None in dataset_hashes or len(selection_hashes) != 1 or None in selection_hashes:
        raise ValueError("run_prepare_first")
    попередні = {}
    підготовлені = тека / "prepared.jsonl"
    if підготовлені.exists():
        попередні = {р["sample_id"]: р for р in прочитати(підготовлені)}
    кеш_url = {}
    for р in рядки:
        if not р.get("image_url") or not р.get("ready_for_download", True):
            р["prepare_status"] = "pending_input"
            continue
        початок = time.monotonic()
        try:
            старий = попередні.get(р["sample_id"], {})
            if старий.get("prepare_status") == "ready" and старий.get("image_url") == р["image_url"]:
                файл = (тека / старий["prepared_path"]).resolve()
                if тека not in файл.parents:
                    raise ValueError("cached_path_escapes_evidence")
                байти = файл.read_bytes()
                if хеш(байти) != старий["image_sha256"]:
                    raise ValueError("cached_image_hash_mismatch")
                кінцева = старий["resolved_image_url"]
            elif р["image_url"] in кеш_url:
                байти, кінцева = кеш_url[р["image_url"]]
            else:
                байти, кінцева = http(р["image_url"], таймаут=таймаут)
                кеш_url[р["image_url"]] = байти, кінцева
            ш, в, mime = кадр(байти)
            sha = хеш(байти)
            відносний = "images/" + sha + {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime]
            файл = тека / відносний
            файл.parent.mkdir(exist_ok=True)
            файл.write_bytes(байти)
            р.update(prepare_status="ready", image_sha256=sha, prepared_path=відносний,
                     width=ш, height=в, mime=mime, resolved_image_url=кінцева, prepared_utc=старий.get("prepared_utc") or зараз(),
                     download_latency_ms=старий.get("download_latency_ms", round((time.monotonic() - початок) * 1000, 3)), prepare_error=None)
        except Exception as помилка:
            р.update(prepare_status="error", prepare_error={"type": type(помилка).__name__, "message": str(помилка)})
    jsonl(підготовлені, рядки)
    captures = {р["sample_id"]: {**{к: р.get(к) for к in
        ("sku", "source_kind", "source_id", "image_sha256", "image_url", "source_url", "source_sha", "item_page_url", "source_file", "source_file_sha256", "source_record_pointer", "selection_provenance", "prepared_path", "width", "height", "mime", "blind_id")},
        "bytes_sha256": р["image_sha256"], "crop": None} for р in рядки if р.get("prepare_status") == "ready"}
    capture_manifest = {"version": "visible_item_capture.v1", "dataset_revision": dataset_revision,
        "dataset_sha256": next(iter(dataset_hashes)), "selection_manifest_sha256": next(iter(selection_hashes)), "records": captures}
    записати(тека / "capture-manifest.json", capture_manifest)
    огляд = експортувати_очам(підготовлені, тека)
    return {"rows": len(рядки), "ready": огляд["ready"], "prepared_manifest_sha256": хеш(підготовлені.read_bytes())}


def експортувати_очам(маніфест, тека):
    """Окремий blind-review export: лише actual pixels, blind_id та хеш, без підказок."""
    джерело = Path(маніфест).resolve().parent
    тека = Path(тека).resolve()
    тека.mkdir(parents=True, exist_ok=True)
    огляд = []
    рядки = прочитати(маніфест)
    for р in рядки:
        if р.get("prepare_status") != "ready":
            continue
        файл = (джерело / р["prepared_path"]).resolve()
        if джерело not in файл.parents:
            raise ValueError("review_path_escapes_evidence")
        байти = файл.read_bytes()
        if хеш(байти) != р["image_sha256"] or кадр(байти) != (р["width"], р["height"], р["mime"]):
            raise ValueError("review_image_changed")
        relative = "images/" + файл.name
        destination = тека / relative
        destination.parent.mkdir(exist_ok=True)
        if destination != файл:
            destination.write_bytes(байти)
        огляд.append({**{к: р[к] for к in ("blind_id", "image_sha256", "width", "height", "mime")}, "prepared_path": relative})
    jsonl(тека / "review-manifest.jsonl", огляд)
    плитки = [f'<figure><img src="{html.escape(р["prepared_path"], quote=True)}"><figcaption>{р["blind_id"]}</figcaption></figure>' for р in огляд]
    (тека / "review.html").write_text('<meta charset="utf-8"><title>7483 — кадри для незалежної розмітки</title><style>body{display:flex;flex-wrap:wrap}figure{width:280px}img{width:100%;height:320px;object-fit:contain}</style>' + "\n".join(плитки), encoding="utf-8")
    return {"rows": len(рядки), "ready": len(огляд), "review_manifest_sha256": хеш((тека / "review-manifest.jsonl").read_bytes())}


def контракт(шлях):
    """Завантажує API власника схеми та перевіряє точні хеші його bundle."""
    шлях = Path(шлях).resolve()
    sys.path.insert(0, str(шлях.parent))
    опис = importlib.util.spec_from_file_location("контракт_пілота_7483", шлях)
    модуль = importlib.util.module_from_spec(опис)
    sys.modules[опис.name] = модуль
    опис.loader.exec_module(модуль)
    пакет = модуль.пакет_контракту()
    очікувані = {"schema_sha256": хеш(канон(пакет["schema"])), "prompt_sha256": хеш(пакет["prompt"].encode("utf-8")), "taxonomy_sha256": хеш(канон(пакет["taxonomy"]))}
    if пакет["hashes"] != очікувані:
        raise ValueError("contract_bundle_hash_mismatch")
    return модуль, пакет


def локальна_адреса(адреса):
    """Модельний endpoint — лише явний localhost, без credentials/query/fragment."""
    р = urllib.parse.urlsplit(адреса)
    if р.scheme != "http" or р.hostname not in ("localhost", "127.0.0.1", "::1") or р.username or р.password or р.query or р.fragment or р.path.rstrip("/") not in ("", "/v1"):
        raise ValueError("lm_studio_localhost_only")
    return адреса.rstrip("/") + ("/chat/completions" if р.path.rstrip("/") == "/v1" else "/v1/chat/completions")


def прийняти_підготовку(маніфест, receipt):
    """120 готових кадрів та квитанція freeze незалежного gold до першого inference."""
    рядки = прочитати(маніфест)
    if len(рядки) != 120 or sum(р["role"] == "real" for р in рядки) != 100 or sum(р["calibration"] for р in рядки) != 40:
        raise ValueError("pilot_requires_100_real_20_negative_40_calibration")
    квитанція = json.loads(Path(receipt).read_text(encoding="utf-8"))
    if квитанція.get("blind") is not True or not квитанція.get("reviewer") or квитанція.get("prepared_manifest_sha256") != хеш(Path(маніфест).read_bytes()):
        raise ValueError("blind_gold_receipt_missing_or_mismatched")
    gold_sha = квитанція.get("gold_sha256", "")
    if len(gold_sha) != 64 or any(с not in "0123456789abcdef" for с in gold_sha):
        raise ValueError("gold_sha256_required")
    capture_file = Path(маніфест).resolve().parent / "capture-manifest.json"
    capture = json.loads(capture_file.read_text(encoding="utf-8"))
    capture_sha = хеш(канон(capture))
    if (квитанція.get("version") != "visible_item_capture_receipt.v1"
            or квитанція.get("protocol") != ПРОТОКОЛ or not квитанція.get("evidence_commit")
            or set(квитанція.get("verified_capture_ids", [])) != {р["sample_id"] for р in рядки}
            or квитанція.get("capture_manifest_sha256") != capture_sha
            or квитанція.get("verification") != "actual_bytes_sha256"
            or any(квитанція.get(к) != capture.get(к) for к in ("dataset_revision", "dataset_sha256"))):
        raise ValueError("capture_qa_receipt_mismatch")
    пари = [(р.get("sample_id"), р.get("image_sha256")) for р in квитанція.get("rows", [])]
    if len(пари) != 120 or len(set(пари)) != 120 or set(пари) != {(р["sample_id"], р.get("image_sha256")) for р in рядки}:
        raise ValueError("receipt_frame_bindings_mismatch")
    for р in рядки:
        if р.get("prepare_status") != "ready" or not р.get("image_url"):
            raise ValueError("pilot_frame_not_ready")
        if not ((р["role"] == "real" and р.get("source_kind") == "product" and isinstance(р.get("sku"), str) and р["sku"].strip())
                or (р["role"] == "negative" and р.get("source_kind") == "service_control" and р.get("sku") is None and р.get("source_id"))):
            raise ValueError("product_sku_or_service_control_binding_required")
        bound = capture.get("records", {}).get(р["sample_id"], {})
        if any(bound.get(к) != р.get(к) for к in ("sku", "image_sha256", "image_url", "crop", "source_kind", "source_id")):
            raise ValueError("capture_frame_binding_mismatch")
        файл = (Path(маніфест).resolve().parent / р["prepared_path"]).resolve()
        if Path(маніфест).resolve().parent not in файл.parents:
            raise ValueError("prepared_path_escapes_evidence")
        байти = файл.read_bytes()
        if len(байти) > МАКС_БАЙТІВ or хеш(байти) != р["image_sha256"] or кадр(байти) != (р["width"], р["height"], р["mime"]):
            raise ValueError("prepared_image_changed")
    return рядки, квитанція


def виконати(маніфест, receipt, шлях_контракту, model_id, model_revision, адреса, тека,
             phase="all", parallel=1, max_tokens=512, timeout=180):
    """Один запит на кожний унікальний кадр/модель/контракт; gold-мітки не читаються."""
    if phase not in ("all", "calibration") or not model_id.strip() or model_id != model_id.strip() or not model_revision.strip() or model_revision != model_revision.strip() or not 1 <= parallel <= 3 or not 1 <= max_tokens <= 2048:
        raise ValueError("explicit_model_revision_and_bounded_params_required")
    endpoint = локальна_адреса(адреса)
    рядки, квитанція = прийняти_підготовку(маніфест, receipt)
    модуль, пакет = контракт(шлях_контракту)
    capture = json.loads((Path(маніфест).resolve().parent / "capture-manifest.json").read_text(encoding="utf-8"))
    if модуль.перевірити_кадри(capture, квитанція)["status"] != "verified":
        raise ValueError("contract_capture_receipt_not_verified")
    тека = Path(тека).resolve()
    кеш = тека / "cache"
    кеш.mkdir(parents=True, exist_ok=True)
    run_id = хеш(канон({"manifest": хеш(Path(маніфест).read_bytes()), "model": model_id, "revision": model_revision, "hashes": пакет["hashes"], "max_tokens": max_tokens}))
    параметри = {"temperature": 0, "max_tokens": max_tokens}
    обрані = sorted((р for р in рядки if phase == "all" or р["calibration"]), key=lambda р: (not р["calibration"], р["sample_id"]))
    групи, identities = {}, {}
    for р in обрані:
        identity = {"image_sha256": р["image_sha256"], "model_id": model_id, "model_revision": model_revision, **пакет["hashes"], "parameters": параметри}
        ключ = хеш(канон(identity))
        identities[ключ] = identity
        групи.setdefault(ключ, []).append(р)
    початок = time.monotonic()
    початок_utc = зараз()
    invocation_id = uuid.uuid4().hex

    def запит(пара):
        ключ, свої = пара
        файл = кеш / (ключ + ".json")
        try:
            with файл.open("x", encoding="utf-8") as запис:
                json.dump({"status": "in_progress", "attempt_id": ключ, "cache_identity": identities[ключ], "primary_invocation_id": invocation_id, "wall_started_utc": зараз()}, запис)
        except FileExistsError:
            з = json.loads(файл.read_text(encoding="utf-8"))
            if з.get("attempt_id") != ключ or з.get("cache_identity") != identities[ключ]:
                raise ValueError("cache_identity_mismatch")
            if з.get("status") == "in_progress":
                з = dict(з, status="error", error={"code": "interrupted_attempt_no_automatic_retry"}, usage=None, latency_ms=None, raw_response=None, model_text=None, wall_finished_utc=None)
            return ключ, з, True, False
        р = свої[0]
        з = {"attempt_id": ключ, "cache_identity": identities[ключ], "primary_invocation_id": invocation_id, "wall_started_utc": зараз(), "usage": None, "raw_response": None, "model_text": None, "error": None}
        старт = time.monotonic()
        request_attempted = False
        try:
            байти = (Path(маніфест).resolve().parent / р["prepared_path"]).read_bytes()
            if хеш(байти) != р["image_sha256"]:
                raise ValueError("image_changed_before_request")
            # Єдиний whitelist входу моделі: сталий промпт і перевірені actual bytes.
            payload = {"model": model_id, **параметри, "messages": [{"role": "user", "content": [
                {"type": "text", "text": пакет["prompt"]},
                {"type": "image_url", "image_url": {"url": "data:" + р["mime"] + ";base64," + base64.b64encode(байти).decode("ascii")}}]}],
                "response_format": {"type": "json_schema", "json_schema": {"name": "photo_type_pilot_7483", "strict": True, "schema": пакет["schema"]}}}
            request_attempted = True
            raw, _ = http(endpoint, канон(payload), таймаут=timeout, переспрямування=False)
            з["raw_response_bytes_sha256"] = хеш(raw)
            з["raw_response_text"] = raw.decode("utf-8")
            з["raw_response"] = json.loads(raw)
            з["usage"] = з["raw_response"].get("usage")
            вибір = з["raw_response"]["choices"][0]
            з["model_text"] = вибір["message"]["content"]
            if з["raw_response"].get("model") != model_id:
                raise ValueError("response_model_id_mismatch")
            if вибір.get("finish_reason") != "stop":
                raise ValueError("incomplete_response")
            if not isinstance(з["model_text"], str) or not з["model_text"].strip():
                raise ValueError("empty_or_nontext_response")
            факт = модуль.перевірити_відповідь(з["model_text"])
            if факт["status"] not in КЛАСИ:
                raise ValueError("unrecognized_contract_status")
            з["status"] = факт["status"]
        except Exception as помилка:
            if isinstance(помилка, urllib.error.HTTPError):
                raw_error = помилка.read(МАКС_БАЙТІВ + 1)
                з.update(http_status=помилка.code, error_response_bytes_sha256=хеш(raw_error), error_response_text=raw_error.decode("utf-8", "replace"))
            з.update(status="error", error={"code": str(помилка), "type": type(помилка).__name__})
        з["primary_request_attempted"] = request_attempted
        з.update(latency_ms=round((time.monotonic() - старт) * 1000, 3), wall_finished_utc=зараз())
        записати(файл, з)
        return ключ, з, False, request_attempted

    with ThreadPoolExecutor(max_workers=parallel) as потоки:
        відповіді = list(потоки.map(запит, групи.items()))
    результати = []
    for ключ, з, reused, був_запит in відповіді:
        for і, р in enumerate(групи[ключ]):
            сп, observation, validation_errors = None, None, []
            status = з["status"]
            if з.get("model_text") is not None and status != "error":
                перевірка = модуль.перевірити_відповідь(з["model_text"])
                status, observation, validation_errors = перевірка["status"], перевірка.get("observation"), перевірка.get("errors", [])
                if р.get("sku"):
                    сп = модуль.спостереження(з["model_text"], sku=р["sku"], image_sha256=р["image_sha256"],
                        image_url=р["image_url"], crop=None, model_id=model_id, model_revision=model_revision,
                        capture_id=р["sample_id"], capture_manifest_sha256=квитанція["capture_manifest_sha256"])
            результати.append({"protocol": ПРОТОКОЛ, **{к: р.get(к) for к in ("sample_id", "blind_id", "sku", "image_url", "image_sha256", "frame_target", "role", "stratum", "calibration", "source_kind", "source_id")},
                "crop": None, "run_id": run_id, "invocation_id": invocation_id, "model": {"id": model_id, "revision": model_revision}, "hashes": пакет["hashes"],
                "contract_version": пакет["version"], "provenance_kind": "vision_image_only", "cache_key": ключ,
                "contract_record": сп, **з, "observation": observation, "validation_errors": validation_errors, "status": status,
                "capture": {"manifest_sha256": квитанція["capture_manifest_sha256"], "id": р["sample_id"]},
                "reused": reused or і > 0, "request_performed": був_запит and і == 0,
                "actual_request_count": int(був_запит and і == 0), "gold_receipt_sha256": хеш(Path(receipt).read_bytes())})
    результати.sort(key=lambda р: (not р["calibration"], р["sample_id"]))
    history = тека / "runs" / invocation_id
    history.mkdir(parents=True, exist_ok=False)
    jsonl(history / "results.jsonl", результати)
    jsonl(тека / ("results-" + phase + ".jsonl"), результати)
    звіт = {"protocol": ПРОТОКОЛ, "run_id": run_id, "invocation_id": invocation_id, "results_path": str(history / "results.jsonl"),
        "runner_sha256": хеш(Path(__file__).read_bytes()), "contract_source_sha256": хеш(Path(шлях_контракту).read_bytes()), "phase": phase, "rows": len(результати), "unique_keys": len(групи),
        "actual_requests": sum(р["actual_request_count"] for р in результати), "model": {"id": model_id, "revision": model_revision},
        "hashes": пакет["hashes"], "prepared_manifest_sha256": квитанція["prepared_manifest_sha256"], "gold_sha256": квитанція["gold_sha256"],
        "wall_started_utc": початок_utc, "wall_finished_utc": зараз(), "wall_seconds": round(time.monotonic() - початок, 6),
        "parameters": параметри, "parallel": parallel, "status_counts": {ст: sum(р["status"] == ст for р in результати) for ст in sorted(КЛАСИ | {"error"})}}
    записати(history / "run.json", звіт)
    записати(тека / ("run-" + phase + ".json"), звіт)
    return звіт


def main():
    """CLI не має режиму повного корпусу, повторів або керування моделями."""
    parser = argparse.ArgumentParser(description=__doc__)
    команди = parser.add_subparsers(dest="command", required=True)
    for ім in ("prepare", "download", "review-export", "infer"):
        p = команди.add_parser(ім)
        p.add_argument("--manifest", required=True)
        p.add_argument("--output", required=True, help="prepare: JSONL файл; download/infer: окрема тека")
        if ім == "prepare":
            p.add_argument("--expected-selection-sha256")
        if ім == "download":
            p.add_argument("--dataset-revision", required=True, help="Git SHA40 замороженого селектора/набору")
        if ім in ("download", "infer"):
            p.add_argument("--timeout", type=float, default=180 if ім == "infer" else 60)
        if ім == "infer":
            p.add_argument("--receipt", required=True)
            p.add_argument("--contract", default=str(Path(__file__).resolve().parents[2] / "джерела/фото_тип_контракт.py"))
            p.add_argument("--model-id", required=True)
            p.add_argument("--model-revision", required=True)
            p.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
            p.add_argument("--phase", choices=("calibration", "all"), default="all")
            p.add_argument("--parallel", type=int, choices=(1, 2, 3), default=1)
            p.add_argument("--max-tokens", type=int, default=512)
    a = parser.parse_args()
    if a.command == "prepare":
        звіт = підготувати(a.manifest, a.output, a.expected_selection_sha256)
    elif a.command == "review-export":
        звіт = експортувати_очам(a.manifest, a.output)
    elif a.command == "download":
        звіт = завантажити(a.manifest, a.output, a.dataset_revision, a.timeout)
    else:
        звіт = виконати(a.manifest, a.receipt, a.contract, a.model_id, a.model_revision, a.base_url,
            a.output, a.phase, a.parallel, a.max_tokens, a.timeout)
    print(json.dumps(звіт, ensure_ascii=False, sort_keys=True))
    if a.command in ("download", "review-export"):
        return int(звіт["ready"] != звіт["rows"])
    if a.command == "infer":
        return int(bool(звіт["status_counts"]["error"] or звіт["status_counts"]["invalid"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
