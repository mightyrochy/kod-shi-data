"""Офлайн-регресія суду купівлі (#4690): порада «яку першою» стоїть лише на доведеному, брак входу — не перевага.

Мірило з доручення менеджера (7140464051): каталоговий вхід і фото-вхід; провалення невідомого й відомого; нічия;
порядок, ID і `then` незмінні. Позитивна пара K-FIT-03 на продуктовому вході (усі геометричні входи з походженням і
похибкою; один підтверджено проходить, інший провалюється) — на паузі: сюди вона не входить, а перевага тут
перевіряється на вердиктах із записаним чеклістом."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import суд_покупки as суд
import внутрішня_мова as мова
import пошук_речі
import міст_стилістка


def вердикт(заяви=(), *, рівень="личить", ризик=(), провал=(), без_входу=()):
    return {"рівень": рівень, "повідомлення": {"statements": list(заяви)},
            "чекліст": {"ризик": [{"коди": [код]} for код in ризик],
                        "провал": list(провал), "без_входу": list(без_входу)}}


def коди(в):
    return [(з["code"], з["item_ids"]) for з in в["заяви"]]


def значення(в, код):
    return next(з["values"] for з in в["заяви"] if з["code"] == код)


class НевідомеНеПеревага(unittest.TestCase):
    """Невідоме — не перевага над відомим провалом: порядок лишається, порада зникає."""

    def пара(self):
        return {
            "sparse": вердикт((мова.заява("hem_not_judged", missing="garment_length"),), рівень="невідомо",
                              без_входу=("довжина", "крій", "колір")),
            "known": вердикт((мова.заява("hem_on_her_body", level="міді", measured_from="garment_length"),),
                             рівень="невідомо", ризик=("midi_proportion_decided_by_shoes",),
                             провал=("відомий провал",)),
        }

    def test_брак_входу_проти_відомого_провалу_порядок_без_поради(self):
        порівняння = self.пара()
        до = deepcopy(порівняння)
        for вхід in (порівняння, dict(reversed(list(порівняння.items())))):
            в = суд.вибір(вхід)
            self.assertEqual(в["порядок"], ["sparse", "known"])  # порядок старий
            self.assertEqual(коди(в), [("buy_order_not_established", ["sparse", "known"])])
        self.assertEqual(порівняння, до)

    def test_ризик_без_запису_не_уникнуто(self):
        # у першої нема запису ризику, бо нема входу: це не «уникає ризику»
        в = суд.вибір({"a": вердикт(без_входу=("край",)), "b": вердикт(ризик=("midi_proportion_decided_by_shoes",))})
        self.assertEqual(в["порядок"], ["a", "b"])
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])

    def test_утрата_входу_знімає_першість(self):
        # перша судиться неповно, друга має підтверджений провал — першості доказ не дає
        в = суд.вибір({"a": вердикт(без_входу=("край",)), "b": вердикт(провал=("відомий провал",))})
        self.assertEqual(в["порядок"], ["a", "b"])
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])

    def test_брак_входу_лише_в_решти_не_перевага(self):
        в = суд.вибір({"a": вердикт(), "b": вердикт(без_входу=("край",))})
        self.assertEqual(в["порядок"], ["a", "b"])
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])


class ДоведенаПеревага(unittest.TestCase):
    def test_відомий_провал_проти_пройденого_дає_пораду_з_аспектом(self):
        опора = мова.заява("maxi_holds", by="volume")
        перша, друга = вердикт((опора,)), вердикт(провал=("відомий провал",))
        for перша_з_початку in (True, False):
            вхід = {"first": перша, "other": друга} if перша_з_початку else {"other": друга, "first": перша}
            до = deepcopy(вхід)
            в = суд.вибір(вхід)
            self.assertEqual(в["порядок"], ["first", "other"])
            self.assertEqual(коди(в), [("buy_first", ["first"])])
            self.assertEqual(значення(в, "buy_first"),
                             {"reasons": [], "proven_over": {"other": ["failed_checks"]}, "then": ["other"]})
            self.assertEqual(вхід, до)
        self.assertEqual(перша["повідомлення"]["statements"], [опора])  # окремий факт лишився у вердикті

    def test_лише_названий_ризик(self):
        в = суд.вибір({"a": вердикт(), "b": вердикт(ризик=("midi_proportion_decided_by_shoes",))})
        self.assertEqual(значення(в, "buy_first")["proven_over"], {"b": ["named_risks"]})

    def test_рівні_суджених_речей(self):
        в = суд.вибір({"a": вердикт(рівень="личить"), "b": вердикт(рівень="з умовою")})
        self.assertEqual(в["порядок"], ["a", "b"])
        self.assertEqual(значення(в, "buy_first")["proven_over"], {"b": ["level"]})

    def test_рівень_невідомо_не_доводить(self):
        в = суд.вибір({"a": вердикт(рівень="личить"), "b": вердикт(рівень="невідомо")})
        self.assertEqual(в["порядок"], ["a", "b"])
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])

    def test_перевага_над_кожною_з_решти(self):
        # над другою доведена, над третьою лише «більше не суджених» — порада на всіх зникає
        в = суд.вибір({"a": вердикт(), "b": вердикт(провал=("п",)), "c": вердикт(без_входу=("край",))})
        self.assertEqual(в["порядок"], ["a", "c", "b"])
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])


class ПершістьПопарна(unittest.TestCase):
    """`proven_over` — аспекти окремо проти кожної з решти (перевірка #4725, рішення менеджера)."""

    def test_ризик_над_одною_провал_над_іншою(self):
        в = суд.вибір({"A": вердикт(), "B": вердикт(ризик=("midi_proportion_decided_by_shoes",)),
                       "C": вердикт(провал=("п",))})
        self.assertEqual(в["порядок"], ["A", "B", "C"])
        self.assertEqual(коди(в), [("buy_first", ["A"])])
        self.assertEqual(значення(в, "buy_first"),
                         {"reasons": [], "proven_over": {"B": ["named_risks"], "C": ["failed_checks"]}, "then": ["B", "C"]})

    def test_рівень_над_одною_провал_над_іншою(self):
        в = суд.вибір({"A": вердикт(), "B": вердикт(рівень="з умовою"), "C": вердикт(провал=("п",))})
        self.assertEqual(в["порядок"][0], "A")
        self.assertEqual(значення(в, "buy_first")["proven_over"], {"B": ["level"], "C": ["failed_checks"]})

    def test_недоведена_над_однією_з_решти_порада_не_стоїть(self):
        в = суд.вибір({"A": вердикт(), "B": вердикт(провал=("п",)), "C": вердикт(без_входу=("край",))})
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])
        self.assertEqual(в["заяви"][0]["values"], {"why": "input_missing"})


class ПричинаНеДоведено(unittest.TestCase):
    def test_повністю_суджені_ніколи_не_стверджують_брак_входу(self):
        рівні = ("личить", "з умовою", "невідомо", "краще інша")
        речі = [вердикт(рівень=р, провал=("п",) * ф, ризик=("r",) * н) for р in рівні for ф in (0, 1) for н in (0, 1)]
        перевірено = 0
        for i, a in enumerate(речі):
            for b in речі[i:]:
                for вхід in ({"a": a, "b": b}, {"a": a, "b": b, "c": вердикт(рівень="невідомо")}):
                    for з in суд.вибір(вхід)["заяви"]:
                        if з["code"] == "buy_order_not_established":
                            перевірено += 1
                            self.assertEqual(з["values"], {"why": "no_item_proved_better"}, (a, b))
        self.assertTrue(перевірено)

    def test_брак_входу_називає_брак_входу(self):
        в = суд.вибір({"a": вердикт(без_входу=("край",)), "b": вердикт()})
        self.assertEqual(в["заяви"][0]["values"], {"why": "input_missing"})

    def test_невідомий_рівень_суджених_речей_не_брак_входу(self):
        в = суд.вибір({"a": вердикт(рівень="личить"), "b": вердикт(рівень="невідомо")})
        self.assertEqual([з["code"] for з in в["заяви"]], ["buy_order_not_established"])
        self.assertEqual(в["заяви"][0]["values"], {"why": "no_item_proved_better"})


class Нічия(unittest.TestCase):
    def test_справжня_нічия_суджених(self):
        перші = {"first": вердикт(), "also": вердикт()}
        в = суд.вибір(перші)
        self.assertEqual(в["порядок"], ["first", "also"])
        self.assertEqual(коди(в), [("buy_order_tie", ["first", "also"])])

    def test_рівність_за_браком_входу_не_нічия(self):
        в = суд.вибір({"first": вердикт(без_входу=("край",)), "also": вердикт(без_входу=("край",))})
        self.assertEqual(в["порядок"], ["first", "also"])
        self.assertEqual(коди(в), [("buy_order_not_established", ["first", "also"])])

    def test_часткова_нічия_лишає_порядок_ід_і_then(self):
        перші = {"first": вердикт(), "also": вердикт()}
        в = суд.вибір({**перші, "then": вердикт(ризик=("measured_dividing_line_depends_on_size",))})
        self.assertEqual(в["порядок"], ["first", "also", "then"])
        self.assertEqual(коди(в), [("buy_first", ["first", "also"]), ("buy_order_tie", ["first", "also"])])
        self.assertEqual(значення(в, "buy_first"),
                         {"reasons": [], "proven_over": {"then": ["named_risks"]}, "then": ["then"]})

    def test_часткова_нічия_без_входу_нагорі_не_дає_поради(self):
        в = суд.вибір({"first": вердикт(без_входу=("край",)), "also": вердикт(без_входу=("край",)),
                       "then": вердикт(провал=("п",))})
        self.assertEqual(в["порядок"], ["first", "also", "then"])
        self.assertEqual(коди(в), [("buy_order_not_established", ["first", "also", "then"])])

    def test_менше_двох_речей(self):
        self.assertEqual(суд.вибір({"a": вердикт()}), dict(порядок=["a"], заяви=[]))


ВАРІАНТИ = [{"id": "sparse", "слот": "низ", "назва": "Неповна", "ціна": 1, "url": "u1", "фото": ["f1"]},
            {"id": "known", "слот": "низ", "назва": "Відома", "ціна": 2, "url": "u2", "фото": ["f2"]}]


class КаталоговийВхід(unittest.TestCase):
    """Пошук у каталозі: той самий суд, порядок варіантів — `вибір`."""

    def відповідь(self, вердикти):
        with mock.patch.object(пошук_речі, "знайти", return_value=(deepcopy(ВАРІАНТИ), {})), \
                mock.patch.object(пошук_речі, "оцінити", return_value=вердикти):
            return пошук_речі.відповідь([], {}, {}, {})

    def test_брак_входу_порядок_без_поради(self):
        в = self.відповідь(НевідомеНеПеревага().пара())
        self.assertEqual([в_["ід"] for в_ in в["варіанти"]], ["sparse", "known"])
        self.assertEqual([з["code"] for з in в["choice"]], ["buy_order_not_established"])
        self.assertEqual([з["code"] for з in в["повідомлення"]["statements"]][-1], "buy_order_not_established")

    def test_доведене_зберігає_пораду(self):
        в = self.відповідь({"sparse": вердикт(), "known": вердикт(провал=("п",))})
        self.assertEqual([в_["ід"] for в_ in в["варіанти"]], ["sparse", "known"])
        self.assertEqual([з["code"] for з in в["choice"]], ["buy_first"])
        self.assertEqual(в["choice"][0]["values"]["proven_over"], {"known": ["failed_checks"]})


class ФотоВхід(unittest.TestCase):
    """Дві речі «хочу купити» з фото: промпт стилістки несе `choice` із суду."""

    def промпт(self, вердикти):
        речі = [{"ід": і, "чия": "хочу купити", "вердикт": в, "фото": f"фото-{і}"} for і, в in вердикти.items()]
        return json.loads(міст_стилістка.промпт("яку з цих купити", речі=речі))

    def choice(self, в):
        def шукати(о):
            if isinstance(о, dict):
                if "choice" in о and isinstance(о["choice"], list):
                    return о["choice"]
                for x in о.values():
                    r = шукати(x)
                    if r is not None:
                        return r
            elif isinstance(о, list):
                for x in о:
                    r = шукати(x)
                    if r is not None:
                        return r
        return шукати(в)

    def test_брак_входу_без_поради(self):
        вх = НевідомеНеПеревага().пара()
        з = self.choice(self.промпт(вх))
        self.assertEqual([x["code"] for x in з], ["buy_order_not_established"])

    def test_доведене_з_порадою(self):
        з = self.choice(self.промпт({"a": вердикт(), "b": вердикт(провал=("п",))}))
        self.assertEqual([x["code"] for x in з], ["buy_first"])
        self.assertEqual(з[0]["values"]["proven_over"], {"b": ["failed_checks"]})


if __name__ == "__main__":
    unittest.main()
