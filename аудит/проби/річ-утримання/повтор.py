"""Повтор ж1–ж9: ознаки, дріт палітри, причини та порядок порад без моделі."""
import json
import os
from pathlib import Path
import sys

К = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
if os.environ.get("ОЗНАКИ_КОД"): sys.path.insert(0, os.environ["ОЗНАКИ_КОД"])
import міст_вхід as М
import міст_основи as О
import face_features as Ф
import вибір_палітри as В
import palette as П
import outfit as У
import brief as Б
import пакет_моделі as ПМ
import дріт_моделі as Д
import pipeline as КОНВЕЄР


def повтор():
    """Повертає повний зріз і перелік порушень інваріанта входу моделі."""
    база = json.loads((К / "джерела/стенд_вх.json").read_text("utf8"))
    профілі = sorted((К / "аудит/проби/жінки").glob("*.json"))
    assert len(профілі) == 9, "потрібні всі ж1–ж9"
    записи, помилки = [], []
    for шлях in профілі:
        ж = json.loads(шлях.read_text("utf8"))
        for дж in ("model_hex", "spectro"):
            F = М.features(dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж))[0]
            к = У.контраст_особи(F)
            основи = О.основи(F)
            розв = П.розвилка(к, явні=П.ПОЗА_ЩОДЕННИМ)
            палітри = dict(контраст_рівень=розв["контраст_рівень"], температура=П.температура(F),
                          ознаки_обличчя=Ф.ознаки(F))
            пер = dict(особа=к, палітри=палітри, основи_кольорів=основи)
            особа = В._особа(F, пер)
            людина = Д.людина(ПМ.людина_для_пакета(None, палітри))
            відношення = [В._до_очей(dict(ахром=False, hex="#436147"), F),
                          В._до_очей(dict(ахром=True), F)]
            причини = {код: В.ЗВІРКА_ПРИЧИН[код]("scheme", None, dict(особа=особа))[0]
                       for код in ("why_her_contrast", "why_her_undertone", "why_her_hair")}
            запис = dict(профіль=шлях.stem, джерело=дж, особа=особа, людина=людина,
                         відношення=відношення, причини=причини,
                         основи=[р["ключ"] for р in основи["рекомендовані"]],
                         схеми=[р["схема"] for р in розв["гілки"]])
            записи.append(запис)
            if дж != "model_hex":
                continue
            перевірки = dict(
                ворота=not КОНВЕЄР.підготувати(F, форма_повна=False)["особа"]["гейт_джерела"]["можна_стверджувати"],
                контраст=особа.get("contrast", {}).get("light_dark_gap") is None
                    and особа.get("contrast", {}).get("level") in (None, "unknown", "withheld"),
                походження=all((особа.get(к) or {}).get("source") == "model_hex"
                              for к in ("contrast", "eyes", "hair", "skin")),
                класи_рис=all(not any((особа.get(к) or {}).get(п) is not None
                                   for п in ("family", "lightness", "chroma"))
                              for к in ("eyes", "hair", "skin")),
                вісь=(особа.get("axes") or {}).get("lightness") in (None, "withheld"),
                пакет=людина.get("contrast") in (None, "unknown", "withheld"),
                причини=not any(причини.values()),
                очі=not any(відношення),
                дріт=Ф.для_моделі(Ф.ознаки(F))["contrast"].get("value") is None,
            )
            помилки.extend([шлях.stem, назва] for назва, ок in перевірки.items() if not ок)
    for дуга in (None, (340, 20)):
        колір, вільний = Б.колір_слота(dict(L=[25, 65], C=[15, 35], дуга_тону=дуга))
        if дуга is None and (колір is not None or not вільний):
            помилки.append(["слот", "вільний тон став hex"])
        if дуга and (not колір or вільний):
            помилки.append(["слот", "зник фіксований тон"])
    return dict(записи=записи, порушень=len(помилки), помилки=помилки)


if __name__ == "__main__":
    результат = повтор()
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(результат, ensure_ascii=False, indent=2), "utf8")
    print(json.dumps(dict(профілів=len(результат["записи"]), порушень=результат["порушень"]), ensure_ascii=False))
    sys.exit(bool(результат["порушень"]) if "--перевірити" in sys.argv else 0)
