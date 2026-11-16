"""Друкує незалежну звірку сирої картки з записом і рядком голови #4045.

Продукт і таблицю читань не змінює; моделі не викликає.
"""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import pickle
import sys
import xml.etree.ElementTree as ET


def main():
    """Звіряє три справжні картки та непрочитані значення на вказаному дереві."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--дерево", required=True, type=Path)
    parser.add_argument("--кеш", type=Path)
    parser.add_argument("--вихід", type=Path)
    args = parser.parse_args()
    tree = args.дерево.resolve()
    cache = args.кеш.resolve() if args.кеш else None
    output = args.вихід.resolve() if args.вихід else None
    sys.path.insert(0, str(tree / "джерела"))
    os.chdir(tree / "джерела")
    import картка_взуття as table
    import фід_взуття as feed
    import дріт_моделі as wire

    catalog = pickle.load(cache.open("rb")) if cache else []
    by_id = {r["id"].split("@")[0]: r for r in catalog if r.get("слот") == "взуття"}
    raw = ET.parse(gzip.open(tree / "каталог_повний.xml.gz")).getroot()
    cards = {o.get("id"): {p.get("name", "").strip().lower(): p.text or "" for p in o.findall("param")}
             for o in raw.findall(".//offer")}
    coverage, differences, skipped = Counter(), [], []
    fields = {"каблук_вид": "heel_shape", "каблук_рівень": "heel_height", "підошва_коди": "sole",
              "сезон_пари": "wear_season", "підкладка_коди": "lining"}
    for item_id, record in by_id.items():
        params = cards.get(item_id)
        coverage["пар"] += 1
        coverage["картка_знайдена_без_фільтра_слоту"] += params is not None
        if params is None:
            continue
        expected = table.ознаки(params)
        row = wire.осі({}, dict(record, слот="взуття"))
        for key, row_key in fields.items():
            if key not in expected:
                continue
            coverage["картка_назвала_" + row_key] += 1
            actual = row.get(row_key)
            actual = actual if isinstance(actual, list) else [actual]
            if not set(expected[key]).issubset(actual):
                differences.append({"id": item_id, "ключ": row_key,
                                    "очікувано": expected[key], "рядок": actual})
        if params.get("слот") != "взуття":
            skipped.append({"id": item_id, "сирий_слот": params.get("слот"),
                            "слова_картки": {k: v for k, v in params.items() if k in {"склад", "~склад"}},
                            "картка_кодами": expected,
                            "рядок": {k: row[k] for k in fields.values() if k in row}})
    # Читання перевіряльника GPT з наведених у виході слів картки, незалежне від таблиці автора PR.
    lining = {"ж-08844": "faux_fur", "ж-08853": "flannel", "ж-10245": "leather",
              "ж-10413": None, "ж53-c0f39ea04e3026fb3384": "textile"}
    lost = []
    for item_id, expected_lining in lining.items():
        record = by_id.get(item_id)
        if record is None:
            continue
        row = wire.осі({}, dict(record, слот="взуття"))
        expected = {"sole": "rubber"}
        if expected_lining:
            expected["lining"] = expected_lining
        for key, value in expected.items():
            actual = row.get(key)
            if value not in (actual if isinstance(actual, list) else [actual]):
                lost.append({"id": item_id, "ключ": key, "картка_каже": value, "рядок": actual})
    examples = []
    compound = []
    for offer in raw.findall(".//offer"):
        params = {p.get("name", "").strip().lower(): p.text or "" for p in offer.findall("param")}
        if params.get("слот") != "взуття":
            continue
        for name, value in params.items():
            if name == "~висота підошви" and "Висота підборів:" in value:
                compound.append({"id": offer.get("id"), "поле": name, "значення": value,
                                 "група_таблиці": table.група(name)})
        if offer.get("id") not in {"ж-08718", "ж-09146", "ж-09855"}:
            continue
        direct = feed.взуттєві_поля({"назва": offer.findtext("name"), "параметри": params}, "чоботи")
        record = by_id.get(offer.get("id"), direct)
        examples.append({
            "id": offer.get("id"),
            "є_в_повному_каталозі": offer.get("id") in by_id if cache else None,
            "картка": {k: v for k, v in params.items()
                       if k in {"~висота підошви", "~підошва з підбором 1.4 см, матеріал", "каблук_см"}},
            "запис": {k: v for k, v in record.items()
                      if any(s in k for s in ("каблук", "підошв", "підклад", "не_прочитано"))},
            "рядок": {k: v for k, v in wire.осі({}, dict(record, слот="взуття")).items()
                      if k in {"heel", "heel_shape", "heel_height", "heel_cm", "sole", "wear_season", "lining"}},
        })
    states = []
    for name in ("~Форма підбора", "~Висота підборів", "~Матеріал підошви", "~Сезон", "~Матеріал підкладки"):
        record = feed.картка_в_запис({}, {name: "Нове значення поза таблицею"})
        states.append({"поле": name, "рядок": wire.осі({}, dict(record, слот="взуття"))})
    result = json.dumps({"пар_повного_каталогу": len(by_id) if cache else None,
                      "повне_покриття": dict(coverage),
                      "розбіжності_кодів_картки_й_рядка": differences,
                      "пари_поза_звіркою_автора": skipped,
                      "втрати_незалежного_читання": lost,
                      "складене_поле_поза_таблицею": compound,
                      "картки": examples, "непрочитані_значення": states}, ensure_ascii=False, indent=2)
    if output:
        output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
