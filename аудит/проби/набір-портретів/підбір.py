"""Як складено `набір.json` (запускалось один раз 19.11.2026 UTC; щоб перескласти — нижче; щоденно не потрібне: набір бере `збір.py`).

Джерело — Wikimedia Commons, категорії офіційних портретів членів Конгресу США (`Official portraits of members of the
115th/116th/117th/118th United States Congress`): студійні кадри «одне обличчя, велике, рівне світло», твір федерального
уряду — ліцензія «Public domain» (з `extmetadata`, невідкриту не беремо). Другий знімок тієї самої людини — з іншого
скликання (інша зйомка й світло). Брали жінок (стилістка — для жінок): за першим іменем зі списку.

    PIP_DIR=<тека з opencv-python-headless<5, Pillow, numpy> python3 -I підбір.py <робоча тека>

Етапи (кеш у робочій теці — повторний запуск продовжує): 1) пошук файлів категорій + ліцензія/автор/мініатюра 640 px (450 px,
коли оригінал вужчий: Commons віддає такий оригінал з `upload.wikimedia.org`, який лімітує жорсткіше); 2) завантаження й
ворота — `вимір-портрета-1211/вимір.py` (`зони`: обличчя, більше чверті кадру; `портрет_вимір.виміряти`: ворота щік); 3) `набір.json`:
люди з ≥2 виміряними кадрами, усі завантажені їхні кадри з станом виміру. Запити — повільно, на 429 чекаємо `Retry-After`."""
import hashlib, importlib.util, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
ТУТ = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("PIP_DIR"): sys.path.insert(0, os.environ["PIP_DIR"])
UA = {"User-Agent": "PortraitProbe/0.1 (research script)"}
КАТЕГОРІЇ = ["Official portraits of members of the %dth United States Congress" % n for n in (115, 116, 117, 118)]
ЖІНОЧІ_ІМЕНА = set("""Abigail Alexandria Angie Anna Ashley Ayanna Betty Brittany Carol Carolyn Claudia Connie Cori Deborah Diana Elaine Elise
Elissa Haley Ilhan Jackie Jacky Jasmine Jennifer Jill Julia Kat Kathy Katie Lauren Lisa Lizzie Lois Lori Marie Marilyn Marjorie
Martha Mary Michelle Nicole Nikema Norma Pramila Rashida Robin Rosa Sara Sheila Stephanie Teresa Val Vicky Victoria Yvette
Maggie Maxine""".split())
_ост = [0.0]
def дістати(url, пауза=1.5):
    for _ in range(60):
        чекати = _ост[0] + пауза - time.time()
        if чекати > 0: time.sleep(чекати)
        _ост[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return r.read()
        except urllib.error.HTTPError as е:
            if е.code not in (429, 500, 502, 503, 504): return None
            time.sleep(int(е.headers.get("Retry-After") or 20) + 2)
        except OSError: time.sleep(10)
    return None
def api(**к):
    b = дістати("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(dict(format="json", **к)))
    return json.loads(b) if b else {}
def пошук(тека):
    шлях = os.path.join(тека, "кандидати.json"); кеш = json.load(open(шлях)) if os.path.exists(шлях) else {}
    файли = {}
    for кат in КАТЕГОРІЇ:
        курсор = {}
        while True:
            r = api(action="query", generator="categorymembers", gcmtitle="Category:" + кат, gcmtype="file", gcmlimit=50,
                    prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=640, **курсор)
            for p in r.get("query", {}).get("pages", {}).values():
                ii = (p.get("imageinfo") or [{}])[0]; м = ii.get("extmetadata") or {}
                if not ii.get("thumburl") or not re.search(r"\.jpe?g$", p["title"], re.I): continue
                if not (м.get("LicenseShortName") or {}).get("value", "").startswith("Public domain"): continue
                файли[p["title"]] = dict(файл=p["title"], url=ii["thumburl"], ліцензія=м["LicenseShortName"]["value"],
                                         автор=re.sub(r"<[^>]+>", "", (м.get("Artist") or {}).get("value", ""))[:80].strip(), сторінка=ii.get("descriptionurl"))
            if "continue" not in r: break
            курсор = r["continue"]
    люди = {}
    for ф in файли.values():
        н = re.sub(r"^(Rep\.|Sen\.|Senator|Representative) ", "", ф["файл"][5:])
        м = re.match(r"([A-ZÁ-Ž][\w'’.\-]+(?: [A-Z][\w'’.\-]+){1,3}?),? (?:\d{4} )?(?:official|congressional|portrait|\d+th|photo|-)", н, re.I)
        if м and м.group(1).split()[0] in ЖІНОЧІ_ІМЕНА:
            люди.setdefault(м.group(1).replace(" Portrait", "").replace(" Official", ""), []).append(ф)
    # оригінал вужчий за 640 px → мініатюра 450 px (хост мініатюр, не оригіналів)
    вузькі = [ф for фф in люди.values() for ф in фф if "upload.wikimedia.org" in ф["url"]]
    for i in range(0, len(вузькі), 50):
        r = api(action="query", prop="imageinfo", iiprop="url", iiurlwidth=450, titles="|".join(ф["файл"] for ф in вузькі[i:i + 50]))
        нові = {p["title"]: p["imageinfo"][0]["thumburl"] for p in r.get("query", {}).get("pages", {}).values() if p.get("imageinfo")}
        for ф in вузькі[i:i + 50]:
            if "thumb.wikimedia.org" in нові.get(ф["файл"], ""): ф["url"] = нові[ф["файл"]]
    кеш = {л: фф for л, фф in люди.items() if len(фф) >= 2}
    json.dump(кеш, open(шлях, "w"), ensure_ascii=False, indent=1)
    return кеш
def відбір(тека, кандидати):
    сп = importlib.util.spec_from_file_location("вим", os.path.join(ТУТ, "..", "вимір-портрета-1211", "вимір.py"))
    В = importlib.util.module_from_spec(сп); сп.loader.exec_module(В)
    from PIL import Image
    шлях = os.path.join(тека, "відбір.json"); рез = json.load(open(шлях)) if os.path.exists(шлях) else {}
    os.makedirs(os.path.join(тека, "ф"), exist_ok=True)
    for л, фф in sorted(кандидати.items(), key=lambda kv: sum("upload" in ф["url"] for ф in kv[1][:3])):
        if л in рез: continue
        рр = []
        for ф in sorted(фф, key=lambda x: "upload" in x["url"])[:3]:
            нм = os.path.join(тека, "ф", hashlib.sha1(ф["файл"].encode()).hexdigest()[:12] + ".jpg")
            if not os.path.exists(нм):
                b = дістати(ф["url"])
                if not b: continue
                open(нм, "wb").write(b)
            b = open(нм, "rb").read(); р = dict(ф, sha256=hashlib.sha256(b).hexdigest())
            img = Image.open(нм).convert("RGB"); з, чому = В.зони(img)
            if not з: р["стан"] = "пропуск: " + чому
            else:
                в = В.ПВ.виміряти({ім: В.вирізати(img, рамка) for ім, рамка in з.items()}); р["стан"] = в["стан"]
            рр.append(р)
        рез[л] = рр; json.dump(рез, open(шлях, "w"), ensure_ascii=False, indent=1)
    return рез
def маніфест(тека, рез):
    кадри, n = [], 0
    for л, рр in sorted(рез.items()):
        if sum(р["стан"] == "вимір" for р in рр) < 2: continue
        n += 1
        for k, р in enumerate(рр):
            кадри.append(dict(id="п%02d_%d" % (n, k + 1), людина="п%02d" % n, файл=р["файл"], url=р["url"], ліцензія=р["ліцензія"],
                              автор=р["автор"], сторінка=р["сторінка"], sha256=р["sha256"], стан_виміру=р["стан"]))
    json.dump(dict(джерело="Wikimedia Commons, офіційні портрети членів Конгресу США (115–118 скликання), Public domain",
                   зібрано="19.11.2026 UTC", кадри=кадри), open(os.path.join(ТУТ, "набір.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("людей", n, "кадрів", len(кадри))
if __name__ == "__main__":
    тека = sys.argv[1]; os.makedirs(тека, exist_ok=True)
    маніфест(тека, відбір(тека, пошук(тека)))
