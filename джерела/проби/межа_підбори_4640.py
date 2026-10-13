# -*- coding: utf-8 -*-
"""Рядок 4640 · межа «підбори» і тип пари: скільки взуття з підбором (за кодом типу чи каблуком) проходить
її на каталозі й на записаних пакетах ЖИВІ-23 №13 (seed3_35) і ЖИВІ-22 №8 (seed3_32), і скільки взуття
лишається під нею (щоб слот не спорожнів). ДО — та сама проба з текою джерел бази.
Запуск: cd джерела && python3 проби/межа_підбори_4640.py [тека джерел] [файл каталогу]"""
import sys, os, re, json, subprocess, collections
Д = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, Д); os.chdir(Д)
import фід_каталог as ФК, каблук as КБ, profile as PR, внутрішня_мова as ВМ
КАТ = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ТУТ, "каталог_повний.xml")
ПІДБОР, СУМНІВ = ("pumps", "heeled_sandals"), ("dress_shoes", "mules")   # підбор у визначенні коду / неоднозначні
def клас(тип, є, см=0):
    if є is False: return None
    if є is True or см > 0: return "heel:yes"
    return ("type:" if тип in ПІДБОР else "unknown:") + тип if тип in ПІДБОР + СУМНІВ else None
def звіт(де, речі):
    лиш = [(р, т) for р, т in речі if not PR.сенсорний_збіг("підбори", р)]
    к = collections.Counter(клас(т, р.get("_є"), float(р.get("каблук_см") or 0)) for р, т in лиш)
    к.pop(None, None)
    print("ФАКТ · %s: взуття %d · під межею «підбори» лишається %d · з них з підбором %d (%s)"
          % (де, len(речі), len(лиш), sum(в for к_, в in к.items() if not к_.startswith("unknown")),
             ", ".join("%s %d" % кв for кв in sorted(к.items())) or "—"))
кат = [р for р in ФК._база_прогону(КАТ, ліміт_фото=0)["каталог"] if р.get("слот") == "взуття"]
for р in кат:
    р["каблук_є"] = КБ.каблук(р.get("назва"), None, р.get("url"))["є"]
    р["_є"] = True if True in (р.get("каблук"), р["каблук_є"]) else (False if False in (р.get("каблук"), р["каблук_є"]) else None)
звіт("каталог %s" % os.path.basename(КАТ), [(р, ВМ.код("item_type", р.get("тип"))) for р in кат])
СЛОВО = ВМ.ТАБЛИЦЯ["item_type"]
for гілка, тека, сід in (("claude/zhyvi-23", "аудит/живі_23/А/13_ж2_спорт_коментар", "seed3_35"),
                         ("claude/zhyvi-22", "аудит/живі_22/А/08_ж2_спорт_коментар", "seed3_32")):
    git = lambda *а: subprocess.run(("git", "-C", os.path.dirname(ТУТ)) + а, capture_output=True, text=True).stdout
    шлях = next((ш for ш in git("ls-tree", "-r", "--name-only", "origin/" + гілка, "--", тека + "/VIDPOVIDI/").split("\n")
                 if "/" + сід in ш), None)
    текст = git("show", "origin/%s:%s" % (гілка, шлях)) if шлях else ""
    речі = [json.loads(x) for x in re.findall(r'\{[^{}]*"heel":"[a-z]+"[^{}]*\}', текст)]
    звіт("пакет %s %s" % (гілка[7:], сід), [(dict(слот="взуття", тип=СЛОВО.get(р.get("type")),
                                                   каблук_є={"none": False, "yes": True}.get(р["heel"]),
                                                   _є={"none": False, "yes": True}.get(р["heel"])), р.get("type"))
                                              for р in речі])
