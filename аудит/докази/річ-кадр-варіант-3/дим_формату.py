"""Перевіряє межу дослідного результату й приймального формату храповика."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела/прилади'))
import корінь_річ_кадр_варіант as П


def main():
    """На малому інвентарі відділяє три відмови від прийнятого числа."""
    точка = dict(файл='вхід.py', область='<модуль>', рядок=1, пункт=1, вираз='вираз')
    звіт = []
    for назва, приймання, переглянуто, очікується in [
        ('без приймання', False, True, False),
        ('непереглянутий вираз', True, False, False),
        ('обидві умови не виконано', False, False, False),
        ('прийнята база і переглянутий інвентар', True, True, True),
    ]:
        база = dict(приймання=приймання, рішення={'ключ': dict(порушення=True, чому='доказ')} if переглянуто else {})
        вихід = io.StringIO()
        помилка = None
        with patch.object(П, 'кандидати', return_value=({'ключ': точка}, {'ключ': точка}, 1)), \
             patch.object(Path, 'read_text', return_value=json.dumps(база)), \
             patch.object(sys, 'argv', ['прилад']), redirect_stdout(вихід):
            try:
                П.main()
            except ValueError as виняток:
                помилка = str(виняток)
        assert (помилка is None) == очікується, назва
        assert (вихід.getvalue().splitlines()[-1] == 'місць: 1') if очікується else not вихід.getvalue(), назва
        звіт.append(dict(проба=назва, пройдено=True, stdout=вихід.getvalue(), помилка=помилка))
    Path(__file__).with_suffix('.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Формат: 4/4')


if __name__ == '__main__':
    main()
