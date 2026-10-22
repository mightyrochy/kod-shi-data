"""Закритий фото-тип з кадру: коди, явне незнання й перевірне походження.

К-3, пілот7483: schema-valid не означає photo-correct. Каталог і free_text
не є свідками фото. Тип не змінює статусів кольору/складу/металу договору2.10.
"""
import hashlib as _hashlib
import json as _json
import re as _re
from urllib.parse import urlsplit as _urlsplit

import слоти as _С

ВЕРСІЯ = "visible_item_type.v1"
ФАЙЛ = "каталог_фото_тип.json"
ВЕРСІЯ_ФАЙЛА = "visible_item_type_catalog.v1"
КАДРИ_ФАЙЛ = "каталог_фото_тип_кадри.json"
ПРИЙМАННЯ_ФАЙЛ = "каталог_фото_тип_приймання.json"
ФАЙЛИ = (ФАЙЛ, КАДРИ_ФАЙЛ, ПРИЙМАННЯ_ФАЙЛ)
_ЦІЛІ = ("unique", "ambiguous", "not_visible")
_ПРИЧИНИ = (None, "multiple_objects", "target_unclear", "occluded", "too_small", "taxonomy_gap", "not_visible")
_КЛЮЧІ = frozenset(("target", "item_type", "bbox", "reason"))
_ЗАПИС = frozenset(("version", "sku", "image", "producer", "raw_response", "raw_response_sha256", "visible_item_type", "status", "errors", "capture"))


# Межа файлів поза ядром: audit runner є писачем, evaluator — читачем.
# Receipt видає root/QA після bytes-перевірки; жоден код тут не генерує приймання.
ЗОВНІШНІ_ВХОДИ = {
    "bytes_sha256": "аудит/проби/фото_тип_пілот_7483.py:завантажити → capture-manifest.json records: SHA завантажених bytes",
    "contract_record": "аудит/проби/фото_тип_пілот_7483.py:виконати → results.jsonl: спостереження для product, null для control",
    "dataset_revision": "runner:завантажити (--dataset-revision Git40) → capture-manifest.json; root/QA повторює у receipt",
    "dataset_sha256": "runner:підготувати → SHA canonical selection rows; завантажити → capture-manifest.json; root/QA звіряє receipt",
    "source_kind": "runner:прочитати → product/service_control з selection manifest; завантажити → capture-manifest.json records",
    "reviewer": "root/QA → окремий visible_item_capture_receipt.v1, ідентифікатор перевірки actual bytes; evaluator лише читає",
    "evidence_commit": "root/QA → visible_item_capture_receipt.v1, Git40 коміту перевірених bytes-доказів; перевірити_кадри вимагає",
    "verification": "root/QA → visible_item_capture_receipt.v1, literal actual_bytes_sha256 після перевірки bytes; не самопідпис runner",
    "verified_capture_ids": "root/QA → visible_item_capture_receipt.v1, явний список перевірених capture IDs; evaluator лише читає",
    "source_image_sha256": "зовнішній caller спостереження(crop=...) → валідований independent_visual_target crop API, SHA оригіналу; пілот runner пише crop:null",
}


def канонічні_байти(дані):
    """Одна UTF-8 форма JSON для runner, evaluator, схеми й таксономії."""
    return _json.dumps(дані, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(дані):
    """SHA256 саме байтів, не адреси чи перекладеного опису."""
    return _hashlib.sha256(дані).hexdigest()


def таксономія():
    """Знімок канонічної таблиці2.6 без другого словника типів чи слотів."""
    return dict(types=sorted(_С.СЛОТ_ТИПУ), slots=sorted(_С.КЛЮЧІ), mapping=dict(_С.СЛОТ_ТИПУ))


def схема_відповіді():
    """Закрита схема лише чотирьох полів видимого предмета."""
    типи = таксономія()["types"]
    bbox = dict(type="array", items=dict(type="integer", minimum=0, maximum=1000), minItems=4, maxItems=4)
    варіанти = []
    for ціль, тип, рамка, причина in (
            ("unique", dict(enum=типи), bbox, dict(type="null")),
            ("unique", dict(enum=["unknown"]), bbox, dict(enum=["occluded", "too_small", "taxonomy_gap"])),
            ("ambiguous", dict(enum=["unknown"]), dict(type="null"), dict(enum=["multiple_objects", "target_unclear"])),
            ("not_visible", dict(enum=["unknown"]), dict(type="null"), dict(enum=["not_visible"]))):
        варіанти.append(dict(type="object", additionalProperties=False, required=sorted(_КЛЮЧІ), properties={
            "target": dict(enum=[ціль]), "item_type": тип, "bbox": рамка, "reason": причина}))
    return dict(title=ВЕРСІЯ, oneOf=варіанти)


def промпт():
    """Промпт image-only на штатному збирачі; жодного поля каталогу."""
    import збирач_промптів as ЗП
    о = ЗП.Оголошення(
        задача=ВЕРСІЯ, роль="Classify the visible target item from the supplied image alone.",
        вхід=(ЗП.Поле("item_types", "the allowed existing item_type codes; unknown is allowed too"),),
        правила=(
            "Use only the image. Do not use a product title, description, catalogue type or slot.",
            "One unambiguous item: target=unique. If its type cannot be seen, item_type=unknown.",
            "Several clothing/accessory objects without an independently supplied visual target: target=ambiguous, "
            "item_type=unknown, bbox=null, reason=multiple_objects. Never choose the largest or central object as the SKU.",
            "No visible target: target=not_visible, item_type=unknown, bbox=null, reason=not_visible.",
            "A known type needs unique target, reason=null and bbox [x0,y0,x1,y1], integers 0..1000 relative to this image; "
            "x0<x1 and y0<y1. A unique unknown type needs bbox and reason occluded, too_small or taxonomy_gap.",
            "Ambiguous reason is multiple_objects or target_unclear. Do not guess an occasion, material, metal, "
            "colour or whether separate garments are sold as one set. Use unknown if the taxonomy needs unseen facts.",
            "Return exactly target, item_type, bbox, reason under the supplied response schema."),
        вихід=ВЕРСІЯ, скелет=dict(target="unique|ambiguous|not_visible", item_type="existing code|unknown", bbox=[0, 0, 1000, 1000], reason=None),
        мова_промпту="en", межі=("лише_вхід", "невідомо"))
    # Порядок шаблону (task спершу) зберігається; хеш — точного повернутого рядка.
    return _json.dumps(ЗП.зібрати(о, dict(item_types=таксономія()["types"])), ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def пакет_контракту():
    """Стабільний bundle API для офлайнових runner/evaluator без моделі й фото."""
    схема, текст, типи = схема_відповіді(), промпт(), таксономія()
    return dict(version=ВЕРСІЯ, schema=схема, prompt=текст, taxonomy=типи, hashes=dict(
        schema_sha256=_sha(канонічні_байти(схема)), prompt_sha256=_sha(текст.encode("utf-8")),
        taxonomy_sha256=_sha(канонічні_байти(типи))))


def _bbox(рамка):
    """Перевірити модельний вказівник, не виводячи фізичних мірок речі."""
    return (isinstance(рамка, list) and len(рамка) == 4 and all(type(v) is int and 0 <= v <= 1000 for v in рамка)
            and рамка[0] < рамка[2] and рамка[1] < рамка[3])


def _без_дублів(пари):
    """Не дозволити повторному JSON-ключу тихо перезаписати попереднє рішення."""
    вих = {}
    for к, в in пари:
        if к in вих:
            raise ValueError("duplicate_key")
        вих[к] = в
    return вих


def _не_json(значення):
    """Відкинути NaN/Infinity, яких JSON-договір не допускає."""
    raise ValueError("non_json_number")


def перевірити_відповідь(raw):
    """Текст моделі → classified/unknown/ambiguous/invalid без словесного fallback."""
    try:
        р = _json.loads(raw, object_pairs_hook=_без_дублів, parse_constant=_не_json) if isinstance(raw, str) else None
    except (ValueError, TypeError):
        return dict(status="invalid", observation=None, errors=["invalid_json"])
    if not isinstance(р, dict) or set(р) != _КЛЮЧІ:
        return dict(status="invalid", observation=None, errors=["invalid_fields"])
    ціль, тип, рамка, причина = (р[к] for к in ("target", "item_type", "bbox", "reason"))
    помилки = []
    if not isinstance(ціль, str) or ціль not in _ЦІЛІ:
        помилки.append("invalid_target")
    if not isinstance(тип, str) or тип not in (*_С.СЛОТ_ТИПУ, "unknown"):
        помилки.append("invalid_item_type")
    if причина not in _ПРИЧИНИ:
        помилки.append("invalid_reason")
    if ціль == "unique":
        if not _bbox(рамка):
            помилки.append("invalid_bbox")
        if (тип == "unknown" and причина not in ("occluded", "too_small", "taxonomy_gap")) or (тип != "unknown" and причина is not None):
            помилки.append("incompatible_fields")
    elif ціль in ("ambiguous", "not_visible"):
        причини = ("multiple_objects", "target_unclear") if ціль == "ambiguous" else ("not_visible",)
        if тип != "unknown" or рамка is not None or причина not in причини:
            помилки.append("incompatible_fields")
    if помилки:
        return dict(status="invalid", observation=None, errors=помилки)
    стан = "classified" if ціль == "unique" and тип != "unknown" else "ambiguous" if ціль == "ambiguous" else "unknown"
    return dict(status=стан, observation=р, errors=[])


def _хеш(хеш):
    """Синтаксис SHA256, а не припущення про фактичний кадр."""
    return isinstance(хеш, str) and _re.fullmatch(r"[0-9a-f]{64}", хеш) is not None


def _crop(crop):
    """Лише незалежно задана візуальна ціль із походженням оригінального кадру."""
    return crop is None or (isinstance(crop, dict) and set(crop) == {"bbox", "source", "source_image_sha256"}
        and _bbox(crop["bbox"]) and crop["source"] == "independent_visual_target" and _хеш(crop["source_image_sha256"]))


def _метадані(sku, image_sha256, image_url, crop, model_id, model_revision):
    """Перевірити зовнішню обгортку, яку модель не має права самопроголошувати."""
    рядки = (sku, image_url, model_id, model_revision)
    if not all(isinstance(v, str) and v.strip() and v == v.strip() for v in рядки):
        return False
    try:
        url = _urlsplit(image_url)
    except ValueError:
        return False
    return _хеш(image_sha256) and url.scheme in ("http", "https") and bool(url.netloc) and _crop(crop)


def спостереження(raw, *, sku, image_sha256, image_url, crop, model_id, model_revision,
                  capture_id=None, capture_manifest_sha256=None):
    """Обгорнути відповідь фактичними метаданими runner; не копіювати тип каталогу."""
    if not _метадані(sku, image_sha256, image_url, crop, model_id, model_revision):
        raise ValueError("invalid_provenance")
    if not isinstance(raw, str):
        raise ValueError("raw_must_be_text")
    if (capture_id is None) != (capture_manifest_sha256 is None) or (capture_id is not None and
            (not isinstance(capture_id, str) or not capture_id.strip() or not _хеш(capture_manifest_sha256))):
        raise ValueError("invalid_capture")
    р = перевірити_відповідь(raw)
    return dict(capture=None if capture_id is None else dict(id=capture_id, manifest_sha256=capture_manifest_sha256), version=ВЕРСІЯ, sku=sku, image=dict(sha256=image_sha256, url=image_url, crop=crop),
        producer=dict(kind="vision_image_only", model_id=model_id, model_revision=model_revision,
                      **пакет_контракту()["hashes"]), raw_response=raw,
        raw_response_sha256=_sha(raw.encode("utf-8")), visible_item_type=р["observation"], status=р["status"], errors=р["errors"])


def перевірити_запис(запис):
    """Повторно довести схему, походження й raw→observation до читача."""
    invalid = lambda код: dict(status="invalid", observation=None, errors=[код])
    if not isinstance(запис, dict) or set(запис) != _ЗАПИС or запис["version"] != ВЕРСІЯ:
        return invalid("invalid_record")
    capture = запис["capture"]
    if capture is not None and (not isinstance(capture, dict) or set(capture) != {"id", "manifest_sha256"}
            or not isinstance(capture["id"], str) or not capture["id"].strip() or not _хеш(capture["manifest_sha256"])):
        return invalid("invalid_capture")
    кадр, автор = запис.get("image"), запис.get("producer")
    if not isinstance(кадр, dict) or set(кадр) != {"sha256", "url", "crop"} or not isinstance(автор, dict):
        return invalid("invalid_provenance")
    hashes = пакет_контракту()["hashes"]
    if set(автор) != {"kind", "model_id", "model_revision", *hashes} or автор["kind"] != "vision_image_only":
        return invalid("invalid_provenance")
    if any(автор.get(к) != в for к, в in hashes.items()):
        return invalid("contract_hash_mismatch")
    if not _метадані(запис["sku"], кадр["sha256"], кадр["url"], кадр["crop"], автор["model_id"], автор["model_revision"]):
        return invalid("invalid_provenance")
    raw = запис["raw_response"]
    if not isinstance(raw, str) or запис["raw_response_sha256"] != _sha(raw.encode("utf-8")):
        return invalid("raw_hash_mismatch")
    р = перевірити_відповідь(raw)
    try:
        збіг = all(канонічні_байти(запис[к]) == канонічні_байти(р[в]) for к, в in (
            ("visible_item_type", "observation"), ("status", "status"), ("errors", "errors")))
    except (ValueError, TypeError):
        збіг = False
    if not збіг:
        return invalid("observation_mismatch")
    return р


def проєкція(record, *, sku, image_sha256, image_url, crop=None):
    """Факт окремого кадру → тип/слот тільки за зовнішньої тотожності його свідка."""
    р = перевірити_запис(record)
    if р["status"] != "invalid":
        if not _хеш(image_sha256):
            р = dict(status="unknown", observation=None, errors=["image_unverified"])
        elif record["sku"] != sku or record["image"] != dict(sha256=image_sha256, url=image_url, crop=crop):
            р = dict(status="invalid", observation=None, errors=["image_mismatch"])
    тип = р["observation"]["item_type"] if р["status"] == "classified" else "unknown"
    return dict(status=р["status"], item_type=тип, slot=_С.СЛОТ_ТИПУ.get(тип), errors=р["errors"],
                **{к: р["observation"].get(к) if р["observation"] else None for к in ("target", "bbox", "reason")},
                provenance=dict(image=record["image"], producer=record["producer"]) if isinstance(record, dict) and р["status"] != "invalid" else None)


def перевірити_кадри(manifest, receipt):
    """Перевірити ланцюг окремого release-owned приймання, не приймати overlay за свідка.

    Notebook знімає bytesSHA. Root/QA перевіряє байти та публікує receipt; цей
    офлайновий код перевіряє зв'язок файлів, але не підміняє перевірку людини.
    """
    invalid = lambda код: dict(status="invalid", errors=[код], records={})
    if not isinstance(manifest, dict) or not isinstance(receipt, dict):
        return invalid("capture_unverified")
    try:
        digest = _sha(канонічні_байти(manifest))
    except (ValueError, TypeError):
        return invalid("invalid_capture_manifest")
    if manifest.get("version") != "visible_item_capture.v1" or receipt.get("version") != "visible_item_capture_receipt.v1":
        return invalid("invalid_capture_version")
    rev = manifest.get("dataset_revision")
    if not isinstance(rev, str) or not _re.fullmatch(r"[0-9a-f]{40}", rev) or not _хеш(manifest.get("dataset_sha256")):
        return invalid("invalid_dataset")
    if not _хеш(manifest.get("selection_manifest_sha256")):
        return invalid("invalid_dataset")
    if receipt.get("capture_manifest_sha256") != digest or any(receipt.get(k) != manifest[k] for k in ("dataset_revision", "dataset_sha256")):
        return invalid("capture_hash_mismatch")
    if receipt.get("verification") != "actual_bytes_sha256" or not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"].strip():
        return invalid("invalid_receipt")
    evidence = receipt.get("evidence_commit")
    if not isinstance(evidence, str) or not _re.fullmatch(r"[0-9a-f]{40}", evidence):
        return invalid("invalid_receipt")
    records, ids = manifest.get("records"), receipt.get("verified_capture_ids")
    if not isinstance(records, dict) or not isinstance(ids, list) or not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        return invalid("invalid_capture_records")
    verified = {}
    for key in ids:
        r = records.get(key)
        потрібні = {"sku", "source_kind", "source_id", "image_sha256", "bytes_sha256", "image_url", "crop"}
        if not isinstance(r, dict) or not потрібні.issubset(r) or not _хеш(r["image_sha256"]) or r["bytes_sha256"] != r["image_sha256"]:
            return invalid("invalid_capture_record")
        sku = r.get("sku")
        kind = r.get("source_kind")
        if kind not in ("product", "service_control") or (kind == "service_control" and sku is not None):
            return invalid("invalid_capture_source")
        if not _метадані(sku if kind == "product" else "control", r["image_sha256"], r.get("image_url"), r.get("crop"), "capture", "capture"):
            return invalid("invalid_capture_record")
        verified[key] = r
    return dict(status="verified", errors=[], records=verified)


def перевірити_привязку(manifest, receipt, *, capture_id, sku, image_url, crop=None):
    """Зовнішня SKU/URL/crop ціль → перевірений SHA; контролі мають sku=None."""
    р = перевірити_кадри(manifest, receipt)
    кадр = р["records"].get(capture_id) if isinstance(capture_id, str) else None
    if р["status"] != "verified":
        return dict(status="invalid", errors=р["errors"], image_sha256=None)
    if кадр is None:
        return dict(status="unknown", errors=["capture_unverified"], image_sha256=None)
    if кадр["sku"] != sku or кадр["image_url"] != image_url or кадр.get("crop") != crop:
        return dict(status="invalid", errors=["image_mismatch"], image_sha256=None)
    return dict(status="verified", errors=[], image_sha256=кадр["image_sha256"])


def проєкція_каталогу(overlay, manifest, receipt):
    """Окремий простір фото-типу; жодного перезапису старого типу/слоту/кольору."""
    вих, ліч = {}, dict(records=0, projected=0, unprojected=0, controls_excluded=0)
    chain = перевірити_кадри(manifest, receipt)
    if not isinstance(overlay, dict) or overlay.get("version") != ВЕРСІЯ_ФАЙЛА or not isinstance(overlay.get("records"), list):
        return dict(records=вих, ledger=ліч, errors=["invalid_overlay"])
    from collections import Counter
    counts = Counter(r.get("sku") for r in overlay["records"] if isinstance(r, dict) and isinstance(r.get("sku"), str))
    повтори = {sku for sku, count in counts.items() if count > 1}
    for record in overlay["records"]:
        ліч["records"] += 1
        cap = record.get("capture") if isinstance(record, dict) else None
        valid = перевірити_запис(record)
        кадр = chain["records"].get(cap.get("id")) if isinstance(cap, dict) and isinstance(cap.get("id"), str) else None
        if кадр and кадр["source_kind"] == "service_control":
            ліч["controls_excluded"] += 1
            ліч["unprojected"] += 1
            continue
        if (valid["status"] == "invalid" or not кадр or cap.get("manifest_sha256") != _sha(канонічні_байти(manifest))
                or record.get("sku") in повтори):
            ліч["unprojected"] += 1
            continue
        binding = перевірити_привязку(manifest, receipt, capture_id=cap["id"], sku=record.get("sku"),
                                     image_url=record.get("image", {}).get("url"), crop=record.get("image", {}).get("crop"))
        р = проєкція(record, sku=кадр["sku"], image_sha256=binding["image_sha256"], image_url=кадр["image_url"], crop=кадр.get("crop"))
        if binding["status"] != "verified" or р["status"] == "invalid":
            ліч["unprojected"] += 1
            continue
        р["provenance"]["capture"] = cap
        вих[кадр["sku"]] = р
        ліч["projected"] += 1
    return dict(records=вих, ledger=ліч, errors=chain["errors"])


if __name__ == "__main__":
    import argparse as _argparse
    п = _argparse.ArgumentParser(description="Закритий договір фото-типу; без мережі й моделей")
    п.add_argument("--bundle", action="store_true")
    п.add_argument("--overlay", help="Runner results JSONL, поле contract_record")
    п.add_argument("--captures")
    п.add_argument("--receipt")
    п.add_argument("--output")
    args = п.parse_args()
    if args.bundle:
        print(канонічні_байти(пакет_контракту()).decode("utf-8"))
    elif args.overlay and args.captures and args.receipt and args.output:
        from pathlib import Path as _Path
        rows = [_json.loads(s) for s in _Path(args.overlay).read_text(encoding="utf-8").splitlines() if s.strip()]
        overlay = dict(version=ВЕРСІЯ_ФАЙЛА, records=[r["contract_record"] for r in rows if r.get("contract_record") is not None])
        manifest = _json.loads(_Path(args.captures).read_text(encoding="utf-8"))
        receipt = _json.loads(_Path(args.receipt).read_text(encoding="utf-8"))
        result = проєкція_каталогу(overlay, manifest, receipt)
        if result["errors"] or result["ledger"]["unprojected"]:
            п.error("unverified overlay: " + str(result))
        _Path(args.output).write_bytes(канонічні_байти(overlay) + b"\n")
        print(канонічні_байти(result["ledger"]).decode("utf-8"))
    else:
        п.error("use --bundle or --overlay/--captures/--receipt/--output")
