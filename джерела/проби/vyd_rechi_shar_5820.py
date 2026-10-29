"""Вид речі кодом у перекладі картки (рядки 5820, 3782, 1426): replay записаних викликів шару з переліком речей
(`аудит/живі_1083`, VIDPOVIDI `*мовний_шар*`) — новим промптом (`мовний_шар.промпт`, тип з укладки речі у вердиктах).
Без моделі друкує, скільки речей має код виду; з MODEL_URL і MODEL_MOVA (LM Studio) шле промпт і друкує по речі
код виду, назву й початок перекладу її абзацу (іменник виду — очима) та урізані переклади (`прийняти`.короткі).
Запуск: [MODEL_URL=http://127.0.0.1:1234/v1 MODEL_MOVA=…] python3 проби/vyd_rechi_shar_5820.py <тека живі_1083>"""
import sys, os, re, json, glob, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import мовний_шар as МШ

URL, М = os.environ.get("MODEL_URL"), os.environ.get("MODEL_MOVA")
РЯДОК = re.compile(r"^(\d+) — (.+?)(?: · colour code: (\S+))?(?: · about it: text н=(\d+))?$")
всього = з_кодом = 0
for сц in sorted(glob.glob(os.path.join(sys.argv[1], "*/вердикти.txt"))):
    тип = {р.get("назва"): {к: v for к, v in (("тип", (р.get("укладка") or {}).get("тип")), ("слот", р.get("слот"))) if v}
           for п in json.load(open(сц, encoding="utf8"))["прогони"] for в in п["вердикти"]
           for р in в.get("речі_образу") or [] if "@" in str(р.get("id"))}
    for ф in sorted(glob.glob(os.path.join(os.path.dirname(сц), "VIDPOVIDI", "*мовний_шар.txt"))):
        т = open(ф, encoding="utf8").read()
        if "Речі образу — перелік" not in т or '"виправ"' in т:
            continue
        тексти = json.loads(т.split("ТЕКСТИ:\n", 1)[1].split("\n\n── ВІДПОВІДЬ", 1)[0])
        р = МШ.розмітити({"т%d" % х["н"]: х["текст"] for х in тексти})
        речі = [dict(н=int(м[1]), назва=м[2], **тип.get(м[2], {}),
                     **({"код_кольору": м[3]} if м[3] else {}), **({"опис": "т" + м[4]} if м[4] else {}))
                for м in (РЯДОК.match(л) for л in т.split("(номер речі — назва біля неї):\n", 1)[1].split("\n")) if м]
        пр = МШ.промпт(р, речі)
        всього += len(речі); з_кодом += пр.count(" · kind code: ")
        print("==", os.path.basename(os.path.dirname(сц))[:16], os.path.basename(ф), "речей", len(речі), "з кодом виду", пр.count(" · kind code: "))
        if not (URL and М):
            continue
        з = urllib.request.Request(URL.rstrip("/") + "/chat/completions", headers={"Content-Type": "application/json"},
                                   data=json.dumps(dict(model=М, messages=[{"role": "user", "content": пр}], **МШ.ВИБІРКА)).encode())
        прий = МШ.прийняти(р, json.load(urllib.request.urlopen(з, timeout=600))["choices"][0]["message"]["content"])
        for рч in речі:
            код = (re.search(r"^%d — .*kind code: (\S+)" % рч["н"], пр, re.M) or [None, "—"])[1]
            print("  %s | %s | %s" % (код, рч["назва"][:34], (прий["тексти"].get(рч.get("опис")) or "—")[:80]))
        print("  урізано:", list(прий.get("короткі") or {}), "· без відповіді:", прий.get("без_відповіді"))
print("ПІДСУМОК: речей у переліках", всього, "· з кодом виду", з_кодом)
