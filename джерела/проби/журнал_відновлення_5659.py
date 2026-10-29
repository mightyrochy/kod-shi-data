"""5659: збережений HTML → cutoff 3→2 → тільки pending; HTTP статус — явно контрольний."""
import hashlib, json, re, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_5659_фікстура import Сторінка, прогін


def main():
    """Друкує факт по файлу-джерелу з аргументу, не завантажує його."""
    джерело = Path(sys.argv[1]); тіло = джерело.read_bytes(); html = тіло.decode("utf-8")
    url = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)[1]
    домен = __import__('urllib.parse', fromlist=['urlparse']).urlparse(url).netloc
    адреси = [url] + [u for u in dict.fromkeys(re.findall(r'href="(https://' + re.escape(домен) + r'/[^"#]+)"', html)) if u != url][:2]
    assert len(адреси) == 3
    рецепт = {"сімейство": "horoshop", "домен": домен, "старт": "https://" + домен, "пошук": "sitemap"}
    with tempfile.TemporaryDirectory(prefix="журнал5659-") as корінь:
        виклики = []; сторінка = Сторінка(url, тіло, виклики)
        сторінка.cutoff = True; до = прогін(корінь, рецепт, адреси + [url], сторінка, 3)
        файл = Path(корінь) / "сирі" / (домен + ".jsonl"); історія = файл.read_bytes()
        сторінка.cutoff = False; виклики.clear(); після = прогін(корінь, рецепт, None, сторінка, 3)
        assert до == після == {"total": 3, "done": 1, "pending": 2, "queue_complete": False, "source_complete": None}
        assert виклики == адреси[1:] and файл.read_bytes().startswith(історія)
        assert len(файл.read_text().splitlines()) == 3
        print(json.dumps({"джерело": str(джерело), "sha256": hashlib.sha256(тіло).hexdigest(),
            "URL": url, "cutoff": до, "resume": після, "повторно_готових": 0,
            "відновлено_лише_pending": len(виклики), "історія_збережена": True,
            "HTTP": 0, "статус_200": "контрольний, не фактичний HTTP", "DOM": "не вимірювали"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
