"""СКЛАДАННЯ-СТЕЛЯ-33: записані виклики складання (`ПАКЕТ_V1 → ОБРАЗИ_V1`) ЖИВІ-19/20/21 і живі-4281 — скільки відповідей
дописали за образами дані промпту (ехо: «input», «pool», «answer_schema»…), скільки з них уперлось у стелю (не закрита й
≥10 тис. симв. — 4000 т.), скільки символів ехо; і промпт тих самих даних поточним кодом зі скелетом у «task» (ДО) та
останнім (ПІСЛЯ): довжина, сталий початок, що стоїть за схемою. Запуск: cd джерела && python3 проби/складання_стеля_33.py"""
import dataclasses, json, re, subprocess, sys
sys.path.insert(0, "."); import збирач_промптів as ЗП, пакет_моделі as ПМ
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ЕХО = re.compile(r'"(input|pool|pool_keys|case|person|answer_schema|statement_codes|style_rules|poles|kind_notes|'
                 r'outfits_wanted|name|price)"\s*:')
ПІСЛЯ = ПМ._задача_руки(ПМ.СКЛАДАННЯ); ДО = dataclasses.replace(ПІСЛЯ, скелет_наприкінці=False)
Д = lambda о: json.dumps(о, ensure_ascii=False, separators=(",", ":"))
def промпт(о, дані, мова):
    п = ЗП.зібрати(о, дані, мова_тексту=мова); т = Д(п)
    кінець = json.JSONDecoder().raw_decode(т, т.index("{", т.index('"answer_schema":')))[1]
    return len(т), len(Д(п["task"])), т[кінець:кінець + 10]
for ж in ("19", "20", "21", "4281"):
    Г = "origin/claude/zhyvi-" + ж
    ф_ = [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
          if re.search(r"VIDPOVIDI/.*ПАКЕТ_V1_ОБРАЗИ_V1", ф)]
    ехо = стель = симв = 0; сек = [0, 0]; пр = None
    for ф in ф_:
        т = git("show", "%s:%s" % (Г, ф)); п, в = т.split("── ВІДПОВІДЬ", 1); в = в.split("\n", 1)[1].strip()
        try: json.loads(в.strip("`\n")); закрита = True
        except ValueError: закрита = False
        м = ЕХО.search(в); ехо += bool(м); симв += len(в) - м.start() if м else 0
        с = float(re.search(r"([\d.]+) с,", т.split("── ВІДПОВІДЬ", 1)[1]).group(1)); сек[0] += с; сек[1] += с if м else 0
        стель += not закрита and len(в) >= 10000
        if м: print("  Ж%s %s/%s: %d симв., ехо з %d-го: %s" % (ж, ф.split("/")[-3][:2], ф.split("/")[-1][:8], len(в),
                    м.start(), ",".join(sorted(set(ЕХО.findall(в))))))
        пр = пр or json.loads(п.split("\n")[1])
    дані = {к: з for к, з in пр.items() if к not in ("version", "task")}; мова = пр["task"].get("language")
    (дд, сд, зд), (дп, сп, зп) = промпт(ДО, дані, мова), промпт(ПІСЛЯ, дані, мова)
    print("Ж%s: складань %d (%.0f с) · з ехо %d (%d симв. ехо, %.0f с) · у стелю %d · промпт ДО %d → ПІСЛЯ %d симв., «task» %d → %d, "
          "за схемою ДО %r → ПІСЛЯ %r" % (ж, len(ф_), сек[0], ехо, симв, сек[1], стель, дд, дп, сд, сп, зд, зп))
