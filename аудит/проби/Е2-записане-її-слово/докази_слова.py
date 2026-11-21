"""Докази В2 (рішення менеджера 17:24 UTC 20.11): слова в розмові міняють рядок «записане» тим самим писачем паспорта,
що й рука. Три ходи с8 (записана відповідь моста, прохід 1): «пішки 20 хвилин» → «ні, пішки 30 хвилин» → «пішки не йду,
їду авто». Паспорт кожного ходу дає справжній `паспорт_з_шару` дельтою поверх паспорта досі; рядки малює справжній
показ (`знімок.js` РЕЖИМ=рядки). Без моста й платних викликів. Запуск з кореня:
python3 аудит/проби/Е2-записане-її-слово/докази_слова.py"""
import contextlib, io, json, os, subprocess, sys, tempfile

КОРІНЬ = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
sys.path.insert(0, os.path.join(КОРІНЬ, "джерела"))
with contextlib.redirect_stdout(io.StringIO()):
    import мовний_шар as м

ОБМІНИ = os.path.join(КОРІНЬ, "аудит/проби/Живий-через-міст/стенд/службове/с8_мінус_десять_сніг/обміни.jsonl")
ТЕКСТ = None
for рядок in (json.loads(л) for л in open(ОБМІНИ, encoding="utf-8")):
    try:
        х = json.loads(рядок["відповідь"])["content"][0]["text"]
    except (KeyError, ValueError, TypeError, IndexError):
        continue
    if '"update"' in х and рядок["прохід"] == 1:
        ТЕКСТ = х


def хід(поля, слова, досі):
    d = json.loads(ТЕКСТ)
    d["update"].update(поля)
    пр = m_ = м.прийняти_розмову(json.dumps(d, ensure_ascii=False))
    with contextlib.redirect_stdout(io.StringIO()):
        return м.паспорт_з_шару(пр["внутрішня"], {}, слова_ходу=слова, частини=пр["частини"], паспорт_досі=досі)["паспорт"]


СЛОВА = ["на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин", "ні, пішки 30 хвилин", "пішки не йду, їду авто"]
п1 = хід({}, СЛОВА[:1], None)
п2 = хід({"walk_min": {"quote": "пішки 30 хвилин", "value": 30}, "movement": {"quote": "пішки 30 хвилин", "value": "walk"}}, СЛОВА[:2], п1)
п3 = хід({"walk_min": {"quote": "пішки не йду", "value": 0}, "movement": {"quote": "їду авто", "value": "sit"}}, СЛОВА, п2)
ходи = {"хід1_20_хв": п1, "хід2_поправка_30_хв": п2, "хід3_не_йде_пішки": п3}
файл = os.path.join(tempfile.mkdtemp(), "ходи.json")
json.dump(ходи, open(файл, "w", encoding="utf-8"), ensure_ascii=False, default=str)
н = dict(os.environ, ПАСПОРТИ=файл, LBL="докази", РЕЖИМ="рядки", NODE_PATH="node_modules")
рядки = json.loads(subprocess.run(["node", os.path.join(КОРІНЬ, "аудит/проби/Е2-записане-її-слово/знімок.js")],
                                  cwd=os.path.join(КОРІНЬ, "джерела"), env=н, capture_output=True, text=True, check=True).stdout)
for к in ходи:
    print(к, "·", " | ".join("%s — %s" % (р["назва"], р["текст"]) for р in рядки[к]["рядки"] if р["поле"] in ("дорога_пішки_хв", "рух")) or "рядків нема")
