#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перевірка відтворюваності вибірки 40 записів (зерно 20261115) і підсумків виміру очима."""
import csv
import gzip
import json
import random
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
SRC_GZ = HERE.parent / "кадр_варіант_кв1_канал_1411" / "результати.jsonl.gz"
VYBIRKA_TSV = HERE / "вибірка.tsv"
KADRY_TSV = HERE / "кадри.tsv"

SEED = 20261115
SAMPLE_SIZE = 40


def main():
    population = []
    with gzip.open(SRC_GZ, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("стан") == "невідомо" and r.get("причини") == ["нема_свідчення_одного_кольору"]:
                population.append(r)

    assert len(population) == 2508, f"Очікувалось 2508 записів, знайдено {len(population)}"
    assert [r["ід"] for r in population] == sorted(r["ід"] for r in population), "Порушено сортування за ід"

    expected = random.Random(SEED).sample(population, SAMPLE_SIZE)

    with open(VYBIRKA_TSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    assert len(rows) == SAMPLE_SIZE, f"У вибірка.tsv {len(rows)} рядків замість {SAMPLE_SIZE}"

    for i, (exp, row) in enumerate(zip(expected, rows), 1):
        exp_shop = urlsplit(exp["адреса"]).netloc.lower()
        assert row["ід"] == exp["ід"], f"Рядок {i}: ід {row['ід']} != {exp['ід']}"
        assert row["крамниця"] == exp_shop, f"Рядок {i}: крамниця {row['крамниця']} != {exp_shop}"
        assert row["адреса"] == exp["адреса"], f"Рядок {i}: адреса {row['адреса']} != {exp['адреса']}"
        assert row["вердикт_1"] in ("так", "ні", "не видно"), f"Рядок {i}: невідомий вердикт_1 {row['вердикт_1']}"
        assert row["вердикт_2"] in ("так", "ні", "не видно"), f"Рядок {i}: невідомий вердикт_2 {row['вердикт_2']}"
        assert row["що_видно"].strip(), f"Рядок {i}: порожнє поле що_видно"

    with open(KADRY_TSV, "r", encoding="utf-8") as f:
        frame_rows = list(csv.DictReader(f, delimiter="\t"))

    exp_frames = []
    for i, exp in enumerate(expected, 1):
        for fi, url in enumerate(exp["запис"]["фото"], 1):
            exp_frames.append((str(i), exp["ід"], str(fi), url))

    assert len(frame_rows) == len(exp_frames) == 254, f"Кадрів {len(frame_rows)} замість 254"
    for fr, (idx_s, rid, fi_s, url) in zip(frame_rows, exp_frames):
        assert (fr["номер"], fr["ід"], fr["кадр"], fr["адреса_кадру"]) == (idx_s, rid, fi_s, url)

    frames_by_id = defaultdict(list)
    for fr in frame_rows:
        frames_by_id[fr["ід"]].append(fr)

    by_shop = defaultdict(lambda: {"всього": 0, "в1_так": 0, "в2_так": 0, "обидва_так": 0, "суворо_обидва_так": 0})
    totals = {"всього": 0, "в1_так": 0, "в2_так": 0, "обидва_так": 0, "суворо_обидва_так": 0}

    for row in rows:
        rid = row["ід"]
        shop = row["крамниця"]
        v1 = row["вердикт_1"] == "так"
        v2 = row["вердикт_2"] == "так"
        all_200 = all(fr["http_код"] == "200" for fr in frames_by_id[rid])
        v2_strict = v2 and all_200

        for d in (by_shop[shop], totals):
            d["всього"] += 1
            d["в1_так"] += int(v1)
            d["в2_так"] += int(v2)
            d["обидва_так"] += int(v1 and v2)
            d["суворо_обидва_так"] += int(v1 and v2_strict)

    assert totals["всього"] == 40
    assert totals["в1_так"] == 39
    assert totals["в2_так"] == 39
    assert totals["обидва_так"] == 38
    assert totals["суворо_обидва_так"] == 35

    print(f"Звірено успішно: сукупність = {len(population)}, зерно = {SEED}, вибірка = {len(rows)}, кадрів = {len(frame_rows)}.")
    print(f"Вердикт 1 «так»: {totals['в1_так']}/40")
    print(f"Вердикт 2 «так» (за всіма завантаженими HTTP 200 кадрами галереї): {totals['в2_так']}/40")
    print(f"Обидва «так» (за завантаженими HTTP 200 кадрами галереї): {totals['обидва_так']}/40")
    print(f"Обидва «так» (суворо за всіма URL запис.фото без жодного HTTP 404): {totals['суворо_обидва_так']}/40")
    print("\nЗа крамницями (крамниця | вибірка | В1=так | В2=так | обидва=так [HTTP 200] | обидва=так [суворо всі URL]):")
    for shop, st in sorted(by_shop.items(), key=lambda kv: (-kv[1]["всього"], kv[0])):
        print(
            f"  {shop:22s} | {st['всього']:2d} | {st['в1_так']:2d}/{st['всього']:<2d} | "
            f"{st['в2_так']:2d}/{st['всього']:<2d} | {st['обидва_так']:2d}/{st['всього']:<2d} | "
            f"{st['суворо_обидва_так']:2d}/{st['всього']:<2d}"
        )


if __name__ == "__main__":
    main()
