"""Рядок 3457: опис ЖИВІ-13 №8 (−15 °C, робота). Рука 1 — відповіді опису 22 (перший виклик) і 24 (повтор, обгортка
{"answer":…, "input":…}): чи є текст і записи `about_items` на речі образу. Рука 2 — 32: чи промпт каже рід «Пасок
Базовий блакитний» кодом (`kind`) — без нього опис ішов за кадром (блуза). На базі — ДО, на гілці — ПІСЛЯ."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import розбір_відповідей as РВ, фід_слот as ФС
тека = "origin/claude/zhyvi-13:аудит/живі_13/А/08_ж7_мороз_без_відкритого/VIDPOVIDI/seed3_%s.txt"


def запис(ім):
    try:
        с = subprocess.run(["git", "show", тека % ім], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        sys.exit("нема гілки ЖИВІ-13 (git fetch origin claude/zhyvi-13): %s" % e)
    п, в = с.split("── ВІДПОВІДЬ", 1)
    т = п[п.index("{"):]
    return json.JSONDecoder(strict=False).raw_decode(т)[0]["outfit"]["items"], в.split("\n", 1)[1]


for рука, ім in ((1, "22_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1"), (1, "24_інший_промпт"), (2, "32_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1")):
    речі, відп = запис(ім)
    за_ном = {int(re.match(r"#(\d+)·", r["n"]).group(1)): ("р" + r["n"], r["n"].split("·")[1]) for r in речі}
    РВ._словник_речей = lambda *a, **k: {"р" + r["n"]: dict(id="р" + r["n"], назва=r["name"]) for r in речі}
    РВ._за_номером = lambda *a, **k: за_ном
    р = РВ.опис_відповідь_з_json(відп, склад=["р" + r["n"] for r in речі])
    print("рука %d %s: текст %s · about_items %d з %d · без запису %s · обгортку знято %s" % (
        рука, ім[:2], "є" if р["текст"] else "None", len(р.get("про_речі") or []), len(речі),
        р.get("не_описано") or "—", "так" if "answer_envelope_unwrapped" in р["нормалізовано"] else "ні"))
пояс = next(r for r in речі if r["name"].startswith("Пасок"))
промпт = РВ.опис_v1([dict(н=r["n"], назва=r["name"], слот=ФС.слот({"name": r["name"], "назва": r["name"]}), магазин=r.get("shop"),
                          фото_номери=r.get("photos")) for r in речі], образ="о4")
рядок = next(json.dumps(x, ensure_ascii=False) for x in промпт["outfit"]["items"]
             if x["n"] == пояс["n"])
print("рука 2, промпт: %s · правило «item of its «kind»» %s" % (рядок, "є" if "item of its «kind»" in json.dumps(промпт, ensure_ascii=False) else "нема"))
print("   запис моделі ДО: %s" % next(x["text"] for x in json.loads(відп)["answer"]["about_items"] if x["n"] == пояс["n"]))
