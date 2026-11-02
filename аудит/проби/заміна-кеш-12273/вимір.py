"""Лічить справжні побудови пакета на записаних входах, без підміни моста чи пулу."""
import argparse
import hashlib
import gzip
import json
import os
from pathlib import Path
import sys
import time


def виміряти(входи, модулі, каталог):
    """Відтворює складання й послідовні заміни; лише відсутня відповідь моделі — сценарна."""
    sys.path.insert(0, str(модулі))
    os.chdir(каталог)
    import bridge
    import міст_пакет as МП
    оригінал = МП.пакет_каталогу_кроками
    події, глибина = [], 0

    def спостерігати(*а, **к):
        """Спостерігає зовнішній виклик генератора; рекурсія контексту не є другою побудовою."""
        nonlocal глибина
        зовнішній = глибина == 0
        було = {id(п) for п in МП.КЕШ_ПАКЕТА.values()}
        глибина += 1
        try:
            пак = yield from оригінал(*а, **к)
        finally:
            глибина -= 1
        if зовнішній and пак and пак.get("_ключ"):
            події.append(dict(побудова=id(пак) not in було,
                              ключ=hashlib.sha256(пак["_ключ"].encode()).hexdigest()[:16]))
        return пак

    МП.пакет_каталогу_кроками = спостерігати

    звіт = []
    for запис in входи:
        d = json.loads(запис["вхід"])
        події.clear()
        початок = time.perf_counter()
        р = json.loads(bridge.виклик(запис["ім"], d))
        заміна = d.get("заміна")
        рядок = dict(ім=запис["ім"], рука=d.get("рука"), заміна=bool(заміна),
                     раунд=(1 if заміна and ("текст" in заміна or "відповіді" in заміна) else 0),
                     с=round(time.perf_counter()-початок, 3), події=list(події),
                     побудов=sum(п["побудова"] for п in події))
        рядок['речей_каталогу'] = sorted({len(п.get('_каталог') or []) for п in МП.КЕШ_ПАКЕТА.values()})
        if р.get("помилка"):
            raise RuntimeError(р)
        if заміна:
            рядок['результат'] = {к: в for к, в in р['заміна'].items() if к not in ('запити', 'стан', 'речі', 'річ')}
            рядок['нова_річ'] = (р['заміна'].get('річ') or {}).get('id')
            if р['заміна'].get('готово'):
                assert рядок['нова_річ'], р['заміна']
        звіт.append(рядок)
        print(json.dumps(рядок, ensure_ascii=False), flush=True)
        if заміна and d.get("рука") == '2' and not р["заміна"].get("готово"):
            # Запис обривається до відповіді #32. Це окремий SYNTHETIC дим завершення,
            # який не оголошується точним REPLAY_EXCHANGE чи живим прогоном.
            запит = р["заміна"]["запити"][0]
            пул = json.loads(запит["текст"])["pool"]["rows"]
            відповідь = json.dumps(dict(version='1', outfits=[dict(id='o1', items=[пул[0][0]])]))
            d["заміна"] = dict(заміна, текст=відповідь)
            події.clear()
            фінал = json.loads(bridge.виклик('від_моделі', d))["заміна"]
            річ = фінал.get("річ") or {}
            assert фінал.get("готово") and річ.get("id") != заміна["ід"]
            assert річ.get("слот") == заміна["слот"]
            рядок["сценарний_фінал"] = dict(річ=річ["id"], слот=річ["слот"],
                                            побудов=sum(п["побудова"] for п in події))
            print('SYNTHETIC:', json.dumps(рядок["сценарний_фінал"], ensure_ascii=False), flush=True)
    return звіт


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('входи', type=Path)
    parser.add_argument('--модулі', type=Path, required=True)
    parser.add_argument('--каталог', type=Path, required=True)
    parser.add_argument('--вихід', type=Path, required=True)
    a = parser.parse_args()
    вихід = a.вихід.resolve()
    читати = gzip.open if a.входи.suffix == '.gz' else open
    with читати(a.входи, 'rt', encoding='utf-8') as ф:
        входи = [json.loads(р) for р in ф]
    # Кеші наповнює справжній початковий запит; після нього — записані заміни.
    вибрані = [next(р for р in входи if р['ім'] == 'запити')]
    вибрані += [р for р in входи if р['ім'] == 'від_моделі' and json.loads(р['вхід']).get('заміна')]
    результат = виміряти(вибрані, a.модулі.resolve(), a.каталог.resolve())
    вихід.write_text(json.dumps(результат, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
