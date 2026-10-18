"""Реплей реальних речей С01 р1 / С02 р2 та заяв похоронних карток рядка 8241."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import внутрішня_мова as ВМ
import міст_відповіді as М
import траурний_регістр as Т
import знання_речі as З


def головна():
    """Порахувати хибні заяви до/після; відсів пулу не міняє факту образу."""
    сцени = json.loads(pathlib.Path(__file__).with_name("дані_знання_8241.json").read_text())
    до = після = 0
    for с in сцени:
        речі = [{"назва": р["name"], "тип": р.get("type"), "метал": None,
                 "слот": ВМ.ключ("slot", р["kind"])} for р in с["outfit"]]
        до += sum(з["code"] == "mourning_no_metal_near_face" for з in с["before"])
        виходи = []
        for знято in ({}, {"mourning_metal_near_face_not_chosen": 8}):
            з = М._нагода_трауру(речі, {"випадок": {"подія": True}, "знято": знято})
            коди = [з["code"] for з in з["повідомлення"]["statements"]]
            виходи.append(коди)
        assert виходи[0] == виходи[1], "пул не доводить факту образу"
        після += sum(к == "mourning_no_metal_near_face" for к in виходи[1])
        assert "mourning_only_dark_and_quiet" not in виходи[1]
        прикраса = next(р for р in речі if р["тип"] == "jewelry_generic")
        assert З.властивість(прикраса, "metal")["status"] == "unknown"
        print(с["scene"], "метал unknown; заяви", виходи[1])
    print("8241: неправдиві заяви", до, "→", після)
    assert до == 2 and після == 0
    assert Т.без_металу_біля_обличчя([{"тип": "ring", "метал": "gold"}])
    assert М._нагода_трауру([{"тип": "ring"}], {"випадок": {"подія": True}})["повідомлення"]["statements"][-1]["code"] == "mourning_no_metal_near_face"
    assert not Т.без_металу_біля_обличчя([{"тип": "earrings", "метал": "gold"}])
    assert not Т.без_металу_біля_обличчя([{"тип": "earrings", "метал": None}])


if __name__ == "__main__":
    головна()
