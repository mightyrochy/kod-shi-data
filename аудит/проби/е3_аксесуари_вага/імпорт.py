"""Окремий повтор §117 без зміни гейта; результат — імпорт.json поруч."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

КОРІНЬ = Path(__file__).resolve().parents[3]
ДЖЕРЕЛА = КОРІНЬ / 'джерела'
sys.path.insert(0, str(ДЖЕРЕЛА / 'прилади'))
from запуск_python import запустити_python


def main():
    """Запустити ті самі три імпорти у порожній теці й зберегти всі результати."""
    звіт = {}
    тимчасова = Path(os.environ['TMP']).resolve()
    for модуль in ('траса_петлі', 'гейти_нові', 'measure_person_axis'):
        with tempfile.TemporaryDirectory(prefix='імпорт117_', dir=тимчасова) as тека:
            assert Path(тека).resolve().is_relative_to(тимчасова)
            до = {п.name for п in ДЖЕРЕЛА.iterdir() if п.name != '__pycache__'}
            старт = time.perf_counter()
            р = запустити_python([sys.executable, '-c', 'import ' + модуль], cwd=тека,
                                  env=dict(os.environ, PYTHONPATH=str(ДЖЕРЕЛА)),
                                  capture_output=True, text=True, timeout=10)
            звіт[модуль] = dict(код=р.returncode, секунд=time.perf_counter() - старт,
                                stdout=р.stdout, stderr=р.stderr,
                                нове_в_теці=sorted(п.name for п in Path(тека).iterdir()
                                                  if п.name != '__pycache__'),
                                нове_в_джерелах=sorted({п.name for п in ДЖЕРЕЛА.iterdir()
                                                       if п.name != '__pycache__'} - до))
    Path(__file__).with_suffix('.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(звіт, ensure_ascii=False))


if __name__ == '__main__':
    main()
