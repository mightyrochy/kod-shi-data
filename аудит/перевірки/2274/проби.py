"""Відтворює прицільні проби PR #2274 без виконання коду продукту."""
import importlib.util
import pathlib
import random
import sys
import tempfile

корінь = pathlib.Path(sys.argv[1]).resolve()
спец = importlib.util.spec_from_file_location(
    "прилад", корінь / "джерела/прилади/корінь_річ_колір_вимір.py")
прилад = importlib.util.module_from_spec(спец)
спец.loader.exec_module(прилад)

приклади = {
    "п.5 імпорт модуля з псевдонімом": "import surface as S\ndef колір(rgb):\n return S.виміряти(rgb, 1, 1, [])\n",
    "п.5 імпорт функції з псевдонімом": "from surface import виміряти as f\ndef колір(rgb):\n return f(rgb, 1, 1, [])\n",
    "п.1 запис лише з розкидом": "def колір(rgb):\n return dict(lab=rgb, розкид=2, колір_тип='вимір')\n",
    "п.1 читач лише з розкидом": "def колір(x):\n return x.get('файл'), x.get('розкид'), x.get('lab')\n",
    "п.1 читач лише з придатністю": "def колір(x):\n return x.get('файл'), x.get('придатний'), x.get('lab')\n",
    "п.2 читач із розкидом і придатністю": "def колір(x):\n return x.get('файл'), x.get('розкид'), x.get('придатний'), x.get('lab')\n",
    "п.3 значення or": "def колір(x):\n слот=x.get('слот')\n return x.get('hex') or '#000000'\n",
    "п.5 докстрінг і imwrite": "import surface as S\ndef колір(rgb):\n \"\"\"маніфест\"\"\"\n imwrite('фото', rgb)\n return S.виміряти(rgb, 1, 1, [])\n",
    "п.1 повернення точки кортежем": "def колір(rgb):\n домінанта={'lab': rgb}\n return домінанта['lab'], 0.5\n",
}
with tempfile.TemporaryDirectory() as тека:
    файл = pathlib.Path(тека) / "приклад.py"
    for назва, код in приклади.items():
        файл.write_text(код, encoding="utf-8")
        дерево, батьки = прилад.розібрати(файл)
        місця = прилад.шлях_А(файл.name, дерево, батьки) + прилад.шлях_Б(файл.name, дерево, батьки)
        print(назва + ": " + str(sorted({м.пункт for м in місця})))
    файл_js = pathlib.Path(тека) / "приклад.js"
    for ім in ("р", "x", "s"):
        файл_js.write_text(f"const hex = {ім}.hex || null;\n", encoding="utf-8")
        print(f"п.3 JS приймач {ім}: " + str([м.пункт for м in прилад.шлях_Б_js([файл_js])]))

місця, без_місць = {}, []
for файл in sorted((корінь / "джерела").glob("*.py")):
    if прилад.ВИКЛЮЧЕНО.match(файл.name):
        continue
    дерево, батьки = прилад.розібрати(файл)
    знахідки = прилад.шлях_А(файл.name, дерево, батьки) + прилад.шлях_Б(файл.name, дерево, батьки)
    for м in знахідки:
        місця[(м.файл, м.рядок, м.пункт)] = м
    if not знахідки:
        без_місць.append(файл)
for файл in sorted((корінь / "джерела/показ").glob("*.js")):
    знахідки = прилад.шлях_Б_js([файл])
    for м in знахідки:
        місця[(м.файл, м.рядок, м.пункт)] = м
    if not знахідки:
        без_місць.append(файл)
впорядковані = sorted(місця.values(), key=lambda м: (м.пункт, м.файл, м.рядок))
print("Вибірка 20 місць; сід 73:")
for м in random.Random(73).sample(впорядковані, 20):
    print(f"{м.файл}:{м.рядок} · п.{м.пункт}")
print("Вибірка 20 файлів без місць; сід 73:")
for файл in random.Random(73).sample(без_місць, 20):
    print(файл.relative_to(корінь / "джерела").as_posix())
for ім in ("мовний_шар.js", "збирання_руки.js"):
    знайдені = [м.рядок for м in прилад.шлях_Б_js([корінь / "джерела/показ" / ім])]
    print(f"JS {ім}: {знайдені}")
