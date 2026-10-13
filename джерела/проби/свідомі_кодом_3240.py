"""Рядок 3240: хід ремонту, адресований ід знахідки, доходить до вибору. Replay живих 13 А/08, А/09 (руки 1–2, гілка
claude/zhyvi-13; модель — записані відповіді): ходи «declined»/«deliberate» останнього ремонту з ід знахідки (правило —
код заяви на дроті) → злиття доробки кодом бази eb7b3c7b (ДО) і цим (ПІСЛЯ) → послаблення зауважень обраного образу
(верхня межа: ходи вважаються такими, що лишились у новому суді). Запуск: cd джерела && python3 проби/свідомі_кодом_3240.py"""
import json, os, re, subprocess, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import протокол as П, повнота_образу as НОВЕ, розбір_відповідей as РВ
sh = lambda *a: subprocess.run(["git", "-c", "core.quotepath=false", *a], capture_output=True, text=True).stdout
СТАРЕ = {"__name__": "повнота_старе"}; exec(sh("show", "eb7b3c7b:джерела/повнота_образу.py"), СТАРЕ)
Г, ко, ДІЇ = "origin/claude/zhyvi-13", lambda z: next(iter(z)) if isinstance(z, dict) else z, ("виправлено", "відхилено", "частково")
for сц in ("08_ж7_мороз_без_відкритого", "09_ж2_корпоратив_виділитися"):
    тека, файли = "аудит/живі_13/А/%s/" % сц, {}
    for ф in [ф for ф in sh("ls-tree", "-r", "--full-tree", "--name-only", Г, тека + "VIDPOVIDI/").split() if "ВЕРДИКТ" in ф]:
        т = sh("show", "%s:%s" % (Г, ф)); і = т.index("── ВІДПОВІДЬ")
        файли[int(re.search(r"\((\d+) симв", т).group(1))] = json.loads(т[т.index("{"):і])
    т = sh("show", "%s:%sвердикти.txt" % (Г, тека))
    for в in [json.JSONDecoder().raw_decode(т, м.start())[0] for м in re.finditer(r'\{"рука":"[12]"', т)]:
        св, ходи, дії, крок, пр = в["етапи"]["суд"].get("свідомі") or [], [], [0, 0], None, None
        for x in в["етапи"]["виклики"]:      # промпт виклику — за довжиною; повтор формату — промпт того самого кроку
            крок, пр = x["крок"], файли.get((x.get("запит") or {}).get("символів")) or (пр if x["крок"] == крок else None)
            об = (П.розбір_за_схемою(x.get("відповідь_сира") or "", "ВИБІР_V1" if крок == "choice" else "ОБРАЗИ_V1")[0] or {}) if пр else {}
            if крок == "repair" and об.get("образи"):
                зн = {П.ід_з_дроту(z["id"]): (ко(z["statements"][0]), z.get("items") or []) for v in пр["verdict"] for z in v.get("findings") or []}
                вик = [x for о in об["образи"] for x in о.get("виконано") or []]
                дії = [sum(1 for x in вик if x["дія"] not in ДІЇ), len(вик)]
                ходи = [dict(ід=о["ід"], річ=", ".join(зн[x["знахідка"]][1]), чому=x.get("чому"), правило=зн[x["знахідка"]][0])
                        for о in об["образи"] for x in (о.get("виконано") or []) + (о.get("свідомо") or [])
                        if x.get("знахідка") in зн and x.get("чому") and x.get("дія", "відхилено") == "відхилено"]
            if крок == "completeness_repair" and ходи:
                база = dict(образи=[dict(ід=о, свідомі=[h for h in ходи if h["ід"] == о]) for о in dict.fromkeys(h["ід"] for h in ходи)])
                злито = {н: (м["злити_з_неторканими"](об, база) or [{}])[0] for н, м in (("ДО", СТАРЕ), ("ПІСЛЯ", vars(НОВЕ)))}
            if крок == "choice" and ходи and об.get("обрано"):
                рем = [dict(ід=z["id"], правило=c, речі=z.get("items"), сила_нп=1.0) for c, л in пр["remarks_by_code"].items()
                       for z in л if z["outfit"] == П.ід_на_дріт(об["обрано"])]
                for н, о in злито.items():
                    х = [dict(текст=s.get("чому") or "", правило=s["правило"], ід_речей=s["річ"].split(", ")) for оо in о.get("образи") or []
                         if оо.get("ід") == об["обрано"] for s in оо.get("свідомо") or [] if s.get("правило")]
                    print("%s рука %s · %-5s у вибір %s ходів з кодом %d (%s), послаблено %d із %d зауважень" % (сц[:2], в["рука"], н, об["обрано"],
                          len(х), ", ".join(h["правило"] for h in х) or "—", sum(1 for z in РВ._застосувати_свідомі(рем, х, [])[0] if z.get("свідомий")), len(рем)))
        print("%s рука %s · останній ремонт: ходів з ід %d · «action» поза переліком %d із %d · ЗАПИС суд.свідомі %d, з кодом %d, послаблено %d"
              % (сц[:2], в["рука"], len(ходи), дії[0], дії[1], len(св), sum(1 for x in св if not x.get("без_коду")), sum(x.get("послаблено", 0) for x in св)))
