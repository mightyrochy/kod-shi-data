"""Відтворення записаних коментарів на межі мова; аргументи — дерево джерел, JSON результату, режим номерів 0/1."""
import json
from pathlib import Path
import subprocess
import sys

def main():
    """Пропускає чотири записи крізь обране дерево коду й зберігає дані та паспорт."""
    sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
    import мовний_шар as М
    номери = bool(int(sys.argv[3]))
    результати = []
    for серія, сід in ((14, 34), (16, 36), (17, 36), (19, 33)):
        джерело = (f"origin/claude/zhyvi-{серія}:аудит/живі_{серія}/А/13_ж2_спорт_коментар/"
                   f"VIDPOVIDI/seed3_{сід}_мовний_шар_вхід.txt")
        коміт = subprocess.check_output(["git", "rev-parse", джерело.split(":", 1)[0]]).decode().strip()
        запис = subprocess.check_output(["git", "show", джерело]).decode("utf-8")
        промпт, відповідь = запис.split("── ВІДПОВІДЬ", 1)
        сирий, _ = М._обʼєкт(відповідь.split("\n", 1)[1])
        початок = промпт.index("[", промпт.index('"items"'))
        речі, _ = json.JSONDecoder().raw_decode(промпт[початок:])
        речі = [dict(id=р["id"], слот=р["slot"]) for р in речі]
        відповідність = {р["id"]: str(н) for н, р in enumerate(речі, 1)}
        if номери:
            сирий = dict(сирий, about_items=[dict(р, id=відповідність.get(р.get("id"), "чужий"))
                                           for р in сирий.get("about_items", [])])
        р = json.loads(М.мова(dict(вхід="verdict_comment", речі=речі,
                                  відповідь_моделі=json.dumps(сирий, ensure_ascii=False))))
        паспорт = М.паспорт_з_коментаря(р["внутрішня"], {"перекладено_шаром": True, "вето": {}})
        результати.append(dict(джерело=джерело, коміт_джерела=коміт, внутрішня=р["внутрішня"], паспорт=паспорт))
    чужий = json.loads(М.мова(dict(вхід="verdict_comment", речі=[dict(id="річ@крамниця", слот="взуття")],
        відповідь_моделі=json.dumps(dict(about_items=[dict(id="чужий", opinion="dislike", reasons=["heels"])])))))
    підсумок = dict(коментарі=результати, чужих_меж=len(чужий["внутрішня"].get("vetoes", [])))
    Path(sys.argv[2]).write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Записаних коментарів:", len(результати), "меж із чужого посилання:", підсумок["чужих_меж"])


if __name__ == "__main__":
    main()
