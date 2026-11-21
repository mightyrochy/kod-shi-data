"""Наряд `Збирання-запит-склад`, крок 2: розмір запитів ремонту й вибору ПІСЛЯ правки дроту вердикта — та сама функція
коду (`дріт_моделі.без_типових_полів_заяв`) над записаними запитами, плюс зняті неперевірені пункти (`checklist.not_run`,
`not_run_everywhere` і його рядок входу). Нових викликів моделі нема.
Запуск із кореня:  python3 аудит/проби/Збирання-запит-склад/після_дроту.py"""
import glob, gzip, json, os, sys, statistics as st
sys.path.insert(0, os.path.join(os.getcwd(), "джерела"))
import дріт_моделі as _Д

ФАЙЛИ = sorted(glob.glob("аудит/проби/Живий-через-міст/стенд/службове/с*/обміни.jsonl")) + \
    sorted(glob.glob("аудит/проби/живий-як-людина-4/стенд/службове/с*/обміни.jsonl.gz"))


def після(т):
    т = dict(т)
    т.pop("not_run_everywhere", None)
    з = dict(т["task"])
    з["input"] = [р for р in з.get("input") or [] if not р.startswith('"not_run_everywhere"')]
    т["task"] = з
    for к in ("verdict",):
        вих = []
        for о in т.get(к) or []:
            о = dict(о)
            ч = {б: {"failed": п["failed"]} for б, п in (о.get("checklist") or {}).items() if п.get("failed")}
            if "checklist" in о:
                if ч:
                    о["checklist"] = ч
                else:
                    del о["checklist"]
            вих.append(о)
        т[к] = вих
    return _Д.без_типових_полів_заяв(т)


def зн(о):
    return len(json.dumps(о, ensure_ascii=False, separators=(",", ":")))


Р = {"ремонт": [], "вибір": []}
for ф in ФАЙЛИ:
    with (gzip.open(ф, "rt") if ф.endswith(".gz") else open(ф)) as в:
        for р in в:
            д = json.loads(р)
            if д.get("статус") != 200:
                continue
            т = "".join(б.get("text", "") for б in json.loads(д["запит"])["messages"][0]["content"] if б.get("type") == "text")
            try:
                о = json.loads(т)
            except ValueError:
                continue
            роль = (о.get("task") or {}).get("role", "") if isinstance(о.get("task"), dict) else ""
            к = "ремонт" if "Improve the outfits" in роль else "вибір" if "Choose one" in роль else None
            if к:
                Р[к].append((зн(о), зн(після(о))))
for к, пп in Р.items():
    до, пі = st.mean(x for x, _ in пп), st.mean(y for _, y in пп)
    print(f"{к}: викликів {len(пп)}; знаків ДО {до:,.0f} → ПІСЛЯ {пі:,.0f} ({100 * (пі - до) / до:+.0f} %);"
          f" макс ДО {max(x for x, _ in пп):,} → ПІСЛЯ {max(y for _, y in пп):,}")
