"""6975: перевіряє доставлений raw HTML, а не покриття повторних жнив.
Джерело: claude/html-6977-1369@12fbdc7026373969d183818b259c8e5368e8087f,
аудит/html_1369/palto-stella-polare-raw.html; UTC 2026-10-17T16:10:26Z, HTTP200.
URL https://bella-bicchi.com/catalog/zhinoche-palto-stella-polare-122344/
"""
import hashlib
import sys
from pathlib import Path
К = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(К / "zhnyvarka"))
import жниварка as Ж


def main():
    """Звіряє SHA raw-входу, сирі пари та збереження двох матеріалів дослівно."""
    шлях = Path(sys.argv[1]) if len(sys.argv) > 1 else К / "zhnyvarka/фікстури/bella_6975_20261017_raw.html"
    тіло = шлях.read_bytes()
    відбиток = hashlib.sha256(тіло).hexdigest()
    assert len(тіло) == 782303 and відбиток == "aeef2de85c3752d34d2597ab845f8b447645f34e49c5e3f450b9aa7d0da62e3d"
    assert Ж.BeautifulSoup is not None, "Потрібна залежність beautifulsoup4"
    ф = Ж.факти_з_картки(тіло.decode(), "https://bella-bicchi.com/catalog/zhinoche-palto-stella-polare-122344/", Ж.рецепт_селекторів("bella-bicchi.com"))
    пари = dict(ф["характеристики_сирі"])
    print("ФАКТИЧНИЙ RAW", len(тіло), "sha256", відбиток, "пар", len(пари))
    assert len(пари) == 26
    верх = "альпака (alpaca) - 20%, вовна (wool) - 65%, поліамід (polyamide) - 15%"
    підкладка = "ацетат (acetate) – 48%, віскоза (viscose) – 52%"
    assert пари["Матеріал верху"] == верх and пари["Матеріал підкладки"] == підкладка
    assert ф["характеристики"]["склад"] == верх
    assert пари["Тип товару"] == "пальто вовняне" and пари["Сезон"] == "осінь, весна"
    print("Два матеріали збережено дослівно; повторних жнив каталогу НЕ БУЛО")


if __name__ == "__main__":
    main()
