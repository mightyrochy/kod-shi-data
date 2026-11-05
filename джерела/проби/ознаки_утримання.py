"""Оцінка не проходить порогів; утримання не є нулем, нульовий вимір є фактом."""
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import face_features as Ф
import colorspace as С
import вибір_палітри as В


def main():
    """Звіряє контракт утримання, фізичний контроль та звірку причини без факту."""
    F = С.features(С.hx("#aa9977"), С.hx("#aa9977"), С.hx("#5e775e"), джерело="model_hex")
    with patch.object(Ф, "рівень_контрасту", side_effect=AssertionError("поріг оцінки")):
        for назва in ("контраст", "очі", "шкіра", "волосся", "очі_кільце"):
            о = Ф.ознака_палітри(F, назва)
            assert not о["доступно"] and о["значення"] is None and о["джерело"] == "оцінка моделі"
        assert Ф.ознаки(F)["контраст"]["value_gap"] is None
    F["_meta"]["protocol"] = "spectro"
    к = Ф.ознака_палітри(F, "контраст")
    assert к["доступно"] and к["значення"] == 0 and к["рівень"] == "низький"
    for доступно, рівень, gap, очікування in ((False, "low", 0, False), (True, "unknown", 0, False),
                                            (True, "low", None, False), (True, "low", 0, True)):
        риса = dict(available=доступно, level=рівень, light_dark_gap=gap)
        assert В.ЗВІРКА_ПРИЧИН["why_her_contrast"]("scheme", None, {"особа": {"contrast": риса}})[0] == очікування
    assert Ф.підтон_палітри(F, самозвіт={"метал": "срібло"})["доступно"]
    print("утримання перед порогами, зміна джерела, нульовий вимір і причина: пройдено")


if __name__ == "__main__":
    main()
