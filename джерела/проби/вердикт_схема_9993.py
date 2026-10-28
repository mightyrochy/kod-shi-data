"""Час і розмір `від_моделі` на тому самому каталозі: аргумент — тека джерел ДО чи ПІСЛЯ."""
import json, os, statistics, sys, time
from pathlib import Path


def виклик(вхід):
    """Заміряти реальний міст, включно із серіалізацією відповіді."""
    початок = time.perf_counter()
    текст = Б.виклик("від_моделі", json.dumps(вхід, ensure_ascii=False))
    return time.perf_counter() - початок, текст


if __name__ == "__main__":
    тека = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(тека)); os.chdir(тека)
    import bridge as Б
    вхід = dict(json.loads(Path("стенд_вх.json").read_text(encoding="utf8")), сід=4242,
                варіантів=10, ремонт_варіантів=5, бюджет_символів=120000, без_фото=1, пакети=1)
    запити = json.loads(Б.виклик("запити", json.dumps(вхід, ensure_ascii=False)))
    пул = запити["пакети"]["1"]["пул"]
    образи = [dict(ід="о%d" % (і + 1), речі=[пул[с][і % len(пул[с])]["н"]
                      for с in ("верх", "низ", "взуття", "сумка")]) for і in range(10)]
    вхід["текст_моделі"] = json.dumps(dict(версія="1", образи=образи), ensure_ascii=False)
    часи = [виклик(вхід) for _ in range(3)]
    вихід = json.loads(часи[-1][1])
    assert not вихід.get("помилка"), вихід.get("помилка")
    print(json.dumps(dict(джерела=str(тека), секунд=[round(ч, 6) for ч, _ in часи],
                          медіана=statistics.median(ч for ч, _ in часи),
                          відповідь_символів=len(часи[-1][1]),
                          ремонт_символів=len(вихід["промпт_ремонту"]),
                          вибір_символів=len(вихід["промпт_лише_вибору"])), ensure_ascii=False))
