"""Крок 22: `колір_тон` бази (`git show <ревізія>`) проти дерева на каталозі — вердикт ДО → ПІСЛЯ з переходами,
найсильніша сім'я, стик (≥ 3 значних), пари одного слова (так — сім'ї двох речей перетинаються), 40 свотчів
`мірило.json` кроку 05.11. Запуск із кореня (розпакований `джерела/каталог_повний.xml`):
python3 -W ignore аудит/перевірка/річ_колір_межі_крок22/до_після.py <ревізія> > …/до_після.txt"""
import collections, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "джерела")
import колір_річ as КР, колір_тон as Т, фід_каталог as ФК  # noqa: E402
from колір_простір_перетворення import hex_з_lab  # noqa: E402
т = subprocess.run(["git", "show", f"{sys.argv[1]}:джерела/колір_тон.py"], check=True, capture_output=True).stdout
ф = tempfile.NamedTemporaryFile(suffix=".py", delete=False); ф.write(т); ф.close()
сп = importlib.util.spec_from_file_location("кт_база", ф.name); Д = importlib.util.module_from_spec(сп); сп.loader.exec_module(Д)
ім = lambda в: "+".join(к for к, _ in в)
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
всього = 0; переходи, перша, стик, приклади = collections.Counter(), [collections.Counter(), collections.Counter()], [0, 0], collections.defaultdict(list)
за_словом = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
for р in кат:
    lab = КР.точка_кольору(р)
    if lab is None:
        continue
    lab = [float(x) for x in lab]; всього += 1
    в = (Д.сім_ї_кольору(lab), Т.сім_ї_кольору(lab))
    слово = (р.get("колір_назва") or "").strip().lower()
    for і in (0, 1):
        перша[і][в[і][0][0]] += 1; стик[і] += len(в[і]) >= 3
        if слово:
            за_словом[і][слово][frozenset(к for к, _ in в[і])] += 1
    if в[0] != в[1]:
        к = (ім(в[0]), ім(в[1])) if [x for x, _ in в[0]] != [x for x, _ in в[1]] else ("(сили)", "(сили)")
        переходи[к] += 1
        if len(приклади[к]) < 3:
            приклади[к].append(f"{р.get('id')} {hex_з_lab(lab)} «{слово}»")


def пари(групи):
    так = ні = 0
    for набори in групи.values():
        с = list(набори.items())
        for і, (а, nа) in enumerate(с):
            так += nа * (nа - 1) // 2
            for б, nб in с[і + 1:]:
                if а & б:
                    так += nа * nб
                else:
                    ні += nа * nб
    return так, ні


print(f"речей з виміром: {всього}; решітка {Д._РЕШІТКА_СІМЕЙ['sha256'][:8]} → {Т._РЕШІТКА_СІМЕЙ['sha256'][:8]}")
print(f"вердикт змінився: {sum(переходи.values())}; на стику (≥ 3): {стик[0]} → {стик[1]}")
for к, n in переходи.most_common():
    print(f"  {к[0]} → {к[1]}: {n} — {'; '.join(приклади[к])}")
print("найсильніша ДО → ПІСЛЯ:", {к: f"{перша[0][к]}→{перша[1][к]}" for к in sorted(set(перша[0]) | set(перша[1])) if перша[0][к] != перша[1][к]})
print("пари одного слова так / ні: %d / %d → %d / %d" % (*пари(за_словом[0]), *пари(за_словом[1])))
св = json.loads(Path("аудит/перевірка/річ_колір_межі_сім_ї_20261105/мірило.json").read_text(encoding="utf-8"))["свотчі"]
for і, с in enumerate(св, 1):
    д, п = Д.сім_ї_кольору(с["lab"]), Т.сім_ї_кольору(с["lab"])
    if д != п:
        print(f"свотч №{і} {с['hex']} «{с['слово']}»: " + " · ".join(f"{к} {s:.2f}" for к, s in д) + " → " + " · ".join(f"{к} {s:.2f}" for к, s in п))
