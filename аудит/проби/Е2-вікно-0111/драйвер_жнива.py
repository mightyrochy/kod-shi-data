"""Прогін жнив із вікном, нижчим за поріг звірки: звірка моделі (перезавантаження на 16384) вимкнена, модель завантажена рукою."""
import sys, os, json, io, urllib.request
sys.path.insert(0, os.path.abspath("джерела"))
журнал = sys.argv[1]
справжній = urllib.request.urlopen
class Обгортка(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def urlopen(зап, *а, **к):
    адреса = getattr(зап, "full_url", зап)
    в = справжній(зап, *а, **к)
    if "/chat/completions" not in str(адреса):
        return в
    байти = в.read()
    try:
        ужиток = json.loads(байти).get("usage")
    except ValueError:
        ужиток = None
    тіло = json.loads(зап.data)
    with open(журнал, "a", encoding="utf-8") as ф:
        ф.write(json.dumps(dict(max_tokens=тіло.get("max_tokens"), кадрів=sum(1 for б in тіло["messages"][0]["content"] if б["type"] == "image_url"),
                                usage=ужиток), ensure_ascii=False) + "\n")
    return Обгортка(байти)
urllib.request.urlopen = urlopen
import жнива_прогін as G
G.звірити_модель = lambda модель, потоки: (True, "звірку вимкнено драйвером: вікно задано рукою")
sys.argv = ["жнива_прогін.py"] + sys.argv[2:]
G.main()
