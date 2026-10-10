"""ОЦІНКА-Ж18 (#849, рядки 4024, 4025, 4040): записані відповіді складання й ремонту ЖИВІ-17/18 №11–13 тим кодом, що
в теці аргументу (типово `.`): образів у тексті (`"pole"`, `"caption"`, `"items"` — лічить ПРОБА) проти прочитаних `протокол.розбір_за_схемою`,
ехо промпту (`answer_schema`, `statement_codes` у відповіді), довжина. Кращим: прочитано стільки, скільки написано, ехо 0.
Запуск: cd джерела && python3 проби/живі18_складання.py [тека джерел іншої збірки]"""
import re, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import протокол as П
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for ж in ("17", "18"):
    Г = "origin/claude/zhyvi-%s" % ж
    git("fetch", "-q", "origin", "claude/zhyvi-%s" % ж)
    ф_ = [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
          if re.search(r"/1[123]_.*VIDPOVIDI/.*(ОБРАЗИ_V1|повтор_формату)", ф)]
    ехо = менше = напис = проч = 0
    for ф in ф_:
        т = git("show", "%s:%s" % (Г, ф)); відп = т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
        написано = max(len(re.findall(r'"pole"\s*:', відп)), len(re.findall(r'"(?:caption|підпис)"\s*:', відп)),
                       len(re.findall(r'"(?:items|речі)"\s*:\s*\[', відп)))
        об = П.розбір_за_схемою(відп, "ОБРАЗИ_V1")[0]
        прочитано = len((об or {}).get("образи") or []) if isinstance(об, dict) else 0
        є_ехо = bool(re.search(r'"(answer_schema|statement_codes)"', відп)); ехо += є_ехо; менше += прочитано < написано
        напис += написано; проч += прочитано
        print("Ж%s %s/%s: написано %d · прочитано %d · %d симв.%s" % (ж, ф.split("/")[-3][:2], ф.split("/")[-1][:24],
              написано, прочитано, len(відп), " · ЕХО" if є_ехо else ""))
    print("Ж%s: відповідей %d · образів написано %d, прочитано %d · недочитаних відповідей %d · з ехом %d" % (
        ж, len(ф_), напис, проч, менше, ехо))
