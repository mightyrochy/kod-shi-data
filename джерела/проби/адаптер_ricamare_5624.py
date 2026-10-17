"""Друкує факти одного actual HTML RicaMare 13.10 → v1 → чинний фід, без мережі."""
import gzip, hashlib, json, sys, tempfile
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела")]
import ricamare_сторінка as р
import складальник as с
import фід_розбір as ф


def main():
    """Звіряє той самий source, структурні втрати й контрольні пошкодження знімка."""
    тека = КОРІНЬ / "zhnyvarka/фікстури"
    м = json.loads((тека / "ricamare_3448.json").read_text(encoding="utf-8"))
    м["html"] = gzip.decompress((тека / м["html_file"]).read_bytes()).decode("utf-8")
    шапка, записи = с.читати_записи()
    до = next(з for з in записи if з["адреса"] == м["url"])
    після = р.розібрати(до, м, р.рецепт())
    with tempfile.NamedTemporaryFile(suffix=".xml") as файл:
        файл.write(с.скласти(шапка, [після]).encode("utf-8")); файл.flush()
        офери, _ = ф.читати_yml(файл.name, показ=False)
    о = офери[0]
    print("ДО → ПІСЛЯ", {к: [до[к], після[к]] for к in ("ід", "ціна", "доступність", "артикул")})
    print("SOURCE", м["знято"], м["sha256"], "кадри", len(до["кадри"]), "→", len(після["кадри"]), "опис", len(до["опис"]), "→", len(після["опис"]))
    print("ФІД", {к: о.get(к) for к in ("id_жниварки", "ціна", "available", "url", "опис", "колір_сирий")}, "розмір", о["параметри"].get("розміри"), "кадри", len(о.get("фото_сирі", [])))
    for назва, html in (("ru", м["html"].replace('lang="uk"', 'lang="ru"', 1)), ("нема Product", м["html"].replace('itemtype="https://schema.org/Product"', 'itemtype="https://schema.org/Thing"')), ("нема наявності", м["html"].replace('itemprop="availability"', 'data-unavailable="1"'))):
        проба = dict(м, html=html, sha256=hashlib.sha256(html.encode()).hexdigest())
        try:
            print("КОНТРОЛЬ", назва, р.розібрати(до, проба, р.рецепт())["доступність"])
        except ValueError as помилка:
            print("КОНТРОЛЬ", назва, str(помилка))
    return 0


if __name__ == "__main__":
    sys.exit(main())
