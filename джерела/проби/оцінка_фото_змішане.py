"""ОЦІНКА-ЧИТАННЯ-ФОТО-2 (рядок 4210): скільки викликів «ОЦІНКА: речі на фото» живих прогонів Ж15…Ж19 мають змішаний `photo`
(частина речей з `photo`, частина без). Береться кожен запис `…VIDPOVIDI/*ОЦІНКА_речі_на_фото*` з гілок `claude/zhyvi-N`
(Ж19 — що вже запушено); друкує по виклику: речей усього · без `photo` · прочитано · незнайомі «фото ... не було».
Запуск: cd джерела && python3 проби/оцінка_фото_змішане.py [тека джерел іншої збірки] [фото: 2]"""
import json, re, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import оцінка_образу as О
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ФОТО = [{"ід": "ф%d" % (і + 1)} for і in range(int(sys.argv[2]) if len(sys.argv) > 2 else 2)]
усього = змішаних = 0
for N in ("15", "16", "17", "18", "19"):
    Г = "origin/claude/zhyvi-" + N
    git("fetch", "-q", "origin", "claude/zhyvi-" + N)
    файли = [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_" + N).split("\n") if re.search(r"VIDPOVIDI/.*ОЦІНКА_речі_на_фото", ф)]
    зм = 0
    for ф in файли:
        т = git("show", "%s:%s" % (Г, ф))
        відп = т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1] if "── ВІДПОВІДЬ" in т else т
        об, _, _ = О._ПР.розбір_останній(відп, ("items",))
        it = [о for о in (об or {}).get("items", []) if isinstance(о, dict)] if isinstance(об, dict) and isinstance(об.get("items"), list) else []
        без = sum(not str(о.get("photo") or "").strip() for о in it)
        змішане = 0 < без < len(it)
        в = О.речі_з_відповіді(відп, ФОТО)
        зм += змішане
        print("Ж%s %s: речей %d · без photo %d%s · прочитано %d · причина %s" % (N, ф.split("/")[-1][:12], len(it), без, " ЗМІШАНО" if змішане else "", len(в["речі"]), в["причина"]))
    усього += len(файли); змішаних += зм
    print("Ж%s: викликів %d · змішаних %d" % (N, len(файли), зм))
print("РАЗОМ Ж15…Ж19: викликів %d · зі змішаним photo %d" % (усього, змішаних))
