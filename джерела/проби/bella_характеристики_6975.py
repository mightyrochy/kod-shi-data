"""Друкує сирий baseline Bella та пари синтетичного DOM; НЕ вимір повторних жнив."""
import gzip
import hashlib
import sys
import xml.etree.ElementTree as Е
from pathlib import Path
К = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(К / "zhnyvarka"))
import жниварка as Ж


def main():
    """Звіряє передачу пар, межу рекомендацій і незмінні старі формати офлайн."""
    assert Ж.BeautifulSoup is not None, "Потрібна залежність beautifulsoup4"
    шлях = К / "zhnyvarka/фікстури/bella_6975_синтетична.html"
    тіло = шлях.read_bytes()
    селектори = Ж.рецепт_селекторів("bella-bicchi.com")
    ф = Ж.факти_з_картки(тіло.decode(), "https://bella-bicchi.com/catalog/fixture-6975/", селектори)
    очікувані = [["Поле А", "А & Б"], ["Поле Б", "В Г"], ["Поле В", "Д"]]
    print("СИНТЕТИЧНИЙ DOM, не HTTP/покриття: sha256", hashlib.sha256(тіло).hexdigest())
    print("пари", len(ф["характеристики_сирі"]), "очікується", len(очікувані), ф["характеристики_сирі"])
    assert ф["характеристики_сирі"] == очікувані
    assert селектори == {"характеристик": "div.properties-group__item, div.properties__item", "блок": ".catalog-detail"}
    старе = '<h1>fixture</h1><table><tr><td>Поле А</td><td>А</td></tr></table><dl><dt>Поле Б</dt><dd>Б</dd></dl><ul><li><span>Поле В</span><span>В</span></li></ul><p><b>Поле Г:</b> Г</p>'
    assert len(Ж.факти_з_картки(старе, "https://example.test/product/fixture", {"блок": "body"})["характеристики_сирі"]) == 4
    print("Старі формати table/dl/li/p: 4/4; зайві span, навігація, рекомендації та чужий блок відкинуті")
    with gzip.open(К / "каталог_повний.xml.gz", "rb") as вхід:
        каталог = Е.parse(вхід)
    офери = [о for о in каталог.iter("offer") if "bella-bicchi.com" in (о.findtext("url") or "")]
    ключів = sum(п.get("name") == "~Швидкий перегляд Ціна" for о in офери for п in о.findall("param"))
    print("Поточний RAW baseline: речей Bella", len(офери), "ключів", ключів, "; ПІСЛЯ повторних жнив НЕ ВИМІРЯНО")


if __name__ == "__main__":
    main()
