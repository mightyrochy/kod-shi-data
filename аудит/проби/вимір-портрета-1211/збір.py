"""Збір відкритих портретів з Wikimedia Commons (ліцензія з extmetadata) — лише в /tmp, у репозиторій не йдуть."""
import json, os, re, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "PortraitProbe/0.1 (research script)"}
ЛЮДИ = ["Judi Dench", "Helen Mirren", "Viola Davis", "Lupita Nyong'o", "Morgan Freeman", "Kofi Annan",
        "Priyanka Chopra", "Penélope Cruz", "Christine Lagarde", "Oprah Winfrey", "Cate Blanchett",
        "Chimamanda Ngozi Adichie", "Toni Morrison", "Jane Goodall", "Whoopi Goldberg", "Michelle Obama"]
ВИХ = "/tmp/набір/фото"
def get(url, raw=False):
    for спроба in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read()
                return b if raw else b.decode("utf-8")
        except Exception as e:
            print("  повтор", спроба, str(e)[:80], file=sys.stderr); time.sleep(5 * (спроба + 1))
    return None
опис = {}
for л in ЛЮДИ:
    html = get("https://commons.wikimedia.org/wiki/Category:" + urllib.parse.quote(л.replace(" ", "_")))
    if not html:
        continue
    файли = []
    for ф in re.findall(r'href="/wiki/(File:[^"#?]+\.(?:jpe?g|JPE?G))"', html):
        ф = urllib.parse.unquote(ф)
        if ф not in файли:
            файли.append(ф)
    файли = файли[:24]
    інфо = []
    for i in range(0, len(файли), 12):
        q = urllib.parse.urlencode(dict(action="query", format="json", prop="imageinfo", iiprop="url|extmetadata|size",
                                        iiurlwidth=900, titles="|".join(файли[i:i + 12])))
        js = get("https://en.wikipedia.org/w/api.php?" + q)
        if not js:
            continue
        for p in json.loads(js)["query"]["pages"].values():
            ii = (p.get("imageinfo") or [{}])[0]
            м = ii.get("extmetadata") or {}
            інфо.append(dict(файл=p["title"], url=ii.get("thumburl"), ліцензія=(м.get("LicenseShortName") or {}).get("value"),
                             дата=(м.get("DateTimeOriginal") or {}).get("value", "")[:40]))
        time.sleep(1)
    тека = os.path.join(ВИХ, re.sub(r"\W+", "_", л))
    os.makedirs(тека, exist_ok=True)
    взято = []
    for n, і in enumerate(інфо):
        if not і["url"] or not і["ліцензія"] or not re.search(r"CC|Public domain|PD", і["ліцензія"], re.I):
            continue
        b = get(і["url"], raw=True)
        if not b:
            continue
        шлях = os.path.join(тека, "%02d.jpg" % n)
        open(шлях, "wb").write(b)
        взято.append(dict(і, шлях=шлях))
        time.sleep(1)
    опис[л] = взято
    print(л, len(файли), "файлів;", len(взято), "завантажено", flush=True)
json.dump(опис, open(os.path.join(ВИХ, "опис.json"), "w"), ensure_ascii=False, indent=1)
