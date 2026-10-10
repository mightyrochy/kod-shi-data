"""Рядки 3931, 3720, 3451 (МОВА-К7): К7 «йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого не хочу».
Записані перші ходи моделі (`claude/zhyvi-12…15`) — тим самим кодом: що записано (occasion, movement, place, −15, сніг)
і чи лишається обовʼязкове «куди» (`occasion`). Далі — сід 5 Ж15 у формі нового правила `update` (той самий уривок —
цитата і `occasion`, і `movement`) і чи стоїть правило в промпті. Кращим: occasion є, обовʼязкового нема, place не
`walk`. Запуск: cd джерела && python3 проби/мова_к7_одна_цитата.py"""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ФРАЗА = "йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого не хочу"
def рядок(підпис, відповідь):
    в = М.прийняти_розмову(відповідь)["внутрішня"]
    о = М.паспорт_з_шару(в, {}, слова_ходу=[ФРАЗА])
    print("  %-34s occasion=%-5s movement=%-5s place=%-5s %s/%s | обовʼязкове: %s" % (підпис, в.get("occasion"),
          в.get("movement"), в.get("place"), в.get("temperature_c"), в.get("precipitation"),
          о["обовʼязкове"] or "—"))
    return відповідь
сід5 = None
for ж in ("12", "13", "14", "15"):
    г = "origin/claude/zhyvi-" + ж
    git("fetch", "-q", "origin", г.split("/", 1)[1])
    print("живі %s:" % ж)
    for ф in sorted(ф for ф in git("ls-tree", "-r", "--name-only", г, "../аудит/живі_%s/А" % ж).split("\n")
                    if re.search(r"/\d\d_ж7_мороз_без_відкритого/VIDPOVIDI/seed\d_01_мовний", ф)):
        т = git("show", "%s:%s" % (г, ф)).split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]
        рядок(ф.split("/")[-3][:2] + " " + ф.split("/")[-1][:5], т)
        if ж == "15" and "seed5" in ф: сід5 = json.loads(re.search(r"\{.*\}", т, re.S).group(0))
у = сід5["update"]
у["occasion"] = {"quote": у["movement"]["quote"], "value": "work"}
print("форма нового правила (Ж15 сід 5, той самий уривок під двома полями):")
рядок("01 seed5 + occasion", json.dumps(сід5, ensure_ascii=False))
п = json.dumps(М.промпт_розмови({"розмова": {"нове": ФРАЗА, "історія": []}}), ensure_ascii=False)
for уривок in ("may be the quote of each of them", "never movement alone", "are never place"):
    print("  у промпті «%s»: %d" % (уривок, п.count(уривок)))
