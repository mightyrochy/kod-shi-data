"""Рядки 3661, 3662, 3380 (наряд МОВА-2): записані ходи розмови ЖИВІ-12/13/14 (VIDPOVIDI гілок живих) — тим самим
кодом `прийняти_розмову` → `паспорт_з_шару`. Друкує кожен хід, де модель дала `hour`, `event` чи `place_words`:
година й пора, що стали в паспорт; вільний текст — сире значення моделі (до) і що взяв шов (після); `place_words`,
яке не дійшло до паспорта, — чи є слід у `не_взято_кодом`, і місце паспорта. Слова тут читає ПРОБА, не код.
Запуск: cd джерела && python3 проби/мова_2_пара_пора.py"""
import json, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
сире = lambda x: x.get("value", x.get("quote")) if isinstance(x, dict) else x
for ж in ("12", "13", "14"):
    г = "origin/claude/zhyvi-%s" % ж
    for ф in git("ls-tree", "-r", "--name-only", г, "../аудит/живі_%s" % ж).split():
        if "хід_розмови" not in ф:
            continue
        с = git("show", "%s:%s" % (г, ф))
        відп = с.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]
        u = (М._обʼєкт(відп)[0] or {}).get("update") if isinstance(М._обʼєкт(відп)[0], dict) else None
        if not isinstance(u, dict) or not {"hour", "event", "place_words"} & set(u):
            continue
        нове = json.loads(с.split("\n", 1)[1].split("── ВІДПОВІДЬ")[0])["her_new_message"]
        р = М.прийняти_розмову(відп)
        ш = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=[нове], частини=р["частини"], не_взято=р.get("не_взято"))
        п, в = ш["паспорт"], р["внутрішня"]
        ряд = ["ж%s %s%s/%s" % (ж, ф.split("/")[-4][:1], ф.split("/")[-3][:2], ф.split("/")[-1][:8])]
        if "hour" in u:
            ряд.append("hour %s → година=%s пора=%s %s" % (сире(u["hour"]), п.get("година"), в.get("part_of_day"),
                                                         [x for x in р["перенесено"] if "hour" in x]))
        for к, ім in (("event", "подія"), ("place_words", "місце_слова")):
            if isinstance(u.get(к), dict):
                слід = [x.split(" · ")[0] for x in п.get("не_взято_кодом") or [] if "field=%s" % к in x]
                ряд.append("%s: %r → %r%s" % (к, сире(u[к]), М._текст(в.get(к)) or None,
                                             "" if п.get(ім) or not слід else " (не взято: %s)" % слід[0])
                           + (" · місце=%s %s" % (п.get("місце"), [x for x in р["перенесено"] if "place" in x])
                              if к == "place_words" else ""))
        if ряд[1:]:
            print(" · ".join(ряд))
