"""Крок 21: вердикт `колір_тон.сім_ї_кольору` і сили на каталозі — база (`git show <ревізія>`) проти дерева, та клас
«≥ 3 значних сімей» (сила ≥ `значна_сила`), який вердикт обтинає до пари. Запуск із кореня (розпакований
`джерела/каталог_повний.xml`): python3 -W ignore аудит/перевірка/річ_колір_межі_крок21/сім_ї_до_після.py <ревізія>"""
import collections, importlib.util, subprocess, sys, tempfile
sys.path.insert(0, "джерела")
import колір_річ as КР, колір_тон as Т, фід_каталог as ФК
т = subprocess.run(["git", "show", f"{sys.argv[1]}:джерела/колір_тон.py"], check=True, capture_output=True).stdout
ф = tempfile.NamedTemporaryFile(suffix=".py", delete=False); ф.write(т); ф.close()
сп = importlib.util.spec_from_file_location("кт_база", ф.name); Д = importlib.util.module_from_spec(сп); сп.loader.exec_module(Д)
З = Т.РЕЄСТР["значна_сила"]["val"]
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
всього = переходів = сил_інших = 0; значних = collections.Counter(); обтято = collections.Counter()
for р in кат:
    lab = КР.точка_кольору(р)
    if lab is None:
        continue
    lab = [float(x) for x in lab]; всього += 1
    переходів += Д.сім_ї_кольору(lab) != Т.сім_ї_кольору(lab)
    сил_інших += Д.сили_сімей(lab) != Т.сили_сімей(lab)
    зн = [к for к, в in Т.сили_сімей(lab).items() if к != Т.НЕВІДОМО and в >= З]
    значних[len(зн)] += 1
    if len(зн) >= 3:
        обтято[зн[2]] += 1
print("речей з виміром:", всього, "| вердикт змінився:", переходів, "| сили змінились:", сил_інших)
print("значних сімей → речей:", dict(sorted(значних.items())))
print("≥ 3 значних — вердикт лишає поза собою (третя сім'я):", dict(обтято.most_common()))
