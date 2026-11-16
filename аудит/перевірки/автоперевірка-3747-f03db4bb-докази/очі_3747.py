"""Офлайн-контроль справжнього рендера картки 390×844 з фото RicaMare."""
import base64
import gzip
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
html = gzip.open(root / "zhnyvarka/фікстури/ricamare_3448.html.gz", "rt", encoding="utf-8").read()
soup = BeautifulSoup(html, "html.parser")
fixture = json.loads((root / "zhnyvarka/фікстури/ricamare_3448.json").read_text(encoding="utf-8"))
name = soup.select_one('h1[itemprop="name"]').get_text(" ", strip=True)
url = urljoin(fixture["url"], soup.select_one('.gallery__photos .j-gallery-link[data-href]')["data-href"])
photo = out / "ricamare-3448.jpg"
if not photo.exists():
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as resp:
        photo.write_bytes(resp.read())
data = "data:image/jpeg;base64," + base64.b64encode(photo.read_bytes()).decode()
packet = dict(в="ПОКАЗ-V1", збірка="f03db4bb", каталог="контроль рендера", профіль="Оля", розклад="1", картки=[
    dict(рука="1", текст="Сукня RicaMare.", речі=[dict(id="ricamare-3448", назва=name, ціна=0,
         фото=data, урл=fixture["url"], слот="сукня")], мітки=[], знахідки=[])])
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-gpu"])
    page = browser.new_page(viewport={"width":390,"height":844}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    template = Path(__file__).with_name("показ-3747.html").read_text(encoding="utf-8")
    page.route("https://review.test/", lambda route: route.fulfill(status=200, content_type="text/html", body=template))
    page.route("https://api.**/*", lambda route: route.abort())
    page.goto("https://review.test/", wait_until="domcontentloaded")
    page.wait_for_function("typeof рендер === 'function'")
    print("помилки старту:", errors, flush=True)
    page.wait_for_function("typeof document.getElementById('сцн-новий')?.onclick === 'function'")
    page.evaluate("packet => {П=packet; рендер();}", packet)
    page.locator("#к-0").scroll_into_view_if_needed()
    page.locator("#к-0 img").first.wait_for(state="visible")
    page.wait_for_function("[...document.querySelectorAll('#к-0 img')].some(x=>x.complete && x.naturalWidth>0)")
    page.screenshot(path=str(out / "після-390x844.png"))
    print(json.dumps(dict(фото=url, назва=name, viewport=[390,844], карток=page.locator('#картки .картка').count(),
                          фото_завантажено=page.locator('#к-0 img').first.evaluate('(x)=>[x.naturalWidth,x.naturalHeight]'),
                          помилки=errors, текст=page.locator('#к-0').inner_text()), ensure_ascii=False))
    browser.close()
