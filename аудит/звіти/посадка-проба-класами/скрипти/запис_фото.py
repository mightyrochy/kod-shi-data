"""Галерея кожної речі одягу складів і пулів (верх, низ, сукня, комплект, верхній шар): усі кадри варіанта з
`каталог_записи_v1.jsonl.gz` (до 8), 640 px — моделі запису (той самий шлях, що `запис-речі-колір-с5/скрипти/фото.py`).
Поза репозиторієм: /tmp/пс/фото. Запуск з кореня."""
import gzip, io, json, os, pickle, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ОДЯГ = {"верх", "низ", "сукня", "комплект", "верхній_шар"}
Р = {р["id"]: р for р in pickle.load(open("/tmp/каталог_рядки.pkl", "rb"))}
ІДИ = [і for і in json.load(open("/tmp/пс/речі_запису.json")) if Р[і].get("слот") in ОДЯГ]
БУЛО = json.load(open("/tmp/пс/кадрів.json")) if os.path.exists("/tmp/пс/кадрів.json") else {}
ІДИ_ВСІ = ІДИ; ІДИ = [і for і in ІДИ if БУЛО.get(і, 0) <= 0]  # докачування: лише речі без кадрів
ПОТРІБНІ = {і.split("@")[0] for і in ІДИ}
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in ПОТРІБНІ: R[р["ід"]] = р
import time
def взяти(url):
    for спроба in range(5):
        try:
            з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(з, timeout=25) as в:
                І = Image.open(io.BytesIO(в.read())); І.load()
            return І.convert("RGB")
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(5 * (спроба + 1))
    raise RuntimeError("429")
def одна(ід):
    к = ід.split("@")[0]
    if к not in R: return ід, -1
    н = 0
    for url in [u for u in R[к]["кадри"] if u.startswith("http")][:8]:
        try: І = взяти(url)
        except Exception: continue
        if min(І.size) < 120: continue
        н += 1; І.thumbnail((640, 640)); І.save(f"/tmp/пс/фото/{к}-{н}.jpg", quality=82)
    return ід, н
with ThreadPoolExecutor(2) as п: рез = {**БУЛО, **dict(п.map(одна, ІДИ))}
json.dump(рез, open("/tmp/пс/кадрів.json", "w"), ensure_ascii=False)
print("речей", len(ІДИ_ВСІ), "нема в v1", sum(1 for н in рез.values() if н < 0), "без кадрів", sum(1 for н in рез.values() if н == 0), "кадрів", sum(н for н in рез.values() if н > 0))
