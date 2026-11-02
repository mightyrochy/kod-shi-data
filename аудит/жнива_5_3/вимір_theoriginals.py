"""ДО/ПІСЛЯ theoriginals у v1 (ДО — з HEAD): адреси, повтори, /ru/ /en/, склад."""
import gzip, io, json, re, subprocess, collections
def load(b): return [json.loads(l) for l in io.TextIOWrapper(b, encoding="utf-8")][1:]
нов = load(gzip.open("каталог_записи_v1.jsonl.gz"))
стар = load(gzip.GzipFile(fileobj=io.BytesIO(subprocess.check_output(["git", "show", "HEAD:каталог_записи_v1.jsonl.gz"]))))
норм = lambda а: re.sub(r"^https?://(www\.)?", "", re.sub(r"/(ua|ru|en)/", "/", а.lower())).rstrip("/")
for ім, д in (("ДО", стар), ("ПІСЛЯ", нов)):
    т = [р for р in д if "theoriginals.com.ua" in р["адреса"]]
    c = collections.Counter(норм(р["адреса"]) for р in т)
    print(ім, "theoriginals", len(т), "повторів", sum(v - 1 for v in c.values()), "зі складом", sum(any(п[0] == "склад" for п in р["параметри"]) for р in т),
          "/ru/ /en/", sum(bool(re.search(r"/(ru|en)/", р["адреса"])) for р in т))
ст = {норм(р["адреса"]) for р in стар}; нв = {норм(р["адреса"]) for р in нов}
print("зниклих старих адрес (за нормалізацією)", len(ст - нв), "усього записів", len(стар), "→", len(нов))
print("/ru/ /en/ усього", sum(bool(re.search(r"/(ru|en)/", р["адреса"])) for р in стар), "→", sum(bool(re.search(r"/(ru|en)/", р["адреса"])) for р in нов))
c = collections.Counter(норм(р["адреса"]) for р in нов); print("повторів усього", sum(v - 1 for v in c.values()))
