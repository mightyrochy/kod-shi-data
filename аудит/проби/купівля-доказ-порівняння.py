"""Офлайн-регресія суду купівлі: пояснення не плутає брак доказу з перевагою."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import суд_покупки as суд
import внутрішня_мова as мова


def вердикт(заяви=(), *, рівень="невідомо", ризик=(), провал=(), без_входу=()):
    return {"рівень": рівень, "повідомлення": {"statements": list(заяви)},
            "чекліст": {"ризик": [{"коди": [код]} for код in ризик],
                        "провал": list(провал), "без_входу": list(без_входу)}}


class Пояснення(unittest.TestCase):
    def test_брак_і_ризик_не_перевага(self):
        порівняння = {
            "sparse": вердикт((мова.заява("hem_not_judged", missing="garment_length"),
                               мова.заява("cut_vs_figure_not_judged", missing="cut"),
                               мова.заява("colour_role_not_judged", missing="colour_measure")),
                              без_входу=("довжина", "крій", "колір")),
            "known": вердикт((мова.заява("hem_on_her_body", level="міді", measured_from="garment_length"),),
                             ризик=("midi_proportion_decided_by_shoes",), провал=("відомий провал",)),
        }
        до = deepcopy(порівняння)
        for вхід in (порівняння, dict(reversed(list(порівняння.items())))):
            в = суд.вибір(вхід)
            self.assertEqual(в["порядок"], ["sparse", "known"])
            self.assertEqual(в["заяви"][0]["item_ids"], ["sparse"])
            self.assertEqual(в["заяви"][0]["values"], {"reasons": [], "then": ["known"]})
        self.assertEqual(порівняння, до)

    def test_підтверджена_опора_не_причина_порядку(self):
        опора = мова.заява("maxi_holds", by="volume")
        with_fact = вердикт((опора,))
        failed = вердикт(провал=("відомий провал",))
        for first in (with_fact, вердикт()):
            вхід = {"first": first, "other": failed}
            до = deepcopy(вхід)
            в = суд.вибір(вхід)
            self.assertEqual(в["порядок"], ["first", "other"])
            self.assertEqual(в["заяви"][0]["item_ids"], ["first"])
            self.assertEqual(в["заяви"][0]["values"], {"reasons": [], "then": ["other"]})
            self.assertEqual(вхід, до)
        нічия = суд.вибір({"first": with_fact, "other": вердикт()})
        self.assertEqual(нічия["порядок"], ["first", "other"])
        self.assertEqual([(з["code"], з["item_ids"]) for з in нічия["заяви"]],
                         [("buy_order_tie", ["first", "other"])])
        self.assertEqual(with_fact["повідомлення"]["statements"], [опора])

    def test_нічия_і_наступна_позиція_не_змінені(self):
        перші = {"first": вердикт(), "also": вердикт()}
        self.assertEqual([з["code"] for з in суд.вибір(перші)["заяви"]], ["buy_order_tie"])
        в = суд.вибір({**перші, "then": вердикт(ризик=("measured_dividing_line_depends_on_size",))})
        self.assertEqual(в["порядок"], ["first", "also", "then"])
        self.assertEqual([(з["code"], з["item_ids"]) for з in в["заяви"]],
                         [("buy_first", ["first", "also"]), ("buy_order_tie", ["first", "also"])])
        self.assertEqual(в["заяви"][0]["values"], {"reasons": [], "then": ["then"]})


if __name__ == "__main__":
    unittest.main()
