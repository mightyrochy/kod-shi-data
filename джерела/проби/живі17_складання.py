"""ОЦІНКА-Ж17 (#844, рядки 4024–4026): записані відповіді складання й ремонту ЖИВІ-16/17 №11–13 тим кодом, що в теці
аргументу (типово `.`): образів у тексті (`"pole"` — лічить ПРОБА) проти прочитаних `протокол.розбір_за_схемою`, ехо
промпту; на пакет руки 1–2 Ж17 — речей пулу без `type` (без роду) і пояси з кроєм сукні. Кращим: прочитано стільки,
скільки написано. Запуск: cd джерела && python3 проби/живі17_складання.py [тека джерел іншої збірки]"""
import json, re, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import протокол as П
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for ж in ("16", "17"):
    Г = "origin/claude/zhyvi-%s" % ж
    git("fetch", "-q", "origin", "claude/zhyvi-%s" % ж)
    ф_ = [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
          if re.search(r"/1[123]_.*VIDPOVIDI/.*(ОБРАЗИ_V1|повтор_формату)", ф)]
    ехо = менше = 0
    for ф in ф_:
        т = git("show", "%s:%s" % (Г, ф)); запит, відп = т.split("── ВІДПОВІДЬ", 1)[0], т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
        написано = max(len(re.findall(r'"pole"\s*:', відп)), len(re.findall(r'"(?:caption|підпис)"\s*:', відп)))
        об = П.розбір_за_схемою(відп, "ОБРАЗИ_V1")[0]
        прочитано = len((об or {}).get("образи") or []) if isinstance(об, dict) else 0
        є_ехо = bool(re.search(r'"(answer_schema|statement_codes)"', відп)); ехо += є_ехо; менше += прочитано < написано
        if є_ехо or прочитано < написано:
            print("Ж%s %s/%s: написано %d · прочитано %d%s" % (ж, ф.split("/")[-3][:2], ф.split("/")[-1][:8], написано,
                  прочитано, " · ЕХО промпту, %d симв." % len(відп) if є_ехо else ""))
        if "ПАКЕТ_V1" in ф and ж == "17":
            пул = json.JSONDecoder().raw_decode(запит[запит.find("{"):])[0].get("pool") or []
            без = [р for р in пул if "type" not in р]
            пояс = [р["name"][:24] + " cut=" + р["cut"] for р in пул if re.match(r"(Пасок|Ремінь|Пояс)", р.get("name", "")) and р.get("cut") not in (None, "belted")]
            print("   пул %s/%s: речей %d · без type (і без роду) %d, напр. %s · пояси з кроєм %d %s" % (ф.split("/")[-3][:2],
                  ф.split("/")[-1][:8], len(пул), len(без), [р["name"][:18] for р in без[:3]], len(пояс), пояс[:2]))
    print("Ж%s: відповідей складання/ремонту %d · прочитано менше, ніж написано, %d · з ехом промпту %d" % (ж, len(ф_), менше, ехо))
