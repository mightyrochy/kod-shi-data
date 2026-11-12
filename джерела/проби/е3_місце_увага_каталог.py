# -*- coding: utf-8 -*-
"""R-CHEV-08 на всьому каталозі: скільки речей рухає кожна мета й чи рухає невідоме місце.
Запуск: cd джерела && python проби/е3_місце_увага_каталог.py [SHA_ДО]. Фото не завантажуються."""
if __name__ == "__main__":
    import collections, os, subprocess, sys, types
    from pathlib import Path
    ТУТ = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ТУТ)); os.chdir(ТУТ)
    import feed, фід_каталог as Ф, регістр_уваги as Р, outfit
    if len(sys.argv) > 1:
        Р = types.ModuleType("регістр_уваги_до")
        exec(compile(subprocess.check_output(["git", "show", sys.argv[1] + ":джерела/регістр_уваги.py"]), "регістр_уваги_до", "exec"), Р.__dict__)
    каталог = Ф.прочитати_каталог(feed.каталог_на_диску(), ліміт_фото=0)["каталог"]
    print("речей каталогу:", len(каталог), flush=True)
    for мета, зони in (("приховати", None), ("експресія", None), ("лестити", ["живіт"]), ("експресія", ["живіт"])):
        лічба = collections.Counter()
        for р in каталог:
            ранг = Р.ранг_уваги(р, мета, зони_мети=зони)
            лічба["уперед" if ранг < 0 else "назад" if ранг > 0 else "нерухомі"] += 1
            if зони and not set(зони) & set(outfit.зони_речі(р)[0] or ()):
                лічба["зона невідома"] += 1
                лічба["рух невідомого місця"] += ранг != 0
        print(мета, зони, dict(лічба), flush=True)
