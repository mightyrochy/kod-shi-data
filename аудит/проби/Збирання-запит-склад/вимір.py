"""Наряд `Збирання-запит-склад`, крок 1: з чого складаються запити складання («Build outfits») і ремонту («Improve the
outfits»), і що з цього модель може вжити. Читає записані обміни сторінки з моделлю, нових викликів не робить.

Запуск із кореня репозиторію:  python3 аудит/проби/Збирання-запит-склад/вимір.py [тека обмінів …]
Типово — 16 проходів `аудит/проби/Живий-через-міст/` (міст, Sonnet 5.5, справжні `usage`) і 4 проходи
`аудит/проби/живий-як-людина-4/` (`claude -p`: лише знаки — `usage` там від Claude Code, а не від запиту сторінки).
Токени частини — оцінка: знаки частини × (токени входу виклику / знаки виклику); токенів по частинах API не дає."""
import glob, gzip, json, re, sys, collections, statistics as st

ТИПОВО = sorted(glob.glob("аудит/проби/Живий-через-міст/стенд/службове/с*/обміни.jsonl")) + \
    sorted(glob.glob("аудит/проби/живий-як-людина-4/стенд/службове/с*/обміни.jsonl.gz"))
НЕ_СУДИТЬ = re.compile(r"the code does not (judge|know)")   # визначення заяви в statement_codes
ТИПОВІ_МЕТА = {"recipient": "woman", "source": "unknown", "choice": "unknown", "rank": None, "item_ids": []}


def зн(о):
    return len(json.dumps(о, ensure_ascii=False, separators=(",", ":")))


def рядки(ф):
    with (gzip.open(ф, "rt") if ф.endswith(".gz") else open(ф)) as в:
        for р in в:
            yield json.loads(р)


def тіло(д):
    з = json.loads(д["запит"])
    т = "".join(б.get("text", "") for б in з["messages"][0]["content"] if б.get("type") == "text")
    try:
        return т, json.loads(т)
    except ValueError:
        return т, None


def відповідь(д):
    try:
        в = json.loads(д.get("відповідь") or "")
    except ValueError:
        return None, {}
    текст = "".join(б.get("text", "") for б in в.get("content") or [] if б.get("type") == "text")
    try:
        return json.loads(текст), в.get("usage") or {}
    except ValueError:
        return None, в.get("usage") or {}


def вид(т):
    р = ((т or {}).get("task") or {}).get("role", "") if isinstance((т or {}).get("task"), dict) else ""
    for к, с in (("складання", "Build outfits"), ("ремонт", "Improve the outfits"), ("вибір", "Choose one")):
        if с in р:
            return к
    return None


def обійти(о, ф):
    if isinstance(о, dict):
        ф(о)
        for v in о.values():
            обійти(v, ф)
    elif isinstance(о, list):
        for v in о:
            обійти(v, ф)


def заяви_в(о):
    вих = []
    обійти(о, lambda д: вих.append(д) if isinstance(д.get("code"), str) and "values" in д else None)
    return вих


def main(файли):
    В = collections.defaultdict(list)       # вид → записи
    for ф in файли:
        міст = "Живий-через-міст" in ф          # стенд за підпискою (`claude -p`): лише знаки й секунди
        ситуація = ф.split("/")[-2]
        for д in рядки(ф):
            if д.get("статус") != 200:
                continue
            текст, т = тіло(д)
            к = вид(т)
            if not к:
                continue
            відп, u = відповідь(д)
            вх = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            з = dict(ситуація=ситуація, прохід=д.get("прохід"), міст=міст, знаків=len(текст), т=т, відп=відп,
                     вх=вх if міст else None, кеш=u.get("cache_read_input_tokens") if міст else None,
                     вих=u.get("output_tokens") if міст else None,
                     думки=((u.get("output_tokens_details") or {}).get("thinking_tokens")) if міст else None,
                     с=д.get("с"), час=д.get("час"))
            В[к].append(з)
    for к in ("складання", "ремонт", "вибір"):
        зз = В[к]
        if not зз:
            continue
        мм = [з for з in зз if з["міст"]]
        т_на_зн = sum(з["вх"] for з in мм) / max(1, sum(з["знаків"] for з in мм))
        print(f"\n## {к}: викликів {len(зз)} (міст {len(мм)}), знаків середнє {st.mean(з['знаків'] for з in зз):,.0f}"
              f" (макс {max(з['знаків'] for з in зз):,}), токенів входу (міст) середнє {st.mean(з['вх'] for з in мм) if мм else 0:,.0f},"
              f" секунд середнє {st.mean(з['с'] or 0 for з in зз):.1f}"
              f"; токенів на знак {т_на_зн:.3f}")
        частини = collections.defaultdict(list)
        for з in зз:
            for ключ, v in з["т"].items():
                if ключ == "task":
                    for к2, v2 in v.items():
                        частини["task." + к2].append(зн(v2))
                elif ключ == "verdict" and isinstance(v, list):
                    підч = collections.Counter()
                    for о in v:
                        for к2, v2 in о.items():
                            підч[к2] += зн(v2)
                    for к2, n in підч.items():
                        частини["verdict[]." + к2].append(n)
                else:
                    частини[ключ].append(зн(v))
        сер = st.mean(з["знаків"] for з in зз)
        print("| частина | знаків, середнє | частка | токенів, оцінка |\n|---|---|---|---|")
        for ключ, сп in sorted(частини.items(), key=lambda x: -sum(x[1]) / len(зз)):
            с = sum(сп) / len(зз)
            if с / сер >= 0.004:
                print(f"| `{ключ}` | {с:,.0f} | {100 * с / сер:.1f} % | {с * т_на_зн:,.0f} |")
        # (а) пункти перевірки без входу: «not_run» образів і `not_run_everywhere`
        if к == "ремонт":
            нр_зн, клітинок_нр, клітинок_пров, образів = [], 0, 0, 0
            for з in зз:
                т = з["т"]
                n = зн(т.get("not_run_everywhere") or {})
                скрізь = sum(len(x) for x in (т.get("not_run_everywhere") or {}).values())
                for о in т.get("verdict") or []:
                    образів += 1
                    ч = о.get("checklist") or {}
                    n += sum(зн(б.get("not_run") or []) for б in ч.values())
                    клітинок_нр += скрізь + sum(len(б.get("not_run") or []) for б in ч.values())
                    клітинок_пров += sum(len(б.get("failed") or []) for б in ч.values())
                нр_зн.append(n)
            print(f"\n(а) «не запущено» у вході ремонту: {st.mean(нр_зн):,.0f} знаків на виклик; клітинок «пункт × образ»"
                  f" названо не запущеними {клітинок_нр} і проваленими {клітинок_пров} на {образів} образах —"
                  f" {клітинок_нр / max(1, образів):.1f} не запущених на образ; частка від 61 пункту × образ:"
                  f" {100 * клітинок_нр / max(1, 61 * образів):.0f} %")
        # (б) заяви «код не судить» і (є) типові поля заяв
        if к in ("ремонт", "вибір"):
            нс, мета, ключі, усього, фікс_дубль = [], [], [], [], []
            for з in зз:
                т = з["т"]
                коди = {к2 for к2, опис in ((т.get("task") or {}).get("statement_codes") or {}).items()
                        if isinstance(опис, str) and НЕ_СУДИТЬ.search(опис)}
                зв = заяви_в(т.get("verdict")) + заяви_в(т.get("set")) + заяви_в(т.get("remarks_by_code"))
                нс.append(sum(зн(x) for x in зв if x["code"] in коди))
                мета.append(sum(len(json.dumps({к2: x[к2]}, ensure_ascii=False, separators=(",", ":"))) - 1
                                for x in зв for к2, v in ТИПОВІ_МЕТА.items() if к2 in x and x[к2] == v))
                ключі.append(sum(len(json.dumps({"key": x["key"]}, separators=(",", ":"))) - 1 for x in зв if "key" in x))
                усього.append(len(зв))
                фд = 0
                обійти(т.get("verdict"), lambda д: None)
                for о in т.get("verdict") or []:
                    for f in о.get("findings") or []:
                        if f.get("fix") and f.get("fix") == f.get("statements"):
                            фд += зн(f["fix"]) + 7
                фікс_дубль.append(фд)
            print(f"\n{к}: заяв на виклик {st.mean(усього):.0f}; (б) заяви «код не судить / не знає» — {st.mean(нс):,.0f} знаків;"
                  f" типові поля заяв (recipient=woman, source/choice=unknown, rank=null, item_ids=[]) — {st.mean(мета):,.0f};"
                  f" `key` заяви — {st.mean(ключі):,.0f}; `fix`, що дослівно повторює `statements`, — {st.mean(фікс_дубль):,.0f}"
                  f" знаків на виклик (середнє знаків виклику {сер:,.0f})")
        if к == "складання":
            # (в) пул: рядків і скільки з них у відповіді; (г) про жінку зі статусом withheld
            рядків, взято, витр, нев = [], [], [], []
            for з in зз:
                т = з["т"]
                пул = (т.get("pool") or {}).get("rows") or []
                рядків.append(len(пул))
                ном = {р[0] for р in пул}
                обр = (з["відп"] or {}).get("outfits") or []
                взяті = {x for о in обр for x in (о.get("items") or []) if isinstance(x, str) and x.split("/")[0] in ном}
                взяті = {x.split("/")[0] for x in взяті}
                взято.append(len(взяті))
                кол = ((т.get("person") or {}).get("colouring") or {})
                нев.append(sum(зн(v) + len(к2) + 4 for к2, v in кол.items() if isinstance(v, dict) and v.get("status") == "withheld"))
                витр.append(sum(1 for v in кол.values() if isinstance(v, dict) and v.get("status") == "withheld"))
            print(f"\n(в) пул: рядків {st.mean(рядків):.0f} (від {min(рядків)} до {max(рядків)}), різних речей у відповіді"
                  f" {st.mean(взято):.0f} ({100 * sum(взято) / sum(рядків):.0f} % пулу)")
            print(f"(г) `person.colouring` зі статусом withheld: {sum(1 for x in витр if x)} з {len(витр)} запитів,"
                  f" {st.mean(нев):,.0f} знаків на виклик")
            # (ґ) вихід
            образів = [len((з["відп"] or {}).get("outfits") or []) for з in зз]
            print(f"(ґ) образів у відповіді: {collections.Counter(образів)}; просили `outfits_wanted`: "
                  f"{collections.Counter(з['т'].get('outfits_wanted') for з in зз)}")
        if мм:
            print(f"(ґ/д) міст: вихід токенів середнє {st.mean(з['вих'] for з in мм):,.0f} (з них думок"
                  f" {st.mean(з['думки'] or 0 for з in мм):,.0f}), секунд середнє {st.mean(з['с'] for з in мм):.1f}"
                  f" (макс {max(з['с'] for з in мм):.0f}); з кешу прочитано {sum(з['кеш'] for з in мм):,} з"
                  f" {sum(з['вх'] for з in мм):,} токенів входу ({100 * sum(з['кеш'] for з in мм) / sum(з['вх'] for з in мм):.1f} %)")
        if к == "ремонт":
            лишено = [len((з["відп"] or {}).get("outfits") or []) for з in зз]
            print(f"(ґ) ремонт отримав образів {collections.Counter(len(з['т'].get('verdict') or []) for з in зз)},"
                  f" лишив {collections.Counter(лишено)}; вибір бере один на картку")
    # (д) однакове між двома складаннями й двома ремонтами одного проходу
    print("\n(д) однакові частини двох викликів одного проходу: частка знаків, що збігається дослівно")
    for к in ("складання", "ремонт"):
        групи = collections.defaultdict(list)
        for з in В[к]:
            групи[(з["ситуація"], з["прохід"])].append(з)
        сп, однак = collections.Counter(), []
        for г in групи.values():
            if len(г) != 2:
                continue
            а, б = г[0]["т"], г[1]["т"]
            сп_зн = 0
            for ключ in а:
                if ключ == "task":
                    for к2 in а["task"]:
                        if а["task"][к2] == (б.get("task") or {}).get(к2):
                            сп["task." + к2] += 1
                            сп_зн += зн(а["task"][к2])
                elif а[ключ] == б.get(ключ):
                    сп[ключ] += 1
                    сп_зн += зн(а[ключ])
            однак.append(сп_зн / г[0]["знаків"])
        if not однак:
            continue
        print(f"{к}: пар {len(однак)}; однакового {100 * st.mean(однак):.0f} % знаків; частини, однакові в усіх парах: "
              + ", ".join(f"`{x}`" for x, n in sorted(сп.items()) if n == len(однак)))


if __name__ == "__main__":
    main(sys.argv[1:] or ТИПОВО)
