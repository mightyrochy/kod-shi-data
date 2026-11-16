# -*- coding: utf-8 -*-
"""Прилад кореня Е2-опора-пояснення на малому дереві: місця класу лічить, не місця — ні (без запуску продукту).

На кожен із шести пунктів класу `аудит/корені/Е2-опора-пояснення.md` — щонайменше один випадок «лічиться» і один
«не лічиться». Запуск: `python3 джерела/прилади/тест_корінь_е2_опора_пояснення.py` з кореня репозиторію."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_е2_опора_пояснення as К  # noqa: E402

# ── вхід пояснення: `дріт_моделі.опис` (п.1, п.2) ──
ДРІТ = '''
_ОЗНАКИ = ("cut", "fabric", "material", "length", "sleeve")


def опис(р, сценарій):
    п = {}
    п["metal"] = "gold"
    п["light"] = сценарій["light"]
    п["light_source"] = "scenario"
    рядки = [("kind", р["kind"]), ("type", р["type"])]
    рядки += [("color", кадр_колір(р)), ("hex", кадр_колір(р))]
    ярлик = "colour code: %s" % р["color"]
    for к in _ОЗНАКИ:
        п[к] = р[к]
    п["palette"] = палітра_опису(палітра(сценарій))
    return п, рядки, ярлик


def палітра(сц):
    пал = {}
    пал["farthest"] = сц["найдальші"]
    пал["combinations"] = [x for x in сц["поєднання"]]
    пал["scheme"] = сц["схема"]
    return пал


def палітра_опису(пал):
    return {к: пал[к] for к in ("farthest", "combinations") if пал.get(к)}


def не_з_входу(р):
    return {"kind": р["kind"], "type": р["type"], "color": р["color"]}
'''

# ── заяви (п.3): словник ≥ 20 кодів + виходи в іншому модулі ──
def _словник():
    рядки = []
    for і in range(22):
        рядки.append('    "filler_code_%02d": "a plain note number %d for the report of the look",' % (і, і))
    рядки += [
        '    "sole_grip_unknown_ice": "the card does not say whether the sole grips, and today there is black ice '
        '(values: item — the item)",',
        '    "wet_grip_unknown_rain": "the card does not say whether the sole grips, and today there is rain '
        '(values: item — the item)",',
        '    "possible_wet_note": "the card does not say whether the sole grips, and today there is rain on the road",',
        '    "salt_slush_warmer_wears_faster": "salty slush: what warms better wears out faster",',
        '    "maybe_ice_note_for_her": "the card does not say whether the sole grips, and today there is black ice, '
        'may be",',
        '    "windy_day_without_exit": "the weather is rough, and today it is windy for the whole walk",',
        '    "keep_look_say_why_it_holds_day": "keep the look and say why it holds this day",',
        '    "heavy_snow_by_temperature": "the card does not say whether the sole grips, and today there is heavy snow '
        '(values: item — the item)",',
        '    "heavy_snow_by_her_words": "the card does not say whether the sole grips, and today there is heavy snow '
        '(values: item — the item)",',
        '    "describe_fabric_and_day": "describe the fabric of each item and why it suits her day",',
        '    "describe_when_known": "when the fabric is known, describe the fabric of each item and why it suits her day",',
    ]
    return "ЗАЯВИ = {\n" + "\n".join(рядки) + "\n}\n\n\ndef заява(код, **поля):\n    return {\"код\": код}\n"


ВНУТРІШНЯ = _словник()
СУД = '''
import внутрішня_мова as _ВМ


def морозна(смуга_погоди, речі):
    з = []
    if смуга_погоди in ("мороз", "стужа"):
        з.append(_ВМ.заява("sole_grip_unknown_ice"))
    return з


def дощова(опади, речі):
    з = []
    if опади == "дощ":
        з.append(_ВМ.заява("wet_grip_unknown_rain"))
    return з


def змішана(опади):
    return _ВМ.заява("possible_wet_note" if опади == "можливо" else "wet_grip_unknown_rain")


def сніг_за_температурою(температура):
    if температура < 0:
        return [_ВМ.заява("heavy_snow_by_temperature")]
    return []


def сніг_за_її_словами(її_слова):
    if "сніг" in її_слова:
        return [_ВМ.заява("heavy_snow_by_her_words")]
    return []


def сльота_ранній_вихід(в, сльота):
    if в is None or not сльота:
        return []
    return [_ВМ.заява("salt_slush_warmer_wears_faster")]
'''

# ── промпти (п.4, п.5): англійські літерали Python ──
ПРОМПТ = '''
ВИМОГА_БЕЗ_УМОВИ = "In the last part, say how this outfit lives through her day."
ВИМОГА_З_УМОВОЮ = "When the known item properties support it, say how this outfit lives through her day."
БЕЗ_ВИМОГИ = "The outfit lives through her day in the order of the plan shown on the screen."
ЗАМІНА_КОДОМ = ("The colour of an item is its colour code (colour code: …): write that name of the code. "
                "The code stands in its place whatever the model called from the photo.")
ВИД_ІМЕННИКОМ_КОДУ = "Call every item by the noun of its kind code, whatever word the stylist used."
СЛОВО_СТИЛІСТКИ = "Keep the stylist's own colour word for every item, as she wrote it down."
КОД_БЕЗ_ЗАМІНИ = "Write the colour code as a value of the field and nothing more about the choice."
'''
ПРОБА = '''
ВИМОГА = "In the last part, say how this outfit lives through her day."
'''

# ── JS (п.6) ──
ПОКАЗ = '''
async function модельП(промпт, фото){
  const р = await fetch('/v1/messages', {method: 'POST', body: JSON.stringify({промпт, фото})});
  return р.json();
}
async function без_лічби(фото){
  const т = await модельП('текст', фото);
  return т;
}
async function з_лічбою(фото){
  const т = await модельП('текст', фото);
  const дійшло = ОСТАННІ_ЗАГОЛОВКИ_П['x-images-dropped'];
  return {т, дійшло};
}
async function кадр_у_змінній(к){
  const блоки = [{type: 'image', source: к}, {type: 'text', text: 'опис'}];
  return await модельП(блоки);
}
async function кадр_у_змінній_з_лічбою(к){
  const блоки = [{type: 'image', source: к}];
  const т = await модельП(блоки);
  return {т, дійшло: ОСТАННІ_ЗАГОЛОВКИ_П['x-images-dropped']};
}
async function кадри_ланцюгом(фото, промпт){
  const копії = фото.map(ф => ({type: 'image', data: ф}));
  const запит = блокиЗапиту(промпт, копії);
  return await модельП(запит);
}
async function результат_виміру_не_кадри(фото){
  const вимір = фото ? await виміряти(фото) : null;
  const скільки = фото.length;
  return await модельП(вимір, скільки);
}
async function без_кадрів(){
  return await модельП('текст');
}
'''
# ── мовний_шар._абзац_речей (п.1: статичний ключ), сценарій.день_кодами (п.2: ключі з таблиці) ──
МОВНИЙ_ШАР = '''
def _абзац_речей(р):
    о = {}
    о["color"] = р["колір"]
    if not р.get("колір_не_вимір"):
        о["fabric"] = р["тканина"]
    if р.get("свідчення_крою"):
        о["cut"] = р["крій"]
    return о
'''
СЦЕНАРІЙ = '''
_КОДИ_ДНЯ = (("place", "місце", "place_field"), ("format", "формат", "format_field"))
_КОДИ_З_ДЖЕРЕЛОМ = (("surface", "поверхня"),)


def день_кодами(с):
    д = {}
    for ключ, ім, _ in _КОДИ_ДНЯ:
        д[ключ] = с[ім]
    return д, _з_джерелом(с)


def _з_джерелом(с):
    д = {}
    for ключ, ім in _КОДИ_З_ДЖЕРЕЛОМ:
        д[ключ] = с[ім]
    д["surface_source"] = с["джерело"]
    return д
'''
ВОРКЕР = '''
async function віддати(відповідь, фото){
  відповідь.headers.set('x-images-dropped', String(фото.length));
  return fetch('/v1/messages', {method: 'POST', body: фото});
}
'''


class Прилад(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.тека = tempfile.TemporaryDirectory()
        д = os.path.join(cls.тека.name, "джерела")
        for ім, т in (("дріт_моделі.py", ДРІТ), ("внутрішня_мова.py", ВНУТРІШНЯ), ("суд_погода.py", СУД),
                      ("мовний_шар.py", МОВНИЙ_ШАР), ("сценарій.py", СЦЕНАРІЙ), ("промпт.py", ПРОМПТ), ("проби/проба.py", ПРОБА), ("показ/сторінка.js", ПОКАЗ),
                      ("показ/воркер.js", ВОРКЕР)):
            шлях = os.path.join(д, ім)
            os.makedirs(os.path.dirname(шлях), exist_ok=True)
            with open(шлях, "w", encoding="utf-8") as ф:
                ф.write(т)
        cls.старий = К.КОРІНЬ
        К.КОРІНЬ = cls.тека.name
        К._КЕШ.clear()
        cls.вимір = К.вимір(cls.тека.name)
        cls.місця = {(ф, cls.зміст(ф, р), п) for ф, р, п, _ in cls.вимір["місця"]}
        cls.не_місця = {(ф, cls.зміст(ф, р), п) for ф, р, п, _ in cls.вимір["не_місця"]}
        cls.без_виходу = {(ф, cls.зміст(ф, р), п) for ф, р, п, _ in cls.вимір["без_виходу"]}

    @classmethod
    def tearDownClass(cls):
        К.КОРІНЬ = cls.старий
        К._КЕШ.clear()
        cls.тека.cleanup()

    @classmethod
    def зміст(cls, ф, р):
        """Позначка місця — імʼя сталої/функції чи ключ заяви в рядку: тест не залежить від номерів рядків."""
        with open(os.path.join(cls.тека.name, ф), encoding="utf-8") as фл:
            рядки = фл.read().splitlines()
        лінія = рядки[р - 1]
        for х in sorted({"sole_grip_unknown_ice", "wet_grip_unknown_rain", "possible_wet_note", "salt_slush_warmer_wears_faster",
                         "windy_day_without_exit", "keep_look_say_why_it_holds_day"}, key=len):
            if х in лінія:
                return х
        if "=" in лінія and not лінія.startswith(" "):
            return лінія.split("=")[0].strip()
        for і in range(р - 1, -1, -1):
            for поч in ("def ", "async function ", "function "):
                if рядки[і].startswith(поч):
                    return рядки[і][len(поч):].split("(")[0]
        return лінія.strip()

    # ── п.1 ──
    def test_п1_лічиться_пара_вид_і_тип_цикл_за_перелічком_і_ярлик(self):
        що = [х for ф, _, п, х in self.вимір["місця"] if п == 1 and ф == "джерела/дріт_моделі.py"]
        self.assertEqual(len(що), 4, що)  # kind, color (кадр не виміряє слово крамниці), цикл, ярлик
        self.assertTrue(any("пара ключ-значення «kind»" in х for х in що))
        self.assertTrue(any("цикл за перелічком" in х for х in що))
        self.assertTrue(any("рядок-ярлик" in х for х in що))

    def test_п1_не_лічиться_захищений_кадром_колір_і_функція_поза_входом(self):
        # `hex` на `кадр_колір` — умова певності виміру; `не_з_входу` недосяжна з `опис`
        нс = [що for ф, _, п, що in self.вимір["не_місця"] if "певності" in що and п == 1]
        self.assertTrue(any("«hex»" in що for що in нс), нс)
        self.assertFalse(any("«color»" in що for що in нс), нс)
        рядки_з_входу = [що for ф, _, п, що in self.вимір["місця"] if п == 1 and "не_з_входу" in що]
        self.assertEqual(рядки_з_входу, [])

    # ── п.2 ──
    def test_п2_лічиться_металь_без_джерела(self):
        є = [що for ф, _, п, що in self.вимір["місця"] if п == 2 and ф == "джерела/дріт_моделі.py"]
        self.assertTrue(any("metal" in що for що in є), є)

    def test_п2_не_лічиться_світло_із_сусіднім_ключем_джерела(self):
        нс = [що for ф, _, п, що in self.вимір["не_місця"] if п == 2]
        self.assertTrue(any("light" in що and "light_source" in що for що in нс), нс)
        self.assertFalse(any("light" in що for _, _, п, що in self.вимір["місця"] if п == 2))

    # ── п.3 ──
    def test_п3_лічиться_лід_за_смугою_а_не_за_ожеледицею(self):
        self.assertIn(("джерела/внутрішня_мова.py", "sole_grip_unknown_ice", 3), self.місця)

    def test_п3_не_лічиться_дощ_за_опадами_і_сльота_з_раннім_виходом(self):
        self.assertNotIn(("джерела/внутрішня_мова.py", "wet_grip_unknown_rain", 3), self.місця)
        self.assertIn(("джерела/внутрішня_мова.py", "wet_grip_unknown_rain", 3), self.не_місця)
        self.assertNotIn(("джерела/внутрішня_мова.py", "salt_slush_warmer_wears_faster", 3), self.місця)

    def test_п3_не_лічиться_код_із_умовного_виразу_в_аргументі(self):
        self.assertNotIn(("джерела/внутрішня_мова.py", "possible_wet_note", 3), self.місця)
        self.assertIn(("джерела/внутрішня_мова.py", "possible_wet_note", 3), self.не_місця)

    def test_п3_застереження_й_заява_без_виходу_не_місця(self):
        self.assertNotIn(("джерела/внутрішня_мова.py", "maybe_ice_note_for_her", 3), self.місця)
        self.assertIn(("джерела/внутрішня_мова.py", "windy_day_without_exit", 3), self.без_виходу)
        self.assertNotIn(("джерела/внутрішня_мова.py", "windy_day_without_exit", 3), self.місця)

    # ── п.4 ──
    def test_п4_лічиться_вимога_без_умови(self):
        self.assertIn(("джерела/промпт.py", "ВИМОГА_БЕЗ_УМОВИ", 4), self.місця)

    def test_п4_не_лічиться_умова_відомості_без_вимоги_й_проби(self):
        for х in ("ВИМОГА_З_УМОВОЮ", "БЕЗ_ВИМОГИ"):
            self.assertNotIn(("джерела/промпт.py", х, 4), self.місця, х)
        self.assertIn(("джерела/промпт.py", "ВИМОГА_З_УМОВОЮ", 4), self.не_місця)
        self.assertFalse([ф for ф, _, п, _ in self.вимір["місця"] if "проби" in ф])

    # ── п.5 ──
    def test_п5_лічиться_код_замість_слова_моделі(self):
        self.assertIn(("джерела/промпт.py", "ЗАМІНА_КОДОМ", 5), self.місця)

    def test_п5_не_лічиться_код_без_заміни_слова(self):
        self.assertNotIn(("джерела/промпт.py", "КОД_БЕЗ_ЗАМІНИ", 5), self.місця)

    # ── п.6 ──
    def test_п6_лічиться_виклик_із_кадрами_без_лічби(self):
        self.assertIn(("джерела/показ/сторінка.js", "без_лічби", 6), self.місця)

    def test_п6_не_лічиться_із_лічбою_без_кадрів_і_у_виробника(self):
        self.assertNotIn(("джерела/показ/сторінка.js", "з_лічбою", 6), self.місця)
        self.assertIn(("джерела/показ/сторінка.js", "з_лічбою", 6), self.не_місця)
        self.assertNotIn(("джерела/показ/сторінка.js", "без_кадрів", 6), self.місця)
        self.assertFalse([ф for ф, _, п, _ in self.вимір["місця"] if п == 6 and ф.endswith("воркер.js")])

    # ── виправлені класи (дошка 16058–16060) і власні випадки перевірки 16.11 ──
    @classmethod
    def рядок(cls, ф, фрагмент):
        """Номери рядків файла, де є фрагмент: тест не залежить від того, де в тексті стоїть випадок."""
        with open(os.path.join(cls.тека.name, ф), encoding="utf-8") as фл:
            return [і + 1 for і, л in enumerate(фл.read().splitlines()) if фрагмент in л]

    def лічиться(self, ф, фрагмент, п):
        рр = self.рядок(ф, фрагмент)
        self.assertTrue(рр, фрагмент)
        return all((ф, р, п) in {(а, б, в) for а, б, в, _ in self.вимір["місця"]} for р in рр)

    def test_п1_власний_лічиться_статичний_ключ_запису_речі(self):
        self.assertTrue(self.лічиться("джерела/мовний_шар.py", 'о["color"] = р["колір"]', 1))

    def test_п1_власний_не_лічиться_статичний_ключ_під_умовою_певності_виміру(self):
        self.assertFalse(self.лічиться("джерела/мовний_шар.py", 'о["fabric"] = р["тканина"]', 1))
        self.assertFalse(self.лічиться("джерела/мовний_шар.py", 'о["cut"] = р["крій"]', 1))

    def test_п1_колір_слова_крамниці_не_захищений_кадром_іншого_кольору(self):
        # дошка 16058: `_інший_кадр` мовчить колір лише коли кадр суперечить, а без виміру слово їде як факт
        self.assertTrue(self.лічиться("джерела/дріт_моделі.py", 'рядки += [("color"', 1))

    def test_п2_власний_лічиться_ключ_палітри_який_лишає_фільтр_у_коді(self):
        self.assertTrue(self.лічиться("джерела/дріт_моделі.py", 'пал["farthest"] = сц', 2))
        self.assertTrue(self.лічиться("джерела/дріт_моделі.py", 'пал["combinations"] = ', 2))

    def test_п2_власний_не_лічиться_ключ_палітри_якого_фільтр_не_пускає(self):
        self.assertFalse(self.лічиться("джерела/дріт_моделі.py", 'пал["scheme"] = сц', 2))

    def test_п2_лічиться_ключ_з_таблиці_кодів_у_циклі_і_не_лічиться_з_джерелом_поруч(self):
        рр = self.рядок("джерела/сценарій.py", "д[ключ] = с[ім]")
        місця = {(ф, р) for ф, р, п, _ in self.вимір["місця"] if п == 2}
        self.assertIn(("джерела/сценарій.py", рр[0]), місця)
        self.assertNotIn(("джерела/сценарій.py", рр[1]), місця)  # `surface_source` поруч

    def test_п3_власний_лічиться_сніг_з_силою_за_температурою(self):
        self.assertTrue(self.лічиться("джерела/внутрішня_мова.py", '"heavy_snow_by_temperature"', 3))

    def test_п3_власний_не_лічиться_сніг_за_її_словами(self):
        self.assertFalse(self.лічиться("джерела/внутрішня_мова.py", '"heavy_snow_by_her_words"', 3))

    def test_п4_власний_лічиться_вимога_в_визначенні_заяви_без_умови(self):
        self.assertTrue(self.лічиться("джерела/внутрішня_мова.py", '"describe_fabric_and_day"', 4))
        self.assertTrue(self.лічиться("джерела/внутрішня_мова.py", '"keep_look_say_why_it_holds_day"', 4))

    def test_п4_власний_не_лічиться_визначення_з_умовою_відомості(self):
        self.assertFalse(self.лічиться("джерела/внутрішня_мова.py", '"describe_when_known"', 4))

    def test_п5_власний_лічиться_вид_іменником_коду(self):
        self.assertTrue(self.лічиться("джерела/промпт.py", "ВИД_ІМЕННИКОМ_КОДУ", 5))

    def test_п5_власний_не_лічиться_слово_стилістки(self):
        self.assertFalse(self.лічиться("джерела/промпт.py", "СЛОВО_СТИЛІСТКИ", 5))

    def test_п6_власний_лічиться_кадр_у_змінній_без_фото_в_імені(self):
        self.assertTrue(self.лічиться("джерела/показ/сторінка.js", "return await модельП(блоки);", 6))

    def test_п6_лічиться_кадри_ланцюгом_копії_запит(self):
        self.assertTrue(self.лічиться("джерела/показ/сторінка.js", "return await модельП(запит);", 6))

    def test_п6_власний_не_лічиться_кадр_у_змінній_з_лічбою(self):
        self.assertFalse(self.лічиться("джерела/показ/сторінка.js", "const т = await модельП(блоки);", 6))

    def test_п6_не_лічиться_результат_виміру_й_кількість_кадрів(self):
        self.assertFalse(self.лічиться("джерела/показ/сторінка.js", "return await модельП(вимір, скільки);", 6))

    def test_п3_регулярний_вираз_обставини_бачить_силу_перед_назвою(self):
        for т in ("today there is heavy snow", "today there is a lot of snow", "the day is very windy",
                  "today there is light rain", "today there is thick ice"):
            self.assertTrue(any(р.search(т) for р, _ in К.ОБСТАВИНИ.values()), т)
        self.assertFalse(any(р.search("if the sole does not know the snow") for р, _ in К.ОБСТАВИНИ.values()))

    # ── підсумок ──
    def test_підсумок_за_пунктами_збігається_з_переліком(self):
        за = self.вимір["за_пунктами"]
        self.assertEqual(sum(за.values()), len(self.вимір["місця"]))
        self.assertTrue(all(за[п] >= 1 for п in (1, 2, 3, 4, 5, 6)), за)

    def test_тека_проб_і_приладів_поза_обсягом(self):
        шляхи = {ф for ф, _, _, _ in self.вимір["місця"]}
        self.assertFalse([ф for ф in шляхи if "/проби/" in ф or "/прилади/" in ф])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
