"""Незалежні офлайн-виміри PR 3747. Аргументи: корінь дерева, режим."""
import collections
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root / "джерела"), str(root / "zhnyvarka")]
os.chdir(root)
mode = sys.argv[2]

if mode == "опис":
    for p in sorted((root / "джерела/проби").glob("кадр_варіант_*.py")):
        print(p.name, " ".join(p.read_text(encoding="utf-8").splitlines()[:4]))

elif mode == "каталог":
    import feed
    import фід_власник_кадру as owner
    offers = feed.читати_yml(feed.каталог_на_диску())[0]
    counts = collections.Counter()
    for o in offers:
        p = o.get("параметри") or {}
        if p.get("канал") != "картка":
            continue
        counts["записів"] += 1
        counts["поле_власника"] += "власник_кадру" in p
        counts["доведений_власник"] += any(owner.доказ_варіанта(o, frame) for frame in o.get("фото") or [])
    counts["невідомо"] = counts["записів"] - counts["доведений_власник"]
    print("читач XML:", json.dumps(counts, ensure_ascii=False, sort_keys=True))
    counts = collections.Counter()
    with gzip.open(root / "каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            params = rec.get("параметри") or []
            p = {x[0]: x[1] for x in params} if isinstance(params, list) else params
            if p.get("канал") != "картка":
                continue
            counts["записів"] += 1
            counts["свотчі"] += bool(p.get("свотч_джерело"))
            counts["без_свотчів_з_id_і_кадрами"] += not p.get("свотч_джерело") and bool(p.get("id_магазину")) and bool(rec.get("кадри"))
    print("знімок JSONL:", json.dumps(counts, ensure_ascii=False, sort_keys=True))

elif mode == "структура":
    with gzip.open(root / "каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            p = {x[0]: x[1] for x in rec.get("параметри") or []}
            if p.get("канал") == "картка":
                print(json.dumps(rec, ensure_ascii=False)[:6000])
                break

elif mode == "сировина":
    import фід_власник_кадру as owner
    keys = collections.Counter()
    count = collections.Counter()
    with gzip.open(root / "каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            p = {x[0]:x[1] for x in r.get("параметри") or []}
            if p.get("канал") != "картка":
                continue
            count["записів"] += 1
            count["без_свотча"] += not bool(p.get("свотч_джерело"))
            count["верхня_межа"] += not p.get("свотч_джерело") and bool(p.get("id_магазину")) and bool(r.get("кадри"))
            count["поле_власника"] += "власник_кадру" in p
            o = dict(id=r.get("ід"), url=r.get("адреса"), фото=r.get("кадри"), параметри=p)
            count["доведений_читачем"] += any(owner.доказ_варіанта(o, frame) for frame in r.get("кадри") or [])
            for key in p:
                if "свотч" in key:
                    keys[key] += 1
    count["невідомо"] = count["записів"] - count["доведений_читачем"]
    print(json.dumps(dict(лічба=count, свотчі=keys), ensure_ascii=False))

elif mode == "довідник":
    sys.path.insert(0, str(root / "джерела/прилади"))
    from експорт_показу import довідник
    Path(sys.argv[3]).write_text(json.dumps(довідник(), ensure_ascii=False), encoding="utf-8")

elif mode == "колір":
    import жнива_запис as m
    base = "https://shop.test/products/dress?variant=11"
    urls = ["https://shop.test/a.jpg", "https://shop.test/b.jpg"]
    def offer(kind, n):
        p = {"id_магазину": "7"}
        if kind != "без поля":
            value = "невідомо" if kind == "невідомо" else dict(
                джерело="shopify:variant_ids", товар="7", адреса=base, варіанти=["11", "12"],
                зв_язки={u: ["11"] for u in urls[:n]})
            if kind == "другий невідомий":
                value["зв_язки"].pop(urls[1], None)
            if kind == "різні розміри одного кольору":
                value["зв_язки"][urls[1]] = ["12"]
            p["власник_кадру"] = json.dumps(value, ensure_ascii=False)
        return dict(id="probe", url=base, фото=urls[:n], параметри=p, назва="Сукня", магазин="shop.test")
    def surface(paths, slot, main):
        return dict(кадри=dict(обрано=0, розкид=0 if len(paths) > 1 else None, до_чужого=None, згідних=len(paths)),
                    частка=0.8, кластери=[], чому="офлайн", джерело="офлайн", світліша=None, поверхня=None)
    common = dict(тип_речі=lambda _: ("Сукня", "сукня"), слова_крамниці=lambda _: [],
                  обрати_кадр=lambda photos, *_: (0, None, {str(i+1): "ціла" for i in range(len(photos))}, "офлайн"),
                  поверхня_кадрів=surface, стиснути_поверхню=lambda _: None,
                  походження_кадру=lambda *args: dict(sha256="однакові байти", клас="ціла"),
                  набір_слота=lambda _: "сукня", це_сукня=lambda *_: True,
                  ПРОМПТ_НАБОРУ={"сукня": ""}, _підставити=lambda *a, **k: "",
                  _фото_1024=lambda _: None, _b64=lambda *a, **k: "", _запит=lambda *a, **k: {},
                  нормалізувати=lambda *a, **k: dict(опис="офлайн"),
                  звести_колір=lambda *a: (dict(слово="червоний", hex="#cc0000"), dict(слово="чорний", hex="#000000"), None),
                  впевненість=lambda *a: 0.9)
    for kind, n in [("без поля", 1), ("невідомо", 1), ("доведений", 1), ("доведений", 2),
                    ("другий невідомий", 2), ("різні розміри одного кольору", 2)]:
        photos = [dict(url=u, шлях="офлайн.jpg") for u in urls[:n]]
        with patch.multiple(m, **common), patch.object(m.F, "тип_речі", return_value="сукня"):
            result = m.обробити(offer(kind, n), photos, "офлайн", показ=False)
        print(json.dumps(dict(випадок=kind, кадрів=n,
                              основний=result["запис"]["колір_основний"] is not None,
                              другий=result["запис"]["колір_другий"] is not None,
                              власники=result["вимір"]["кадри"]["власники"],
                              сирі_id=[(m.доказ_кадру(offer(kind, n), f) or {}).get("ід_варіацій") for f in photos]), ensure_ascii=False))

elif mode == "запис":
    spec = importlib.util.spec_from_file_location("measure", root / "аудит/жнива_5_3/2026-11-06_запис/вимір_запису.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
