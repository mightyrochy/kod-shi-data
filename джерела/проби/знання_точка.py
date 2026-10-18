"""7503: точні посилання hx/hx_round2, нерівність, Lab-only і непрохід range."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import знання_речі as З
import знання_дріт as К
import colorspace as Ц


def головна():
    """Не втратити жодної цифри й не оголосити центр вікна виміром."""
    hex_ = "#bc9e81"
    точка = Ц.hx(hex_)
    for спосіб, стан, значення, поле in (
        ("hx", "measured", точка, dict(hex=hex_)),
        ("hx_round2", "measured", tuple(round(ч, 2) for ч in точка), dict(hex=hex_)),
        (None, "measured", (20, 1, 2), dict(hex=hex_)),
        ("identity", "measured", (20, 1, 2), dict(lab=(20, 1, 2))),
        (None, "range", (10, 30, 0, 5, None), dict(hex=hex_))):
        знання = З.знання({"тип": "dress_generic"})
        знання["color"].update(З.факт(стан, значення, "fixture"))
        річ = dict(n="point", **поле, **З.на_дріт(знання, має_точку=True))
        промпт = dict(task=dict(input=[]), items=[річ])
        дріт = К.ущільнити(промпт)
        назад = К.відновити(дріт)["items"][0]
        assert json.dumps(назад, sort_keys=True) == json.dumps(річ, sort_keys=True)
        значення_дроту = [ф[1] for ф in дріт["knowledge_legend"]["facts"]
                          if дріт["knowledge_legend"]["descriptors"][ф[0]][1] == "fixture"][0]
        assert (значення_дроту.get("conversion") if isinstance(значення_дроту, dict) else None) == спосіб
        print(стан, спосіб or "literal", "→ точний roundtrip")


if __name__ == "__main__":
    головна()
