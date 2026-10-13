# -*- coding: utf-8 -*-
"""Проба поділу жнива_v2 ОФЛАЙН: функції, яким не треба ні моделі, ні мережі, дають ПОБАЙТОВО той самий вихід до поділу
(жнива_v2.py@БАЗА, exec з git) і після (фасад) — на записах чинного `каталог_збагачення.json.gz` (v2) і оферах каталогу. Знімок БАЗИ читає СЬОГОДНІШНІЙ verify, тому дістає той самий словник виміру й перелік слів для моделі, що й фасад: рівно свідома
зміна рядка 137 (a1e99b5 — сім слів поля кольору крамниць дістали вікна в ЛЕКСИКОНІ, але точку не підписують і моделі не
пропонуються; у реєстрі `жнива_колір::слово_з_lab`, `жнива_реєстр::КОЛЬОРИ`). Решта — побайтово; rc 1 — є різниця. Запуск: cd джерела && python3 проби/поділ_жнива_офлайн.py [БАЗА] [каталог.xml]"""
import argparse, contextlib, gzip, io, json, os, subprocess, sys, tempfile, types
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ)
import feed as F, colorspace as CS, verify as V, жнива_v2 as Н
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "95b0102"
С = types.ModuleType("жнива_v2_старий"); С.__file__ = os.path.join(ТУТ, "жнива_v2.py")
exec(compile(subprocess.run(["git", "show", "%s:джерела/жнива_v2.py" % БАЗА], cwd=ТУТ, capture_output=True, check=True).stdout.decode("utf-8"), "жнива_v2.py", "exec"), С.__dict__)
С.V = types.ModuleType("verify_виміру"); С.КОЛЬОРИ = [с for с in С.КОЛЬОРИ if с not in V.ВІКНА_КРАМНИЦЬ]  # рядок 137
С.V.__dict__.update(V.__dict__, ЛЕКСИКОН={с: в for с, в in V.ЛЕКСИКОН.items() if с not in V.ВІКНА_КРАМНИЦЬ})
зб = dict(F.читати_збагачення(ТУТ)); v2 = [зб[к] for к in sorted(зб) if (зб[к].get("версія") or 1) >= 2][:300]
with open(sys.argv[2] if len(sys.argv) > 2 else Н.КАТАЛОГ, "rb") as f: offers = F.читати_yml(f)[0][:3000]
кл = lambda з: [dict(слово=k["слово"], частка=k["частка"], lab=list(CS.hx(k["hex"])), hex=k["hex"], у_вікні=True) for k in (з.get("колір_основний"), з.get("колір_другий")) if k]
з_кольором = [з for з in v2 if з.get("колір_основний")]
сирі = [(dict(з, колір_слово=з["колір_основний"]["слово"], деталі=["комір", "x"]), "одяг" if з.get("крій") else "дрібне") for з in з_кольором] + [({"колір_слово": "чорний", "каблук": {"є": True, "форма": "тонкий"}, "носок": "гострий", "блиск": 2}, "взуття"), ({"тип": "тоут", "ручки": "обидва"}, "сумка"), ({"метал": "золотистий", "масштаб": "велика"}, "прикраса")]
def зведення(м, з):
    о, д, с = м.звести_колір(кл(з), з["колір_основний"]["слово"], ["сірий", "білий"])
    return о, д, с, м.впевненість(0.4, о, с, ["сірий"], 3.0)
def злиття(м, тека):
    а = argparse.Namespace(вихід=os.path.join(тека, "v2.json"), злити_у=os.path.join(тека, "з.gz"))
    json.dump({("ж-%d" % i): dict(запис=з) for i, з in enumerate(v2[:50])}, open(а.вихід, "w", encoding="utf-8"))
    with contextlib.redirect_stdout(io.StringIO()) as вих: м.злити(а)
    return gzip.open(а.злити_у).read().decode("utf-8"), [р for р in вих.getvalue().splitlines() if "КБ" not in р]
ПАРИ = [("нормалізувати", lambda м: [м.нормалізувати(с, н) for с, н in сирі]),
        ("звести_колір+впевненість", lambda м: [зведення(м, з) for з in з_кольором]),
        ("слово_з_lab+_тінь", lambda м: [(м.слово_з_lab(к["lab"]), м._тінь(к["lab"], [к["lab"][0] - 5] + к["lab"][1:])) for з in v2 for к in кл(з)]),
        ("збільшити_url", lambda м: [м.збільшити_url(u) for o in offers for u in (o.get("фото") or o.get("фото_сирі") or [])]),
        ("тип_речі+набір+промпт", lambda м: [(т, м.набір_слота(т[1]), м._підставити(м.ПРОМПТ_НАБОРУ[м.набір_слота(т[1])], т[0])) for т in map(м.тип_речі, offers[:400])]),
        ("вибірка+_url_крамниць", lambda м: ([o["id"] for o in м.вибірка(offers)], [dict(x) for x in м._url_крамниць(offers)[0].values()], м._url_крамниць(offers)[1])),
        ("позначити_одну", lambda м: м.позначити_одну([dict(хеш="a", розмір=[50, 50], мала=True), dict(хеш="b", розмір=[900, 300], майже_біла=True), dict(помилка="x"), dict(хеш="c", розмір=[800, 1200])], lambda ф: {"a": 1, "b": 3, "c": 1}[ф["хеш"]])),
        ("записати_атомарно", lambda м: (lambda т: (м.записати_атомарно({"б": v2[:20], "а": 1}, т + "/з.json"), open(т + "/з.json", "rb").read().decode("utf-8")))(tempfile.mkdtemp())),
        ("злити", lambda м: злиття(м, tempfile.mkdtemp()))]
різних = 0
for ім, ф in ПАРИ:
    a, b = (json.dumps(ф(м), ensure_ascii=False, sort_keys=True, default=str) for м in (С, Н))
    різних += a != b; print("%-26s %7d байт  %s" % (ім, len(a), "ті самі" if a == b else "РІЗНІ"))
sys.exit(1 if різних else 0)
