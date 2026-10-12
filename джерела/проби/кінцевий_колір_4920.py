"""4920: повні читачі на одному каталозі; ДО — main 286b310, також звірка замороженої голови 2801c674."""
import contextlib, io, json, os, subprocess, sys, tempfile, types
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import фід_варіант as FV, фід_кадр_колір as FC, фід_каталог as FK, дріт_моделі as D
from фід_збагачення import читати_збагачення, _збагачення_придатне
from фід_розбір import читати_yml
from фід_фото import _спільні_фото, чужий_кадр
імена = ("фід_варіант", "фід_кадр_колір", "фід_каталог")
чинні = {ім: sys.modules[ім] for ім in імена}
шлях, зб = FK.каталог_на_диску(), читати_збагачення()
offers, _ = читати_yml(шлях); спільні = _спільні_фото(offers)
def прогін(ша=None):
    """Прогнати обидва повні читачі зазначеної голови на незмінних даних."""
    for ім in імена:
        if ша:
            m = types.ModuleType(ім); m.__file__ = чинні[ім].__file__; sys.modules[ім] = m
            exec(subprocess.run(["git", "show", ша + ":джерела/" + ім + ".py"], capture_output=True, text=True, check=True).stdout, m.__dict__)
        else: sys.modules[ім] = чинні[ім]
    каталог, кадр = sys.modules[імена[2]], sys.modules[імена[1]]
    with tempfile.TemporaryDirectory() as т, contextlib.redirect_stdout(io.StringIO()):
        речі = {r["id"]: r for r in каталог._прочитати_каталог(шлях, 0, кеш=os.path.join(т, "кеш.json"), збагачення=зб)["каталог"]}
    к = кадр.контекст(offers, зб, спільні)
    рішення = {o["id"]: кадр.рішення(o, e if _збагачення_придатне(e := зб.get(o["id"])) and not чужий_кадр(e.get("фото"), спільні.get(o.get("магазин")) or {}) else None, к) for o in offers}
    return речі, рішення
до, кдо = прогін("286b310328eb3f981e403ae9b4ddcabd667b2f97")
старі, _ = прогін("2801c67443dedadf0510186054fb509c35383d72")
після, кпісля = прогін()
код = lambda r: D.колір_код((r or {}).get("колір_назва"))[0]
зміни = [i for i in sorted(до.keys() & після.keys()) if код(до[i]) != код(після[i])]
print("ФАКТ · ДО %d; заморожена голова %d; ПІСЛЯ %d; старих змін %d; нових змін %d; додано %d; знято %d" % (len(до), len(старі), len(після), sum(код(до[i]) != код(r) for i, r in старі.items() if i in до), len(зміни), len(після.keys()-до.keys()), len(до.keys()-після.keys())))
for i in sorted(set(зміни) | set(sys.argv[1:])):
    a, b = до.get(i, {}), після.get(i, {})
    print("РІЧ · " + json.dumps(dict(id=i, зміна=i in зміни, до=a.get("колір_назва"), після=b.get("колір_назва"), заморожене=старі.get(i, {}).get("колір_назва"), код_до=код(a), код_після=код(b), lab=b.get("lab"), фото_виміру=(зб.get(i) or {}).get("фото"), фото_картки=кпісля.get(i, {}).get("кадр") or next(iter(b.get("фото") or []), None), варіант=b.get("колір_варіант"), контроль=b.get("колір_перелік_сирий"), спір_до=кдо.get(i, {}).get("спір"), спір_після=кпісля.get(i, {}).get("спір"), кадр_до=кдо.get(i, {}).get("кадр"), кадр_після=кпісля.get(i, {}).get("кадр")), ensure_ascii=False))
