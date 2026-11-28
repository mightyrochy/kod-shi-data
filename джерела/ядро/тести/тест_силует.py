"""Факти силуету на межі пояснення картки."""
import json
from types import SimpleNamespace
import unittest

from межа_текстів import Межа
from ядро import річ, розбір, силует
from ядро.поняття import Ситуація, Факт


class СилуетКартки(unittest.TestCase):
    def setUp(self):
        self.день = Ситуація(1, {"мета": Факт("conceal", "її_слова", "хочу приховати живіт"),
                                 "мета_зони": Факт(("belly",), "її_слова", ("живіт",)),
                                 "мета_важливо": Факт(("comfort",), "форма")}, {})
        self.запис = річ.читати({"id": "coat", "слот": "верхній_шар", "фото": "https://example.org/coat.jpg",
                                 "довжина_рівень": "максі", "мітки_речі": {"мітки": {
                                     "довжина": {"значення": "midi", "джерело": "фото"}}}})

    def _картка(self, профіль, номери):
        межа = Межа(з_порадами=True)
        межа.адреси_речей["coat"] = межа.предмет("coat", label="пальто")
        силует.додати_факти(межа, {"coat": self.запис}, self.день, профіль)
        опора = dict.fromkeys(номери, "known")
        if "f1" in опора:
            опора["f1"] = "item"
        відп = {"text": [{"about": опора, "says": "Поділ пальта веде погляд уздовж фігури."}],
                "advice": [{"about": {"f1": "item"}, "says": "Носи пальто розстебнутим."}], "names": {}, "unknown": []}
        склад = SimpleNamespace(образ="o1", речі=({"н": "coat"},))
        опис = розбір.текст_картки({"текст": json.dumps(відп, ensure_ascii=False)}, межа, склад, 1)
        return межа.факти, опис

    def test_особисте_речення_має_номери_крою_чи_краю_і_мірок(self):
        профіль = {"мірки": {"зріст": 163, "обхвати": {"талія": 71, "стегна": 97}}, "висоти": {"талія": 99}}
        факти, опис = self._картка(профіль, ("f1", "f2", "f3"))
        self.assertEqual(факти["f2"], {"state": "known", "items": ["f1"], "field": "length",
                                      "value": "міді", "source": "фото"})
        self.assertEqual(факти["f3"]["value"], {"height_cm": 163, "girths_cm": {"waist": 71, "hips": 97}})
        self.assertEqual(факти["f4"]["value"], {"goal": {"value": "conceal", "quote": "хочу приховати живіт"},
                                               "zones": {"value": ["belly"], "quote": ["живіт"]}})
        self.assertEqual(опис.розбіжності, ())
        self.assertEqual(опис.речення["text"][0]["about"], {"f1": "item", "f2": "known", "f3": "known"})

    def test_без_мірок_нема_факту_про_її_пропорції(self):
        факти, опис = self._картка({"мірки": {}, "зріст": 168}, ("f1", "f2", "f3"))
        self.assertNotIn("silhouette_measurements", {ф.get("field") for ф in факти.values()})
        self.assertEqual(факти["f3"]["field"], "silhouette_goal")
        self.assertEqual(опис.розбіжності, ())

    def test_мірка_без_краю_не_обґрунтовує_силует(self):
        _, опис = self._картка({"мірки": {"зріст": 163}}, ("f1", "f3"))
        self.assertEqual(опис.речення["text"], [])
        self.assertIn("silhouette_support_missing", {р["чому"] for р in опис.розбіжності})

    def test_зважена_знахідка_стає_дією_зі_своїм_ідентифікатором(self):
        межа = Межа(з_порадами=True)
        річ = межа.предмет("coat", label="пальто")
        код = "long_item_on_short_height_ranked"
        номер = межа.факт(код, {}, (річ,))
        заява = {"ід": "f-o1-5", "код": код, "вага": 0.2}
        силует.додати_дію_знахідки(межа, номер, dict(заява, вага=0))
        self.assertEqual(силует.поради_знахідок(межа), [])
        силует.додати_дію_знахідки(межа, номер, заява)
        дія, = силует.поради_знахідок(межа)
        self.assertEqual(дія["about"], {річ: "item", номер: код})
        self.assertEqual(дія["finding"], "f-o1-5")
        self.assertIn("На примірці", дія["says"])
