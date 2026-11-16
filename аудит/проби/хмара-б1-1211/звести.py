#!/usr/bin/env python3
"""Зведення прогону хмара-б1-1211: таблиця запитів, ціна, час, ✗ — з логів запитів і журналу сервера (не код продукту)."""
import glob, json, os, re, time, datetime
рядки = [json.loads(l) for l in open("журнал_викликів.jsonl") if l.strip()]
вих = []
for d in sorted(glob.glob("[0-9][0-9]_*/")):
    н = d[:2]; id_ = d[3:-1]
    rc, с = map(int, open(d + "rc_секунд.txt").read().split())
    лог = open(d + "лог.txt", encoding="utf-8").read()
    m = re.search(r"ВПАЛО (\d+)", лог); впало = int(m.group(1)) if m else None
    чотири = bool(re.search(r"чотири картки за", лог))
    крок = re.findall(r"^\s*✗ (.{0,170})", лог, re.M)
    кін = os.path.getmtime(d + "rc_секунд.txt"); поч = кін - с - 3
    викл = [r for r in рядки if r.get("початок_utc") and поч <= (time.mktime(time.strptime(time.strftime("%Y-%m-%d ", time.gmtime(кін)) + r["початок_utc"], "%Y-%m-%d %H:%M:%S")) - time.timezone) <= кін + 2]
    # початок_utc — UTC: перерахунок без часової зони
    викл = []
    for r in рядки:
        t = datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.gmtime(кін)) + " " + r["початок_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
        if поч <= t <= кін + 2: викл.append((t, r))
    iv = sorted((t, t + r["с"]) for t, r in викл); моделі = 0; кінець = 0
    for a, b in iv:
        a = max(a, кінець); 
        if b > a: моделі += b - a; кінець = b
    вих.append(dict(н=н, id=id_, rc=rc, с=с, чотири=чотири, впало=впало, невдачі=крок,
        викликів=len(викл), вихід=sum(r.get("вихід") or 0 for _, r in викл), думка=sum(r.get("думка") or 0 for _, r in викл),
        кеш_запис=sum(r.get("вхід_кеш_запис") or 0 for _, r in викл), кеш_читання=sum(r.get("вхід_кеш_читання") or 0 for _, r in викл),
        нових=sum(r.get("вхід_нових") or 0 for _, r in викл), usd=round(sum(r.get("usd") or 0 for _, r in викл), 4),
        модель_с=round(моделі), не200=sum(1 for _, r in викл if r.get("статус") != 200), обрізано=sum(1 for _, r in викл if r.get("стоп") not in ("end_turn", None)),
        макс_викл=max([r.get("с") for _, r in викл] or [0])))
json.dump(вих, open("зведення.json", "w"), ensure_ascii=False, indent=1)
for x in вих: print(x["н"], x["id"], x["rc"], x["с"], x["чотири"], x["впало"], x["викликів"], x["usd"], x["модель_с"], x["не200"], x["обрізано"], x["макс_викл"], [s[:90] for s in x["невдачі"]])
print("разом", sum(x["с"] for x in вих), sum(x["викликів"] for x in вих), round(sum(x["usd"] for x in вих), 2), sum(x["вихід"] for x in вих), sum(x["думка"] for x in вих), sum(x["кеш_запис"] for x in вих), sum(x["кеш_читання"] for x in вих), sum(x["нових"] for x in вих), sum(x["модель_с"] for x in вих))
print("журнал", len(рядки), round(sum(r.get("usd") or 0 for r in рядки), 4), max(r.get("макс_одночасно_досі") or 0 for r in рядки))
