# -*- coding: utf-8 -*-
"""7100: факт збереження всіх результатів після збою/таймаута, без жнив і мережі."""
import importlib.util
from pathlib import Path
import tempfile


def головна():
    """Перевірити короткий звіт на трьох малих пробах та відсутньому вході."""
    шлях = Path(__file__).resolve().parents[1] / "прилади" / "звіт_після_жнив.py"
    опис = importlib.util.spec_from_file_location("звіт_жнив", шлях)
    модуль = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(модуль)
    with tempfile.TemporaryDirectory() as тека:
        корінь = Path(тека) / "репо"
        проби = корінь / "джерела" / "проби"
        проби.mkdir(parents=True)
        for ім, код in {"1": "print('готово')", "2": "raise SystemExit(7)",
                        "3": "import time; time.sleep(2)"}.items():
            (проби / ("каталог_проблеми_" + ім + ".py")).write_text(код, encoding="utf-8")
        каталог = корінь / "нові.xml"
        каталог.write_text("<yml_catalog/>", encoding="utf-8")
        вихід = Path(тека) / "звіт"
        assert модуль.звіт(корінь, вихід, каталог, "failure", секунд=0.2) == 1
        текст = (вихід / "діагностика_каталогу.md").read_text()
        assert all(з in текст for з in ("| 0 |", "| 7 |", "| 124 |", "`failure`"))
        assert "готово" in (вихід / "діагностика_каталогу.log").read_text()
        assert (вихід / "звіт_жнив.md").read_text() == текст
        assert каталог.read_text() == "<yml_catalog/>"
        assert модуль.звіт(корінь, вихід, корінь / "немає.xml", "failure") == 1
        assert (вихід / "діагностика_каталогу.md").read_text().count("старий каталог не підставлено") == 3
    print("7100: rc 0/7/124, stdout, усі 3 рядки, брак входу, незмінний XML; звіт збережено")


if __name__ == "__main__":
    головна()
