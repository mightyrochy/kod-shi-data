# -*- coding: utf-8 -*-
"""Друкує колір примірки на актуальних картках речей руки 1 файла 1551.

Запуск із джерела: python3 проби/примірка_колір_5235.py <каталог.xml>.
Фото не завантажує; ID узяті з наявного вердикту 1551, відповіді моделі не створює.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import міст_опис as М, приміряння as П, внутрішня_мова as В


def виміряти(каталог):
    """Провести справжні картки producer через поля показу й збирач примірки."""
    ід = ['ж-01224@stolyarchuk.com.ua', 'ж-04824@alot.com.ua',
          'ж-08794@favoriteshoes.com.ua', 'ж-07961@cultboutique.com.ua',
          'ж-11777@theoriginals.com.ua']
    картки = json.loads(М.показ(dict(каталог=каталог, речі=ід)))
    показ = pathlib.Path('показ.html').read_text()
    import re, subprocess
    функція = re.search(r'const поляПриміркиП = р => (.*?);', показ, re.S)[0]
    скрипт = функція + '\nprocess.stdout.write(JSON.stringify(' + json.dumps(картки) + '.map(поляПриміркиП)));'
    вхід = json.loads(subprocess.check_output(['node', '-e', скрипт]))
    запит = json.loads(П.промпт(вхід))['item_photos']
    слова = sum(р.get('color') not in В.ТАБЛИЦЯ['color_name'] and р.get('color') != В.UNKNOWN
                for р in запит if 'color' in р)
    print(json.dumps(dict(словесних=слова, кольори=[р.get('color') for р in запит],
                         коди=[р.get('код_кольору') for р in картки],
                         облік=[(р['id'], р.get('урл'), р.get('фото')) for р in картки],
                         фото=[р['photo'] for р in запит]), ensure_ascii=False))
    assert all(П.опис_речі({"код_кольору": к})["color"] == к for к in В.ТАБЛИЦЯ["color_name"])
    assert all(П.опис_речі({"код_кольору": к})["color"] == В.UNKNOWN for к in (None, "оливка", "капучіно", []))
    assert "color" not in П.опис_речі({"код_кольору": "beige", "кадр_інший": True})
    return слова


if __name__ == '__main__':
    sys.exit(bool(виміряти(sys.argv[1])))
