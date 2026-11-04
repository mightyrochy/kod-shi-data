"""Порівнює числові рішення читачів на збережених профілях без викликів моделей."""
import json
import gzip
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import colorspace as КС
import personal_palette as ПП
import face_features as ОБ
import outfit as О
import palette as П
import колір_образу as КО
from аксесуари_взуття import L_шкіри


def main():
    """Зберігає зріз модельних і фізичних профілів для порівняння ДО/ПІСЛЯ."""
    зрізи = []
    for шлях in sorted((КОРІНЬ / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text(encoding="utf-8"))
        for дж in ("model_hex", "spectro", "protocolized", "uncontrolled"):
            лаб = lambda v: [КС.hx(h) for h in v] if isinstance(v, list) else КС.hx(v)
            F = КС.features(лаб(ж["skin"]), лаб(ж["hair"]), лаб(ж["eyes"]), джерело=дж)
            особа = О.контраст_особи(F)
            палітра = ПП.палітра(F)
            регіони = КС.регіони(F)
            спектри = КС.spectra_by_feature(F, "analogous")
            сп = П.специфікація(F, "тональна", ["верх", "низ", "взуття", "сумка"])
            сп_якір = П.специфікація(F, "тональна", ["верх", "низ"], якір_тон="#31576b")
            макіяж = КС.додати_макіяж(F, "#a82e48")[0]
            запис = dict(профіль=шлях.stem, джерело=дж, палітра=палітра,
                          регіони=регіони, спектри=спектри,
                          слоти=сп["слоти"], якір=сп["якір_тон"],
                          обраний_якір=сп_якір["якір_тон"], контраст=сп["контраст_особи"],
                          L_ноги=L_шкіри(особа),
                          макіяж=ПП.палітра(макіяж)["макіяж"],
                          суд=КО.біля_обличчя([dict(річ="білий верх", near=0.9, площа=0.4,
                              L=96.0, lab=(96.0, 0.0, 0.0), виріз="закритий")], особа))
            зрізи.append(запис)
    assert зрізи, "нема збережених профілів"
    вихід = Path(sys.argv[1])
    текст = json.dumps(зрізи, ensure_ascii=False, indent=2)
    вихід.write_bytes(gzip.compress(текст.encode("utf8"), mtime=0) if вихід.suffix == ".gz" else текст.encode("utf8"))
    print("профілів:", len(зрізи), "джерел: 4; винятків: 0")


if __name__ == "__main__":
    main()
