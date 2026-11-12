# -*- coding: utf-8 -*-
"""Тест приладу `корінь_річ_фото_питання.py`: штучні дерева «місце» й «не місце» для кожного правила класів (а) і (б)
та приклади паспорта `аудит/корені/Річ-фото-питання.md` (п.1–5, 7) на справжньому дереві — місця.

Штучне дерево — тимчасова тека з `джерела/*.py` (і `джерела/показ/*.js`); прилад розбирає файли, а не імпортує, тож
модулі дерева з модулями репозиторію не змішуються. Запуск: python3 джерела/прилади/тест_корінь_річ_фото_питання.py
"""
import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_річ_фото_питання as П  # noqa: E402
import обсяг_приладу as _ОБ  # noqa: E402

ВХІД = (("м", "вхід"),)

# суддя речі з усім, що потрібне класу (б): опис ознак, запис речі, суддя образу
СУДДЯ = '''
import json
_ПОЛЯ_ФОТО = (("slot", "слот"), ("cut", "крій"), ("length", "довжина"))

def заява(код):
    return код

def зн(x):
    return x

def _повідомлення(заяви):
    return заяви

def запис_каталогу(річ):
    з = {}
    з["cut"] = річ.get("крій")
    з["len"] = річ.get("довжина")
    return з

def образ(з):
    return зн(з.get("cut")) + зн(з.get("len"))

def вердикт(річ):
    без_входу, заяви = [], []
    крій = річ.get("крій")
    чому = річ.get("чому_не_закріплена") if річ.get("закріплена") is False else None
    if not крій:
        без_входу.append("крій: не названо")
        заяви.append(заява("cut_not_named"))
%s
    return _повідомлення(заяви)

def вхід(в):
    d = json.loads(в)
    річ = d.get("річ") or {}
%s
    return вердикт(річ)
'''


def дерево(файли):
    """Тимчасове дерево: {шлях від `джерела/`: текст} → корінь."""
    тека = tempfile.mkdtemp(prefix="річ_фото_")
    for ш, т in файли.items():
        повний = os.path.join(тека, "джерела", ш)
        os.makedirs(os.path.dirname(повний), exist_ok=True)
        with open(повний, "w", encoding="utf-8") as ф:
            ф.write(textwrap.dedent(т))
    return тека


def правила(файли, входи=ВХІД):
    місця, _ = П.лічба(дерево(файли), входи)
    return [м.правило for м in місця]


def суддя(тіло_судді="", тіло_входу=""):
    відступ = lambda т: textwrap.indent(textwrap.dedent(т).strip("\n"), "    ") if т.strip() else ""
    return {"м.py": СУДДЯ % (відступ(тіло_судді), відступ(тіло_входу))}


def вхід(тіло):
    return {"м.py": "import json\nimport statistics\nВІДОМІ = ('фото', 'опис')\n\ndef вхід(в):\n    d = json.loads(в)\n"
            + textwrap.indent(textwrap.dedent(тіло).strip("\n"), "    ") + "\n"}


class КласА(unittest.TestCase):
    def test_а1_місце(self):
        self.assertIn("а1", правила(вхід('return d["очі"]')))

    def test_а1_не_місце_під_сторожем(self):
        self.assertNotIn("а1", правила(вхід('if d.get("очі"):\n    return d["очі"]\nreturn None')))

    def test_а1_не_місце_протокол(self):
        self.assertNotIn("а1", правила(вхід('п = d.get("пікселі") or {}\nreturn п["дані"]')))

    def test_а2_місце(self):
        self.assertIn("а2", правила(вхід('return statistics.median([x for x in d.get("тони") or []])')))

    def test_а2_не_місце_не_порожній(self):
        self.assertNotIn("а2", правила(вхід('сп = d.get("тони") or [0]\nreturn statistics.median(сп)')))

    def test_а3_місце(self):
        р = правила(вхід('if d.get("зріст") in (None, ""):\n    raise ValueError("нема зросту")\nreturn 1'))
        self.assertIn("а3", р)

    def test_а3_не_місце_невідоме_значення_протоколу(self):
        р = правила(вхід('if d.get("джерело") not in ВІДОМІ:\n    raise ValueError("невідоме джерело")\nreturn 1'))
        self.assertNotIn("а3", р)

    def _промпт(self, правило):
        return {"м.py": "import json\nОГ = Оголошення(задача='x', правила=(%r,))\n\ndef Оголошення(**к):\n    return к\n\n"
                        "def вхід(в):\n    return json.dumps(ОГ)\n" % правило}

    def test_а4_місце(self):
        self.assertIn("а4", правила(self._промпт("If the face is under a quarter of the frame, give only the reason.")))

    def test_а4_не_місце(self):
        self.assertNotIn("а4", правила(self._промпт("If the eye ring is not visible, put null for the ring.")))

    def _показ(self, споживач):
        return dict(вхід("return 1"), **{"показ/п.js": textwrap.dedent('''\
            async function оцінитиП(р) {
              const в = await містП('річ_з_фото', р);
              if (!в) р.збої.push('річ_з_фото: нема відповіді');
              return р;
            }
            function відповістиП(р) {
              оцінитиП(р);
            %s
            }
            ''') % споживач})

    def test_а5_місце(self):
        self.assertIn("а5", правила(self._показ("  if (р.збої.length) return 'Не вдалося оцінити річ';")))

    def test_а5_не_місце_з_причиною(self):
        self.assertNotIn("а5", правила(self._показ("  if (р.збої.length) return повідомленнямП(р.збої);")))

    def test_а6_місце(self):
        тіло = 'інші = d.get("речі") or []\nif len(інші) > 1:\n    річ["чому_не_закріплена"] = "пізніша річ на цьому місці"'
        self.assertIn("а6", правила(суддя(тіло_входу=тіло)))

    def test_а6_не_місце_поле_суду(self):
        тіло = 'if річ.get("слот") == "низ":\n    річ["чому_не_закріплена"] = "низ"'
        self.assertNotIn("а6", правила(суддя('if річ.get("слот"):\n    заяви.append(заява("slot"))', тіло)))

    def test_а6_не_місце_її_рука(self):
        тіло = 'if річ.get("рука") == "окремо":\n    річ["чому_не_закріплена"] = "ти сказала окремо"'
        self.assertNotIn("а6", правила(суддя(тіло_входу=тіло)))


class КласБ(unittest.TestCase):
    def test_б1_місце(self):
        тіло = 'if крій and річ.get("слот") == "верх":\n    без_входу.append("крій: верх сам контуру не дає")'
        self.assertIn("б1", правила(суддя(тіло)))

    def test_б1_не_місце_заява_в_блоці(self):
        тіло = 'if not крій:\n    без_входу.append("крій: не названо")\n    заяви.append(заява("cut_not_named"))'
        self.assertNotIn("б1", правила(суддя(тіло)))

    def test_б1_не_місце_заява_під_тією_самою_умовою(self):
        тіло = ('if not крій:\n    без_входу.append("крій: не названо")\n'
                'if not крій:\n    заяви.append(заява("cut_not_named"))')
        self.assertNotIn("б1", правила(суддя(тіло)))

    def test_б2_місце_довжина(self):
        р = [м for м in П.лічба(дерево(суддя()), ВХІД)[0] if м.правило == "б2"]
        self.assertEqual([("довжина" in м.чому) for м in р], [True])

    def test_б2_не_місце_суддя_читає(self):
        р = [м for м in П.лічба(дерево(суддя('if річ.get("довжина"):\n    заяви.append(заява("len"))')), ВХІД)[0]
             if м.правило == "б2"]
        self.assertEqual(р, [])

    def _промпт(self, правило):
        return {"м.py": "import json\nОГ = Оголошення(задача='x', правила=(%r,))\n\ndef Оголошення(**к):\n    return к\n\n"
                        "def вхід(в):\n    return json.dumps(ОГ)\n" % правило}

    def test_б3_місце(self):
        self.assertIn("б3", правила(self._промпт("Two to four sentences.")))

    def test_б3_не_місце(self):
        self.assertNotIn("б3", правила(self._промпт("Answer in the language of her question.")))


class Паспорт(unittest.TestCase):
    """Приклади паспорта на справжньому дереві: (файл, рядок, правило) — місця."""

    @classmethod
    def setUpClass(cls):
        місця, cls.довжина = П.лічба()
        cls.місця = {(м.файл, м.рядок, м.правило) for м in місця}
        cls.всі = місця

    def є(self, файл, рядок, правило):
        self.assertIn(("джерела/" + файл, рядок, правило), self.місця)

    def test_п1_палітри_нема_зовсім(self):
        self.є("міст_вхід.py", 511, "а4")

    def test_п2_медіана_порожнього(self):
        self.є("міст_вхід.py", 62, "а2")

    def test_п3_зріст_і_обхвати(self):
        self.є("міст_вхід.py", 147, "а3")
        self.є("міст_вхід.py", 150, "а1")
        self.є("areas.py", 292, "а3")

    def test_п4_крій_і_довжина(self):
        self.assertTrue(any(ф == "джерела/річ_з_фото.py" and 1722 <= р <= 1741 and п == "б1" for ф, р, п in self.місця))
        self.assertTrue(any(м.правило == "б2" and "довжина" in м.чому for м in self.всі))

    def test_п5_пізніша_річ(self):
        self.є("річ_з_фото.py", 797, "а6")

    def test_п7_два_чотири_речення(self):
        self.є("міст_стилістка.py", 82, "б3")


def tearDownModule():
    _ОБ.скинути()


if __name__ == "__main__":
    unittest.main()
