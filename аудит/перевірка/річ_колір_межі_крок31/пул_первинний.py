"""Первинний добір семи слотів на вході живого композитора, без наступного добору гілок і пакування.

Запуск із кореня: python пул_первинний.py [тека джерел для ДО]. Рівність з повним стендом ДО звіряється окремо.
"""
import json
import os
import pickle
import sys
import tempfile
from pathlib import Path


def головна():
    """Зняти справжні спільні входи композитора й виконати добір кожного ювелірного слота."""
    репо = Path.cwd()
    код = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else репо / "джерела"
    sys.path.insert(0, str(код))
    os.chdir(репо / "джерела")
    import bridge as Б
    import feed as Ф
    import palettes as П
    import тест_живого_шляху as Т
    import композитор_збирання as З
    import композитор_слоти as С

    class ВхідЗнято(BaseException):
        """Зупинка стенда перед первинним добором; продукт не змінено."""

    вхід = {}

    def зняти(речі, вікна, слот, сід, **параметри):
        """Зберегти спільні аргументи всіх слотів з одного виклику композитора."""
        вхід.update(речі=речі, вікна=вікна, сід=сід, параметри=параметри)
        raise ВхідЗнято()

    З._кандидати_на_слот = зняти
    база = json.loads((репо / "джерела/стенд_вх.json").read_text(encoding="utf-8"))
    база["каталог"] = Ф.каталог_на_диску(str(репо / "джерела/каталог_повний.xml"))
    база["кеш_кольорів"] = str(Path(tempfile.gettempdir()) / ("крок31_первинний_" + код.parent.name + ".json"))
    if not Path(база["кеш_кольорів"]).exists(): Path(база["кеш_кольорів"]).write_text("{}", encoding="utf-8")
    вихід = {}
    for метал in (None, "золото", "срібло"):
        for гілка in (None, 0):
            дані = dict(база, намір="conventional")
            if гілка is not None: дані["гілка"] = гілка
            if метал: дані["драп_сирий"] = {"метал": метал}
            паспорт = json.loads(Б.виклик("паспорт", json.dumps(dict(
                json_моделі=json.dumps(dict(Т.ПАСПОРТ_МОДЕЛІ, намір="conventional"), ensure_ascii=False),
                сценарій=дані.get("сценарій") or {}, вимоги=""), ensure_ascii=False)))
            дані["паспорт"] = паспорт["паспорт"]
            вхід.clear()
            try:
                Б.виклик("запити", json.dumps(dict(дані, пакети=1), ensure_ascii=False))
            except ВхідЗнято:
                pass
            assert вхід, "живий шлях не дійшов до композитора"
            слоти = dict.fromkeys(q["слот"] for q in вхід["вікна"] if q.get("метал") and q.get("слот"))
            assert len(слоти) == 7, list(слоти)
            кеш = Path(tempfile.gettempdir()) / "входи_композитора_31"
            кеш.mkdir(exist_ok=True)
            try:
                with (кеш / f"{код.parent.name}_{метал or 'нема'}_{гілка}.pickle").open("wb") as файл:
                    pickle.dump(вхід, файл)
            except (OSError, TypeError, pickle.PickleError) as помилка:
                print("Кеш входу не записано:", помилка, file=sys.stderr, flush=True)
            композитор = {}
            for слот in слоти:
                пул, _, _ = С.кандидати_на_слот(вхід["речі"], вхід["вікна"], слот, вхід["сід"], **вхід["параметри"])
                композитор[слот] = dict(
                    рядки=sorted(f'{q.get("роль")}|{q.get("метал")}|{q.get("ранг_риси")}|{bool(q.get("менш_ходове"))}'
                                 for q in вхід["вікна"] if q.get("слот") in (None, слот) and q.get("метал")),
                    речі=[dict(id=р.get("id"), метал=р.get("метал"), роль=(р.get("_вікно") or {}).get("роль"),
                               менш=bool((р.get("_вікно") or {}).get("менш_ходове"))) for р in пул])
            назва = f"{метал or 'нема'}·{'—' if гілка is None else гілка}"
            вихід[назва] = dict(композитор=композитор, помилка=None, метал_палітри=метал or "обидва")
            print("Первинний добір:", назва, file=sys.stderr, flush=True)
    json.dump(вихід, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    головна()
