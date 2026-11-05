"""Перевіряє вердикт кожної верхньої речі повного каталогу на семи смугах."""
import json
import os
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
os.chdir(КОРІНЬ / "джерела")
import feed as Ф
import міст_вхід as ВХ
import річ_з_фото as РФ
import сценарій as С


if __name__ == "__main__":
    вхід = json.loads(Path("стенд_вх.json").read_text(encoding="utf-8"))
    особа, тіло = ВХ.збірка(ВХ.нормалізувати_вхід(вхід))[:2]
    каталог = Ф.база_прогону(Ф.каталог_на_диску("каталог_повний.xml"), ліміт_фото=0)["каталог"]
    верхні = [р for р in каталог if р.get("слот") == "верхній_шар"]
    assert верхні, "у каталозі немає верхнього шару"
    збої, підказки, викликів = [], {}, 0
    for смуга in С.СМУГИ_ПОГОДИ:
        підказки[смуга] = 0
        for річ in верхні:
            try:
                в = РФ.вердикт(річ, особа, тіло, dict(нагода="робота", смуга_погоди=смуга))
                зн = [з for з in в["знахідки"] if з.get("правило") == "K-WEA-01"]
                assert bool(зн) == (смуга in ("warm", "hot"))
                assert all("°C" not in з["суть"] for з in зн)
                підказки[смуга] += len(зн)
            except Exception as збій:
                збої.append([річ.get("id"), смуга, type(збій).__name__, str(збій)])
            викликів += 1
    звіт = dict(каталог=len(каталог), верхніх=len(верхні), викликів=викликів,
                підказки=підказки, збоїв=len(збої), помилки=збої)
    print(json.dumps(звіт, ensure_ascii=False, indent=2))
    sys.exit(bool(збої))
