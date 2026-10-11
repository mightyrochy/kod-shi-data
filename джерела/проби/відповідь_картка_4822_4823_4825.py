# -*- coding: utf-8 -*-
"""Replay 4822/4823/4825: службовий текст не доходить до картки й «свідомих»."""
import sys; sys.path.insert(0, '.'); from оцінка_образу import прийняти_оцінку
from розбір_відповідей import _свідомі_з_json

суд = dict(образ=["c1"], запасні=[], зміни=[], рівень="clean", суд=dict(findings=[]),
           без_входу=[dict(input="occasion"), dict(input="temperature"),
                       dict(input="color_measure"),
                       dict(check="face", missing={"free_text": "контраст обличчя"},
                            what={"free_text": "перевірка контрасту"})])
для_оцінки = {
    "seed4_12": '{"answer":"Verdict: wear_with_change (item c1)","verdict":"unknown"}',
    "seed4_13": '{"answer":"answer: item c1","verdict":"unknown"}',
    "seed3_03": '{"answer":"Кольори поєднуються.","verdict":"unknown"}',
}
for імʼя, сире in для_оцінки.items():
    після = прийняти_оцінку(сире, суд)["картка"]
    print(імʼя, "ДО", сире)
    print(імʼя, "ПІСЛЯ", після)
    assert [х["текст"] for х in після["не_знаю"]] == ["Немає даних: нагода.", "Немає даних: температура.",
        "Немає даних: вимір кольору."]
    assert "c1" not in після["відповідь"]

assert прийняти_оцінку('{"answer":"This outfit works well; change nothing.","verdict":"unknown"}', суд)["картка"]["відповідь"]
assert not прийняти_оцінку('{"answer":"Так, товар p1 пасує","verdict":"unknown"}', суд)["картка"]["відповідь"]

словник = {"c1": {"id": "c1", "назва": "Сукня"}}
for текст in ("Wait, #464 is already in the list…", "Зачекай, #464 вже є у списку…"):
    відкинуті = []
    після = _свідомі_з_json([dict(чому=текст)], словник, поза=відкинуті)
    print("лог 291–299 ДО", текст)
    print("лог 291–299 ПІСЛЯ", після, відкинуті)
    assert not після and відкинуті
