"""Друкує факти читання промптів фото проти справжніх читачів, без виклику моделі."""
import json
import sys
from pathlib import Path


def головна():
    """Порівнює обидва виклики й читачі на одному штучному описі сандалів."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
    import річ_з_фото as Р
    import оцінка_образу as О
    фото = [dict(ід="ф1", ширина=600, висота=900)]
    опис = dict(photo="ф1", name="White sandals", slot="bottom", kind="sandals", color="white",
                fabric="leather", cut=None, length=None, pattern="solid", formality="everyday",
                owner="unknown", in_outfit=True, frame=dict(left=100, top=100, right=900, bottom=900))
    def прочитати(о, оцінка):
        """Читає відповідь тим самим входом, що й відповідний міст."""
        вих = (О.речі_з_відповіді if оцінка else Р.речі_з_відповіді_фото)(json.dumps(dict(items=[о])), фото)
        return вих, вих["речі" if оцінка else "речі_з_фото"][0]
    for назва, промпт, оцінка in (("розмова", Р.промпт_фото(фото), False),
                                  ("оцінка", О.промпт_речей(фото), True)):
        п = json.loads(промпт)
        завдання = п["task"]
        вих, р = прочитати(опис, оцінка)
        print(назва, json.dumps(dict(правил=len(завдання["rules"]), полів_входу=len(завдання["input"]),
              лише_коди=any('Field values are only codes' in x for x in завдання["rules"]),
              поля_поза_кодами=[к for к in завдання["answer_schema"]["items"][0] if ("item_type" if к == "kind" else к) not in п["codes"]],
              причина=вих["причина"], назва=р["назва"], слот=р["слот"], рамка=р["рамка"]), ensure_ascii=False))
        хибні = dict(опис, kind="invalid_code", **{к: "invalid_code" for к in Р.коди_полів() if к not in ("item_type", "owner")})
        _, х = прочитати(хибні, оцінка)
        print("поза кодами →", [х[к] for к in ("вид", "слот", "колір", "матеріал", "крій", "довжина", "принт", "ошатність")])
        поле = "owner" if оцінка else "in_outfit"
        а, _ = прочитати(dict(опис, **{поле: "mine" if оцінка else False}), оцінка)
        print("зміна", поле, "не змінює результат читача:", а == вих)
    повтор = json.loads(Р.промпт_фото(фото, помилка="no_json_object"))
    print("повтор: format_error=", повтор["format_error"], "; останній опис входу=", повтор["task"]["input"][-1])


if __name__ == "__main__":
    головна()
