"""Звіряє вузький рецепт Alot на двох справжніх HTML, без мережі."""
import hashlib
import json
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
import жниварка as ж


def main():
    """Порівнює старий резерв і рецепт із фактичним блоком та перевіряє SHA256."""
    тека = Path(__file__).with_name("дані_6977")
    мета = json.loads((тека / "мета.json").read_text(encoding="utf-8"))
    сел = ж.рецепт_селекторів("alot.com.ua")
    старі = {к: з for к, з in сел.items() if к != "опис"}
    лічба = [0, 0]
    for запис in мета["картки"]:
        сире = (тека / (запис["ід"] + ".html")).read_bytes()
        assert hashlib.sha256(сире).hexdigest() == запис["sha256"]
        html = сире.decode("utf-8")
        вузли = ж.BeautifulSoup(html, ж.ПАРСЕР_HTML).select('#tab-description > div[itemprop="description"]')
        assert len(вузли) == 1
        еталон = ж._текст(вузли[0], 8000)
        до = ж.факти_з_картки(html, запис["url"], старі)
        після = ж.факти_з_картки(html, запис["url"], сел)
        assert після["є_товар"] and після["опис"] == еталон and еталон
        лічба = [лічба[0] + bool(до["опис"]), лічба[1] + bool(після["опис"])]
        print(запис["ід"], запис["utc"], "байт", len(сире), "ДО→ПІСЛЯ",
              len(до["опис"] or ""), len(після["опис"]), "незмінний", до["опис"] == після["опис"])
    print("Описів на тих самих actual HTML:", *лічба, "; історичні341→341 НЕ ВИМІРЯНО")


if __name__ == "__main__":
    main()
