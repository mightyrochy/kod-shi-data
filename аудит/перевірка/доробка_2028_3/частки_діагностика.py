"""Звіряє частку кандидата з його вікном на справжньому збирачі слота."""
import ast
import json
import pathlib
import sys

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
import feed
import колір_річ as КР


def головна():
    """Перевіряє два вікна однієї реальної речі та незмінність її вхідного запису."""
    тека = pathlib.Path(__file__).resolve().parent
    вхід = json.loads((тека / 'контекст-ДО.json').read_text(encoding='utf-8'))[0]['речі'][0]
    річ = dict(id=вхід['id'], lab=вхід['lab'], колір_не_вимір=вхід['колір_не_вимір'],
               слот='верх', вікно=вхід['колір_не_вимір']['вікно'])
    дерево = ast.parse((КОРІНЬ / 'джерела/композитор_слоти.py').read_text(encoding='utf-8'))
    функція = next(ф for ф in ast.walk(дерево) if isinstance(ф, ast.FunctionDef) and ф.name == '_збір_слота')
    простір = dict(feed=feed, _КР=КР, слот='верх', у_слоті=[річ])
    exec(compile(ast.Module(body=[функція], type_ignores=[]), 'справжній-збір-слота', 'exec'), простір)
    повне = dict(слот='верх', L_min=0, L_max=100, C_min=0, C_max=200,
                 h_from=0, h_to=359.999, нейтраль=False)
    вікна = [повне, dict(повне, L_min=60)]
    результат = простір['_збір_слота'](вікна)
    факти = [dict(відстань=д, частка_кандидата=к.get('_частка_вікна'),
                  частка_його_вікна=feed.частка_вікна(КР.вікно_речі(к), в), вікно=в)
             for д, к, в in результат]
    assert len(факти) == 2
    assert all(ф['частка_кандидата'] == ф['частка_його_вікна'] for ф in факти)
    assert '_частка_вікна' not in річ
    assert факти[0]['частка_кандидата'] == 1.0 and факти[1]['частка_кандидата'] == 0.75
    (тека / 'частка-контрприклад-ПІСЛЯ.json').write_text(json.dumps(факти, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Частки двох вікон: 1.0 / 0.75; кандидати мають свої значення; вхід не мутовано; код 0')
    return 0


if __name__ == '__main__':
    sys.exit(головна())
