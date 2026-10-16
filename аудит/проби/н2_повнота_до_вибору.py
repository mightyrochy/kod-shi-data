"""Н2, замір (рядки 5238, 5246): ремонт повноти ДО вибору на записаних промптах живих прогонів.

Входи — записи `VIDPOVIDI/*ОБРАЗИ_V1.txt` з роллю «before she chooses» у теках сцен (живі 1510 А, 1083). На кожен запис:
  · промпт, перебудований ЧИННИМ кодом (`повнота_образу.ПОВНОТА_ВСІ`, `збирач_промптів.зібрати`) з тих самих даних дроту
    («case», «day», «verdict», «showcase», «she_refuses»): `options` кожної діри — `повнота_образу._варіанти_блокера` над
    вітриною, розкладеною за слотами з `type` речі (`внутрішня_мова.СЛОТ_ТИПУ`; речі без `type` у цих записах — паски,
    слот «пояс»), порядком вітрини запису, як `дріт_моделі.вердикт`;
  · відповідь, розібрана чинним мостом: ходи (`ДОПОВНЕННЯ_V1` → `доповнити`), інакше стара форма (ОБРАЗИ_V1), і далі
    `злити_з_неторканими` — той самий порядок, що в `міст_відповіді`;
  · закриття: чи склад після злиття закриває САМЕ блокери запису (слот — з `type`, як вище; адреси дубля й мінімум речей —
    із заяв) і чи не поставив додану річ у сім'ю слота, де річ уже є (`лишились`). Повний суд структури тут не годиться:
    без пулу прогону двослотові речі (жакет, кардиган) і «одна річ» розходяться з записом у 21 з 55 образів; повний суд
    дає живий прогін стенда.
Друкує на запис: образів з дірою в промпті і скільки з них ПІСЛЯ без блокера; «done-n ∉ items» (номер у «done»/«deliberate»,
якого не було в образі й нема в «items»); номери відповіді, що не дійшли до складу; образів, що втратили річ без прохання
(поза групою дубля); скільки речей додано.
Режими: без ключа — записані відповіді (хмара); `--живо` — перебудований промпт іде моделі (`MODEL_URL`, `MODEL`, temperature
0, `MAX_TOKENS` 4000 — як `гг1_повтор_ремонту.py`), відповідь лягає в `VYVID/сирі/` (типово ../аудит/н2_замір) і судиться так
само; записана відповідь не кличеться вдруге. `--промпти` — ще й кладе перебудовані промпти в `VYVID/промпти/`.
Запуск із джерела/:  python3 ../аудит/проби/н2_повнота_до_вибору.py [--живо] [--промпти] <тека живих> […]"""
import collections as K, glob, hashlib, json, os, re, sys, time, urllib.request
sys.path.insert(0, ".")
import протокол as _ПР, збирач_промптів as _ЗП, повнота_образу as ПО, внутрішня_мова as _ВМ, суд_від_моделі as СУД

АДРЕСА = (os.environ.get("MODEL_URL") or "http://127.0.0.1:1234/v1").rstrip("/")
МОДЕЛЬ = os.environ.get("MODEL") or "qwen/qwen3.5-9b"
МАКС_ТОКЕНІВ = int(os.environ.get("MAX_TOKENS") or 4000)
ВИВІД = os.environ.get("VYVID") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "н2_замір")
НОМЕР = re.compile(r"#\d+·\d{2}")


def записи(теки):
    """(шлях, промпт dict, відповідь, шапка) кожного запису ремонту повноти до вибору."""
    for т in теки:
        for ф in sorted(glob.glob(os.path.join(т, "*", "VIDPOVIDI", "*.txt")) + glob.glob(os.path.join(т, "VIDPOVIDI", "*.txt"))):
            с = open(ф, encoding="utf8", errors="replace").read()
            г = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^\n]*)\) ──\n(.*)\n$", с, re.S)
            if г and "before she chooses" in г.group(1)[:600]:
                yield ф, json.loads(г.group(1)), г.group(3), г.group(2)


def слот(р):
    """Слот ядра речі дроту з її `type`; без `type` — «пояс» (у записах це паски)."""
    if not р.get("type"):
        return "пояс"
    return _ВМ.ключ("slot", _ВМ.СЛОТ_ТИПУ.get(р["type"])) or "?"


def заяви(сп):
    """Заяви дроту (код або {код: значення}) → `{code, values}` ядра."""
    return [dict(code=з) if isinstance(з, str) else dict(code=next(iter(з)), values=next(iter(з.values())))
            for з in (сп or []) if isinstance(з, (str, dict)) and з]


def ядро(п):
    """Промпт запису → (вердикт ядра, як його бачить `вердикт_повноти`, {номер: річ дроту})."""
    вітрина, описи = K.defaultdict(list), {}
    for р in п.get("showcase") or []:
        вітрина[слот(р)].append(dict(н=р["n"], слот=слот(р))); описи[р["n"]] = р
    образи = []
    for в in п["verdict"]:
        о = в["your_outfit"]
        for р in о["items"]:
            if isinstance(р, dict):
                описи[р["n"]] = р
        образи.append(dict(ід=_ПР.ід_з_дроту(о["id"]), підпис=о.get("caption"), день=о.get("day"),
                           речі=[р["n"] if isinstance(р, dict) else р for р in о["items"]],
                           структура=dict(ок=False, блокери=[dict(ід=_ПР.ід_з_дроту(б["id"]), код=_ВМ.ключ("structural_blocker", б["code"]),
                                                                    речі=list(б.get("items") or []), заяви=заяви(б.get("statements")))
                                                               for б in в["structure"]["blockers"]])))
    return dict(образи=образи, вітрина=dict(вітрина)), описи


def промпт(п, яд):
    """Той самий запис, зібраний чинним оголошенням: діра несе `options` з вітрини запису."""
    позиція = {р["n"]: і for і, р in enumerate(п.get("showcase") or [])}
    вердикт = json.loads(json.dumps(п["verdict"]))
    for в, о in zip(вердикт, яд["образи"]):
        for б, бя in zip(в["structure"]["blockers"], о["структура"]["блокери"]):
            вар = sorted(ПО._варіанти_блокера(бя, яд["вітрина"]), key=lambda н: позиція.get(н, len(позиція)))
            if вар:
                б["options"] = вар
    дані = {к: п[к] for к in ("case", "day", "showcase", "she_refuses") if п.get(к)}
    return json.dumps(_ЗП.зібрати(ПО.ПОВНОТА_ВСІ, dict(дані, verdict=вердикт), мова_тексту="English"),
                      ensure_ascii=False, separators=(",", ":"))


def лишились(о, після, описи):
    """Коди блокерів запису, яких склад `після` не закрив, плюс «слот_двічі», коли додана річ стала в сім'ю слота,
    де річ уже є. Слот — з `type` речі дроту; адреси й мінімуми — із заяв блокера."""
    сл = lambda н: слот(описи.get(н.split("/")[0]) or {"type": "?"})
    до, слоти = set(о["речі"]), [сл(н) for н in після]
    вих = []
    for б in о["структура"]["блокери"]:
        к, зн = б["код"], {з["code"]: з.get("values") or {} for з in б["заяви"]}
        if к == "слот_двічі":
            ok = len([н for н in після if н in б["речі"]]) <= 1
        elif к == "нема_верху_низу":
            ok = bool(set(слоти) & {"сукня", "комплект"}) or all(_ВМ.ключ("slot", x) in слоти
                                                              for x in (зн.get("no_top_bottom_or_dress") or {}).get("missing", []))
        elif к == "неповний":
            ok = len(після) >= зн["too_few_items"]["minimum"] if "too_few_items" in зн else \
                any(с in СУД.СЛОТИ_БЛОКЕРА["неповний"] for с in слоти)
        elif к == "одна_річ":
            ok = len(після) >= 2
        else:
            ok = any(с in СУД.СЛОТИ_БЛОКЕРА.get(к, ()) for с in слоти)
        if not ok:
            вих.append(к)
    сім = K.Counter(СУД._сім_я_слота(с) for с in слоти)
    if any(сім[СУД._сім_я_слота(сл(н))] > 1 for н in після if н not in до) and "слот_двічі" not in вих:
        вих.append("слот_двічі")
    return вих


def модель(текст):
    """Один виклик, як стенд: одне повідомлення, temperature 0, без думання. → (статус, текст, с)."""
    тіло = json.dumps({"model": МОДЕЛЬ, "messages": [{"role": "user", "content": текст}], "max_tokens": МАКС_ТОКЕНІВ,
                       "temperature": 0, "stream": False, "reasoning_effort": "none"}).encode()
    t = time.time()
    try:
        д = json.loads(urllib.request.urlopen(urllib.request.Request(АДРЕСА + "/chat/completions", тіло,
                                                                    {"Content-Type": "application/json"}), timeout=1800).read())
        return 200, ((д.get("choices") or [{}])[0].get("message") or {}).get("content") or "", time.time() - t
    except Exception as е:
        return getattr(е, "code", 599), "", time.time() - t


def розбір(відп, яд):
    """Відповідь → (склад за ід образу після злиття, номери, що не дійшли до складу, «done-n ∉ items», форма)."""
    дп = _ПР.розбір_за_схемою(відп, "ДОПОВНЕННЯ_V1")[0]
    дп = ПО.доповнити(дп, яд) if isinstance(дп, dict) else None
    об = дп[0] if дп else _ПР.розбір_за_схемою(відп, "ОБРАЗИ_V1")[0]
    зл = ПО.злити_з_неторканими(об, яд) if isinstance(об, dict) else None
    склад = {str(о.get("ід")): [str(r) for r in о.get("речі") or []] for о in (зл[0]["образи"] if зл else яд["образи"])}
    було = {о["ід"]: set(о["речі"]) for о in яд["образи"]}
    done = sum(bool(set(НОМЕР.findall(json.dumps([о.get("виконано"), о.get("свідомо")], ensure_ascii=False)))
                    - set(склад.get(str(о.get("ід")), [])) - було.get(str(о.get("ід")), set()))
               for о in ((об or {}).get("образи") or []) if isinstance(о, dict)) if not дп else 0
    return склад, (дп[1]["не_з_вітрини"] if дп else []), done, "ходи" if дп else ("образи" if зл else "нічого")


def main(а):
    живо, кл = "--живо" in а, "--промпти" in а
    теки = [x for x in а if not x.startswith("--")]
    os.makedirs(os.path.join(ВИВІД, "сирі"), exist_ok=True)
    Р = K.Counter()
    for ф, п, відп, шапка in записи(теки):
        яд, описи = ядро(п)
        новий = промпт(п, яд)
        ключ = hashlib.sha1(новий.encode()).hexdigest()[:12]
        if кл:
            os.makedirs(os.path.join(ВИВІД, "промпти"), exist_ok=True)
            open(os.path.join(ВИВІД, "промпти", ключ + ".json"), "w", encoding="utf8").write(новий)
        if живо:
            сира = os.path.join(ВИВІД, "сирі", ключ + ".json")
            if not os.path.exists(сира):
                ст, т, с = модель(новий)
                json.dump(dict(запис=ф, статус=ст, с=round(с, 1), відповідь=т), open(сира, "w", encoding="utf8"), ensure_ascii=False)
            відп = json.load(open(сира, encoding="utf8"))["відповідь"]
        склад, не_дійшли, done, форма = розбір(відп, яд)
        без = [о["ід"] for о in яд["образи"] if not лишились(о, склад.get(о["ід"], о["речі"]), описи)]
        додано = sum(len(set(склад.get(о["ід"], [])) - set(о["речі"])) for о in яд["образи"])
        групи = {о["ід"]: {x for б in о["структура"]["блокери"] for x in б["речі"]} for о in яд["образи"]}
        втратили = sum(bool(set(о["речі"]) - set(склад.get(о["ід"], о["речі"])) - групи[о["ід"]]) for о in яд["образи"])
        print("%-58s промпт %6d→%6d · форма %-6s · з дірою %d → без блокера %d · done-n∉items %d · не дійшли %d · "
              "втратили річ %d · додано речей %d" % ("/".join(ф.split("/")[-3:])[:58], len(json.dumps(п, ensure_ascii=False, separators=(",", ":"))),
                                                      len(новий), форма, len(яд["образи"]), len(без), done, len(не_дійшли), втратили, додано))
        Р.update(записів=1, з_дірою=len(яд["образи"]), без_блокера=len(без), done=done, не_дійшли=len(не_дійшли),
                 втратили=втратили, додано=додано, записів_без_жодного=not без)
    print("РАЗОМ", dict(Р))


if __name__ == "__main__":
    main(sys.argv[1:])
