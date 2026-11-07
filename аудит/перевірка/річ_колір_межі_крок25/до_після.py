"""Крок 25: `palettes` бази (`git show <ревізія>`) проти дерева на каталозі — підпис кольору `назва` (ближній тон
`_тон_поруч`), метал кольору `метал_речі` / `метал_меж` (вікна золота й срібла), `несе_колір` (свідок-слово), сім'я
тону `сім_я_тону` і палітри `палітра_практична` на наборі людей. Запуск із кореня (розпакований
`джерела/каталог_повний.xml`):
python3 -W ignore аудит/перевірка/річ_колір_межі_крок25/до_після.py <ревізія> > …/до_після.txt"""
import collections, importlib.util, json, random, subprocess, sys, tempfile
sys.path.insert(0, "джерела")
import palettes as П, колір_річ as КР, фід_каталог as ФК, verify as V, colorspace as cs  # noqa: E402
from колір_простір_перетворення import lch, hex_з_lab  # noqa: E402
т = subprocess.run(["git", "show", f"{sys.argv[1]}:джерела/palettes.py"], check=True, capture_output=True).stdout
ф = tempfile.NamedTemporaryFile(suffix=".py", delete=False); ф.write(т); ф.close()
сп = importlib.util.spec_from_file_location("pal_база", ф.name); Д = importlib.util.module_from_spec(сп); сп.loader.exec_module(Д)
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
речі = [р for р in кат if КР.межі_кольору(р) is not None]
виміри = [р for р in речі if КР.не_вимір(р) is None]
слово = lambda р: V.назва_кольору(str(р.get("колір_назва") or "")) or "—"
print(f"записів: {len(кат)}; з кольором: {len(речі)}; з виміром: {len(виміри)}")

# 1. Підпис кольору `назва` на точках виміру
пер, пр, збіг = collections.Counter(), collections.defaultdict(list), [0, 0]
for р in виміри:
    lab = tuple(float(x) for x in КР.точка_кольору(р))
    а, б = Д.назва(lab)[0], П.назва(lab)[0]
    с = слово(р)
    збіг[0] += а == с; збіг[1] += б == с
    if а != б:
        к = f"{а} → {б}"; пер[к] += 1
        if len(пр[к]) < 3:
            L, C, h = lch(lab); пр[к].append(f"{hex_з_lab(lab)} L{L:.0f} C{C:.0f} h{h:.0f} «{с}»")
print(f"\n1. назва (точки виміру): змінилось {sum(пер.values())} з {len(виміри)}; збіг зі словом крамниці {збіг[0]} → {збіг[1]}")
for к, n in пер.most_common(25):
    print(f"  {к}: {n} — {'; '.join(пр[к])}")
# ґратка основ ЛАБ-точок: вузли L 5–95 крок 5, C 0–80 крок 4, h крок 5
сітка = [cs.lab_з_lch(L, C, h) if hasattr(cs, "lab_з_lch") else П.lab_з_lch(L, C, h)
         for L in range(5, 100, 5) for C in range(0, 84, 4) for h in range(0, 360, 5)]
рс = collections.Counter(f"{Д.назва(x)[0]} → {П.назва(x)[0]}" for x in сітка if Д.назва(x)[0] != П.назва(x)[0])
print(f"   сітка LCh ({len(сітка)} вузлів): змінилось {sum(рс.values())} — {рс.most_common(12)}")

# 2. Метал кольору
for ім in ("ЗОЛОТО", "СРІБЛО", "РОЖЕВЕ_ЗОЛОТО"):
    print(f"\n2. {ім}: {getattr(Д, ім)} → {getattr(П, ім)}")
мп, мпр = collections.Counter(), collections.defaultdict(list)
юв = collections.Counter()
for р in виміри:
    lab = tuple(float(x) for x in КР.точка_кольору(р))
    а, б = Д.метал_речі(lab), П.метал_речі(lab)
    if а != б:
        к = f"{а} → {б}"; мп[к] += 1
        if len(мпр[к]) < 3:
            L, C, h = lch(lab); мпр[к].append(f"{hex_з_lab(lab)} L{L:.0f} C{C:.0f} h{h:.0f} {р.get('слот')} «{слово(р)}»")
    сл, тп = р.get("слот"), р.get("тип")
    if П.слот_металу(сл, тп):
        а, б = Д.метал_речі(lab, сл, тп), П.метал_речі(lab, сл, тп)
        юв[(а, б)] += 1
print(f"   метал_речі без слота (колір, точки виміру): змінилось {sum(мп.values())} з {len(виміри)}")
for к, n in мп.most_common():
    print(f"  {к}: {n} — {'; '.join(мпр[к])}")
print(f"   метал_речі зі слотом фурнітури ({sum(юв.values())} речей): " +
      "; ".join(f"{а} → {б}: {n}" for (а, б), n in sorted(юв.items(), key=lambda x: -x[1]) if а != б) + f"; без змін {sum(n for (а, б), n in юв.items() if а == б)}")
вв = collections.Counter()
for с, в in V.ЛЕКСИКОН.items():
    x = dict(колір_назва=с, колір_не_вимір=dict(свідок="слово крамниці", слово=с, вікно=в))
    а, б = Д.метал_меж(x), П.метал_меж(x)
    if а != б:
        вв[f"{с}: {а} → {б}"] += 1
print(f"   метал_меж вікон лексикону ({len(V.ЛЕКСИКОН)}): змінилось {sum(вв.values())} — {sorted(вв)}")
мм, ммп = collections.Counter(), collections.defaultdict(list)
for р in речі:
    а, б = Д.метал_меж(р, р.get("слот"), р.get("тип")), П.метал_меж(р, р.get("слот"), р.get("тип"))
    if а != б:
        к = f"{а} → {б}"; мм[к] += 1
        if len(ммп[к]) < 3:
            ммп[к].append(f"{р.get('id')} {р.get('слот')} «{р.get('колір_назва')}» {str(р.get('назва'))[:40]}")
print(f"   метал_меж записів каталогу з кольором, зі слотом ({len(речі)}): змінилось {sum(мм.values())}")
for к, n in мм.most_common():
    print(f"  {к}: {n} — {'; '.join(ммп[к])}")

# 3. Чи річ несе колір
нк, нпр = collections.Counter(), collections.defaultdict(list)
for р in кат:
    а, б = Д.несе_колір(р), П.несе_колір(р)
    if а != б:
        к = f"{а} → {б}"; нк[к] += 1
        if len(нпр[к]) < 4:
            т_ = КР.точка_кольору(р)
            нпр[к].append(f"{р.get('id')} {hex_з_lab(т_) if т_ else '—'} {р.get('слот')} «{(р.get('колір_назва') or '').strip()}»")
print(f"\n3. несе_колір (усі {len(кат)} записів): змінилось {sum(нк.values())}")
for к, n in нк.most_common():
    print(f"  {к}: {n} — {'; '.join(нпр[к])}")

# 4. Сім'я тону палітри — та сама таблиця (крок її не міняє)
print(f"\n4. сім_я_тону на 3600 кутах (крок 0.1°): змінилось {sum(Д.сім_я_тону(h / 10) != П.сім_я_тону(h / 10) for h in range(3600))}")

# 5. Палітри: 300 людей з випадкових шкіри, волосся й очей каталогу ознак
rnd = random.Random(25)
шк = ["#f3d9c6", "#e8c1a0", "#d9a77f", "#c08a63", "#9a6646", "#6e4630", "#f1d3c2", "#e2b597", "#b9805b", "#5a3825"]
вол = ["#2a1f1a", "#4b3428", "#6d4c35", "#a07850", "#d2b48c", "#e6cf9a", "#8a3b1f", "#b5562b", "#9a9a9a", "#0f0f10"]
очі = ["#4a2f1f", "#6b4a2b", "#7fa6c8", "#3d6e9e", "#5f8a5a", "#7b8b6a", "#8a9aa8", "#2e2a28", "#6a7f9a", "#9b8a5a"]
змін, приклади = collections.Counter(), []
for і in range(300):
    F = cs.features(cs.hx(rnd.choice(шк)), cs.hx(rnd.choice(вол)), cs.hx(rnd.choice(очі)))
    а = json.dumps(Д.палітра_практична(F), ensure_ascii=False, sort_keys=True, default=str)
    б = json.dumps(П.палітра_практична(F), ensure_ascii=False, sort_keys=True, default=str)
    змін[а == б] += 1
    if а != б and len(приклади) < 3:
        ра, рб = json.loads(а), json.loads(б)
        приклади.append([к for к in ра if ра.get(к) != рб.get(к)])
print(f"\n5. палітра_практична на 300 людях: без змін {змін[True]}, змінилось {змін[False]}" +
      (f"; ключі змін: {приклади}" if приклади else ""))
