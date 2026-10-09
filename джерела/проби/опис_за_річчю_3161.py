"""Рядок 3161(б): покриття «Чому цей образ» код звіряє номерами — запис `about_items` на кожну річ образу.
Збережені відповіді опису живого 12 А/08 (картки 3 і 4, −15 °C): ДО код бачив лише «named», ПІСЛЯ — чи має кожна річ
свій запис; третій рядок — та сама відповідь у новій формі, де пальто пропущено."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import розбір_відповідей as РВ
тека = "origin/claude/zhyvi-12:аудит/живі_12/А/08_ж7_мороз_без_відкритого/VIDPOVIDI/seed3_%d_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1.txt"
for картка, n in ((3, 26), (4, 27)):
    try:
        сире = subprocess.run(["git", "show", тека % n], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        sys.exit("нема гілки живих 12 (git fetch origin claude/zhyvi-12): %s" % e)
    промпт = json.loads(next(l for l in сире.split("\n") if l.startswith("{")))
    речі = промпт["outfit"]["items"] if "outfit" in промпт else промпт["task"]["outfit"]["items"]
    за_ном = {int(re.match(r"#(\d+)·", r["n"]).group(1)): ("р" + r["n"], r["n"].split("·")[1]) for r in речі}
    РВ._словник_речей = lambda *a, **k: {"р" + r["n"]: dict(id="р" + r["n"], назва=r["name"]) for r in речі}
    РВ._за_номером = lambda *a, **k: за_ном
    склад = ["р" + r["n"] for r in речі]
    відп = сире.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
    до = РВ.опис_відповідь_з_json(відп, склад=склад)
    об = json.loads(відп)["answer"]
    print("картка %d, речей %d · ДО: «named» %d номерів, поза образом %d, повтор %s · ПІСЛЯ: без запису %d — %s" % (
        картка, len(склад), len(об.get("named") or []), len(до.get("названо_поза_образом") or []),
        "так" if до.get("названо_поза_образом") else "ні", len(до.get("не_описано") or []), json.loads(до["повторний_виклик"])["error"] if до.get("повторний_виклик") else "без повтору"))
    нова = dict(об, about_items=[dict(n=x["n"], text=x["what"]) for x in об["named"] if "coat" not in x["what"]])
    п = РВ.опис_відповідь_з_json(json.dumps(dict(answer=нова)), склад=склад)
    print("   нова форма без пальта: записів %d, без запису %s, повтор: %s; рядків картки перед «text» %d" % (
        len(п["про_речі"]), п.get("не_описано"), json.loads(п["повторний_виклик"])["error"] if п.get("повторний_виклик") else "—",
        len(п["текст"].split("\n")) - len(об["text"].split("\n"))))
