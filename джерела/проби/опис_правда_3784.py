"""Рядки 3784, 6621 (наряд ОПИС-ПРАВДА). Replay записів живих: картка руки 1–2 ↔ останній промпт ОПИС_V1 з тими самими
речами. (1) `your_declared`: ДО — речі записаного промпту без знахідки коду (хід без `правило` чи з правилом, якого нема
в `знахідки_коду` картки); ПІСЛЯ — ті самі ходи запису через `заяви_ходу` → `опис_обʼєкт` → дріт. (2) «заправ» при
`goal_zones` belly/hips — рядки відповіді опису з «tuck» (не «tuck … arm/hand»); ПІСЛЯ — ця сама проба на записах
нового живого прогону. Запуск: cd джерела && python3 проби/опис_правда_3784.py [гілка:тека …]"""
import json, os, re, subprocess, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import протокол as П, розбір_відповідей as РВ
sh = lambda *a: subprocess.run(["git", "-c", "core.quotepath=false", *a], capture_output=True, text=True).stdout
ТЕКИ = sys.argv[1:] or ["origin/claude/zhyvi-14:аудит/живі_14/А/11_ж7_мороз_без_відкритого"] + [
    "origin/claude/zhyvi-1016-2:аудит/живі_1016_2/%s" % т for т in ("08_ж4_робота_живіт", "09_ж4_робота_живіт", "10_ж4_робота_живіт")]
ЗАПРАВ, дек = re.compile(r"\btuck(?!\w)(?!\s+(?:one|your|an?)\s+(?:arm|hand))", re.I), json.JSONDecoder()
до_без = до_без_коду = після_без = після_є = заправ = карток = 0
for гт in ТЕКИ:
    г, т = гт.split(":", 1)
    описи = []
    for ф in sorted(ф for ф in sh("ls-tree", "-r", "--full-tree", "--name-only", г, т + "/VIDPOVIDI/").split() if "_ОПИС_V1_" in ф):
        с = sh("show", "%s:%s" % (г, ф)); п = дек.raw_decode(с, с.index('{"version"'))[0]
        в = с[с.index("── ВІДПОВІДЬ"):]; в = П.розбір_за_схемою(в[в.index("\n") + 1:], "ОПИС_ВІДПОВІДЬ_V1")[0] or {}
        описи.append((п, в))
    вт = sh("show", "%s:%s/вердикти.txt" % (г, т))
    for к in [дек.raw_decode(вт, м.start())[0] for м in re.finditer(r'\{"рука":"[12]"', вт)]:
        назви = {р["назва"]: р["id"] for р in к.get("речі_образу") or []}
        пв = [(п, в) for п, в in описи if {x["name"] for x in п["outfit"]["items"]} == set(назви)]
        if not пв: continue
        п, в = пв[-1]; карток += 1; ід_н = {назви[x["name"]]: x["n"] for x in п["outfit"]["items"]}
        ходи, зн = (к["етапи"].get("суд") or {}).get("свідомі") or [], к.get("знахідки_коду") or []
        з_кодом = {і for х in ходи if РВ.заяви_ходу(х, зн) for і in х.get("ід_речей") or []}
        до_без += sum(1 for н in п.get("your_declared") or [] if н not in {ід_н.get(і) for і in з_кодом})
        до_без_коду += sum(1 for н in п.get("your_declared") or [] if н not in {ід_н.get(і) for х in ходи if х.get("правило") for і in х.get("ід_речей") or []})
        об = РВ.опис_обʼєкт([dict(н=н, назва="-") for н in ід_н.values()], свідомі=[dict(н=ід_н[і], заяви=РВ.заяви_ходу(х, зн))
                            for х in ходи for і in х.get("ід_речей") or [] if і in ід_н])
        дріт = (lambda x: json.loads(x) if isinstance(x, str) else x)(РВ.промпт_опису(об)).get("your_declared") or []
        після_є += len({x["item"] for x in дріт}); після_без += len({x["item"] for x in дріт if not x.get("statements")})
        if set((п.get("case") or {}).get("goal_zones") or []) & {"belly", "hips"}:
            рядки = list(РВ._список(в.get("як_носити"))) + [в.get("текст") or ""] + [x.get("текст") or "" for x in в.get("про_речі") or []]
            заправ += sum(1 for р in рядки for _ in ЗАПРАВ.finditer(str(р)))
print("карток %d · your_declared без знахідки в суді картки: записано %d (з них без коду ходу %d) → тепер %d; із знахідкою тепер %d"
      " · «tuck» при belly/hips у записаних відповідях %d" % (карток, до_без, до_без_коду, після_без, після_є - після_без, заправ))
