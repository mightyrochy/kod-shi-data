"""Запис жнив → v1 → XML: повтор не додає двійника й не стирає невиміряний склад."""
import gzip, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import жниварка as ж
import складальник as с
from жнива_каталог import зібрати


def main():
    """Зіставляє незмінні ід й склад на повторному збиранні справжньої фікстури."""
    корінь = Path(__file__).resolve().parents[2]
    html = (корінь / "zhnyvarka/фікстури/bella_6975_20261017_raw.html").read_text(encoding="utf8")
    url = "https://bella-bicchi.com/catalog/palto-122344/"
    ф = ж.факти_з_картки(html, url, ж.рецепт_селекторів("bella-bicchi.com")); ф["url"] = url
    з = ж.канонічний_запис(ф, dict(домен="bella-bicchi.com"), "картка")
    з["склад"] = None
    шапка, записи = с.читати_записи()
    старий = next(р for р in записи if any(п[0] in ("Склад", "склад") for п in р["параметри"]))
    старий = dict(старий, адреса=з["url"]); ід = старий["ід"]
    склад = [п for п in старий["параметри"] if п[0] in ("Склад", "склад")]
    with tempfile.TemporaryDirectory() as жр:
        файл = Path(жр) / "сирі/store.jsonl"; файл.parent.mkdir()
        файл.write_text(json.dumps(dict(url=з["url"], стан="картка", дата="2026-10-29", записи=[з]), ensure_ascii=False) + "\n", encoding="utf8")
        _, після, л = зібрати(жр, шапка, [старий])
        assert л["оновлено"] == 1
        _, повтор, л2 = зібрати(жр, шапка, після.copy())
        assert len(після) == len(повтор) == 1 and після == повтор and після[0]["ід"] == ід
        assert all(п in після[0]["параметри"] for п in склад)
        _, круг = с.розібрати(с.скласти(шапка, після, {}))
        assert len(круг) == 1 and круг[0]["ід"] == ід
        print("ід 1 → 1; склад збережено:", len(склад), "оновлення:", dict(л), "повтор:", dict(л2))


if __name__ == "__main__":
    main()
