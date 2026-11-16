"""Друкує незалежну звірку сирої картки з записом і рядком голови #4045.

Продукт і таблицю читань не змінює; моделі не викликає.
"""
import argparse
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
    args = parser.parse_args()
    tree = args.дерево.resolve()
    cache = args.кеш.resolve() if args.кеш else None
    sys.path.insert(0, str(tree / "джерела"))
    os.chdir(tree / "джерела")
    import картка_взуття as table
    import фід_взуття as feed
    import дріт_моделі as wire

    catalog = pickle.load(cache.open("rb")) if cache else []
    by_id = {r["id"].split("@")[0]: r for r in catalog if r.get("слот") == "взуття"}
    raw = ET.parse(gzip.open(tree / "каталог_повний.xml.gz")).getroot()
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
    print(json.dumps({"пар_повного_каталогу": len(by_id) if cache else None,
                      "складене_поле_поза_таблицею": compound,
                      "картки": examples, "непрочитані_значення": states}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
