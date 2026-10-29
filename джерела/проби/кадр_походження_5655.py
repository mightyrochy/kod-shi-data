# -*- coding: utf-8 -*-
"""5655/5632: replay збереженого виміру на незмінених байтах; API/маска не запускаються.
Аргумент: тека свідків ноутбука з ж-05085.json, мета.json і його local_photo."""
import gzip, hashlib, json, pathlib, sys, tempfile, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import feed as Ф, жнива_запис as Ж, фід_фото as К
from PIL import Image

import колір_річ as _КОЛІР
def головна():
    """Друкує факт producer→злиття→картка на свідку саме цього SKU; клас unknown."""
    тека = pathlib.Path(sys.argv[1]); свідок = json.loads((тека / 'ж-05085.json').read_text())
    в = свідок['records'][0]; шлях = тека / в['local_photo']
    with шлях.open("rb") as файл: sha = hashlib.file_digest(файл, "sha256").hexdigest()
    assert sha == json.loads((тека / 'мета.json').read_text())['files_sha256'][шлях.name]
    оф = Ф.читати_yml(Ф.каталог_на_диску())[0]
    о = next(о for о in оф if о['id'] == свідок['id']); assert в['url'] in о['фото']
    фото = dict(url=в['url'], шлях=str(шлях), джерело='фід')
    # Підміна лише зовнішніх викликів: наявний запис маски/домінантного кластера.
    Ж.обрати_кадр = lambda *а: (0, None, {}, 'replay')
    Ж._запит = lambda *а, **к: {}
    Ж.виміряти_фото = lambda *а: (в['частка_маски'], [dict(слово=в['слово'], lab=_КОЛІР.точка_кольору(в), hex=_КОЛІР.hex_кольору(в), частка=в['частка'])], в['чому'], в['маска'], None)
    зап = Ж.обробити(о, [фото], 'replay', показ=False)['запис']; пр = зап['кадр_виміру']
    assert пр['sha256'] == sha and пр['клас'] == 'unknown' and пр['частка_маски'] == в['частка_маски']
    with Image.open(шлях) as кадр: assert пр["розмір"] == list(кадр.size)
    with tempfile.TemporaryDirectory() as тим:
        вхід, вихід = pathlib.Path(тим)/'input.json', pathlib.Path(тим)/'output.json.gz'
        вхід.write_text(json.dumps({о['id']: dict(запис=зап)})); Ж.ТУТ = тим
        Ж.злити(types.SimpleNamespace(вихід=str(вхід), злити_у=str(вихід)))
        з = json.loads(gzip.decompress(вихід.read_bytes()))[о['id']]
    кадри = К.кадри_речі(о, {}, {}, збагачення=з)
    assert з['кадр_виміру'] == пр and кадри[0] == в['url']
    assert not К.кадри_речі(dict(о, id=о['id']+'other'), {}, {}, збагачення=з)
    assert not К.кадри_речі(о, {}, {}, збагачення=dict(з, кадр_виміру=dict(пр, sha256=None)))
    assert К.стан_кадру_виміру(о, {})['стан'] == 'unknown'
    print(о['id'], sha, пр['розмір'], 'клас', пр['клас'], 'маска', пр['частка_маски'])
    print('producer→злиття→кадри: той самий кадр; чужий id/нема SHA → без фото; історія unknown')

if __name__ == '__main__':
    головна()
