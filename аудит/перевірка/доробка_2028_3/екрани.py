"""Відтворює дані моста ДО/ПІСЛЯ й строго звіряє факти браузерного показу.

python аудит/перевірка/доробка_2028_3/екрани.py
python аудит/перевірка/доробка_2028_3/екрани.py --звірити
"""
import ast
import gzip
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
ТЕКА = pathlib.Path(__file__).resolve().parent


def головна():
    """Порівнює чип і стрічку з фактичним прийомом, включно з явним підписом."""
    if '--звірити' in sys.argv:
        схема = 'тональна' if '--тональна' in sys.argv else 'тріада'
        факти = json.loads((ТЕКА / схема / 'показ.json').read_text(encoding='utf-8'))
        сцени = json.loads(gzip.decompress((ТЕКА / 'екрани.json.gz').read_bytes()))
        колір = lambda h: 'rgb(%d, %d, %d)' % tuple(bytes.fromhex(h[1:]))
        assert len(факти) == 26
        for р in факти:
            сцена = next(с for с in сцени if с['сцена'] == р['сцена'])
            тріада = next(г for г in сцена[р['режим']]['гілки'] if г['схема'] == схема)
            чип = next(ч for ч in р['чипи'] if ч['текст'].startswith(схема))
            assert чип['кольори'] == [колір(h) for h in тріада['зразки']], р['сцена']
            if р['режим'] == 'ПІСЛЯ':
                assert len(чип['кольори']) == 3 and р['стрічка'][1:] == чип['кольори']
                if тріада.get('запасний_прийом'):
                    assert 'зразок:' in чип['текст']
                    assert 'поєднання цієї схеми не дібрано; зразок:' in р['підпис_стрічки']
                else:
                    assert 'зразок:' not in чип['текст']
                if схема == 'тріада':
                    assert not тріада.get('запасний_прийом')
        підсумок = dict(схема=схема, чипів=26, збігів=26, стрічок_ПІСЛЯ=13, код=0)
        (ТЕКА / (схема + '-показ-вимір.json')).write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'DOM {схема}: 26/26 чипів = міст, 13/13 стрічок = чип; підписи відповідають справжньому прийому; код 0')
        return 0
    sys.path.insert(0, str(КОРІНЬ / 'джерела'))
    # Обидві частини ДО беруться з того самого коміту: старий міст не має
    # непомітно читати новий генератор через поточний модуль palettes.
    стара_палітра = subprocess.check_output(['git', 'show', '8c6dd1f7e:джерела/palettes.py'], cwd=КОРІНЬ)
    тимчасова = tempfile.TemporaryDirectory(prefix='kolory-2028-3-screen-do-')
    файл_палітри = pathlib.Path(тимчасова.name) / 'palettes.py'
    файл_палітри.write_bytes(стара_палітра)
    спец = importlib.util.spec_from_file_location('palettes', файл_палітри)
    палітра = importlib.util.module_from_spec(спец)
    sys.modules['palettes'] = палітра
    спец.loader.exec_module(палітра)
    import міст_основи as МО
    старий = subprocess.check_output(['git', 'show', '8c6dd1f7e:джерела/міст_основи.py'], cwd=КОРІНЬ).decode()
    функція = next(ф for ф in ast.parse(старий).body if isinstance(ф, ast.FunctionDef) and ф.name == 'палітри')
    простір = dict(vars(МО))
    exec(compile(ast.Module(body=[функція], type_ignores=[]), 'міст-ДО', 'exec'), простір)
    межа = json.loads(gzip.decompress((ТЕКА / 'тріади-ПІСЛЯ.json.gz').read_bytes()))
    сцени = [dict(сцена='персона-' + str(р['персона']), вхід=р['вхід'],
                  ДО=json.loads(простір['палітри'](р['вхід'])), ПІСЛЯ=р['екран']) for р in межа]
    (ТЕКА / 'екрани.json.gz').write_bytes(gzip.compress(json.dumps(сцени, ensure_ascii=False).encode(), mtime=0))
    файл = pathlib.Path(tempfile.gettempdir()) / 'kolory-2028-3-palitra-do.js'
    файл.write_bytes(subprocess.check_output(['git', 'show', '8c6dd1f7e:джерела/показ/палітра.js'], cwd=КОРІНЬ))
    тимчасова.cleanup()
    print('Справжній міст ДО/ПІСЛЯ: 13 входів; JS ДО:', файл)
    return 0


if __name__ == '__main__':
    sys.exit(головна())
