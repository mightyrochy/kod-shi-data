"""Частина кв1 (Річ-кадр-варіант): власник кадрів сторінки RicaMare — доказ `ricamare:сторінка` лише коли дані сторінки
називають один колір; кілька кольорів без зв'язку «варіант → кадр» — «невідомо». Фікстура `ricamare_3448` (два свотчі).
Запуск: python3 -W ignore джерела/проби/кадр_варіант_кв1_ricamare.py"""
import gzip, hashlib, json, re, sys
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka")]
import ricamare_сторінка as р, фід_власник_кадру as в

ф = json.loads((КОРІНЬ / "zhnyvarka/фікстури/ricamare_3448.json").read_text(encoding="utf-8"))
html = gzip.open(КОРІНЬ / "zhnyvarka/фікстури/ricamare_3448.html.gz", "rt", encoding="utf-8").read()


def власник(h):
    знімок = dict(url=ф["url"], html=h, знято="2026-10-13", sha256=hashlib.sha256(h.encode("utf-8")).hexdigest())
    старий = dict(схема="v1", адреса=ф["url"], параметри=[], ід="1")
    з = р.розібрати(старий, знімок, р.рецепт())
    п = {x[0]: x[1] for x in з["параметри"]}
    return з, json.loads(п["власник_кадру"]), п["id_магазину"]


def доказ(з, вл, ід):
    о = dict(id="1", url=з["адреса"], фото=з["кадри"], параметри=dict(id_магазину=ід, власник_кадру=json.dumps(вл, ensure_ascii=False)))
    return [в.доказ_варіанта(о, к) for к in з["кадри"]]


з, вл, ід = власник(html)
assert вл == "невідомо", "два кольори свотчів без зв'язку — невідомо"
один = re.sub(r'<a\s+class="\s*modification__item\s+modification__item--preview\s+modification__item--stockout.*?</a>', "", html, count=1, flags=re.S)
assert один != html
з, вл, ід = власник(один)
assert isinstance(вл, dict) and вл["джерело"] == "ricamare:сторінка", вл
д = доказ(з, вл, ід)
assert д and all(x and x["варіант"].startswith("ricamare:") and x["джерело"] == "ricamare:сторінка" for x in д), д
# без кольору активного свотча доказу нема
без = re.sub(r'(modification__item--active)', 'x', один)
assert власник(без)[1] == "невідомо"
print("кадр_варіант_кв1_ricamare: ОК (кадрів із доказом %d)" % len(д))
