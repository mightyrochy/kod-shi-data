"""Порівнює записані відповіді мовної моделі на базі й голові без викликів моделей."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ДЖ = Path(__file__).resolve().parents[1]
БАЗА = "cbf3933a6ed0ddf838991f21cc19f65a1c724e9d"


def історія(*арг):
    """Читає модуль чи запис відповіді з точної бази UTF-8."""
    return subprocess.check_output(["git", *арг], cwd=ДЖ).decode("utf-8")


if __name__ == "__main__" and len(sys.argv) > 1:
    sys.path[:0] = [sys.argv[1], str(ДЖ)]
    import мовний_шар as М, паспорт_нагоди as П, суд_образу as Суд, формальність as Ф
    файли = історія("ls-tree", "-r", "--name-only", БАЗА, "--", "../аудит").splitlines()
    файли = [ф for ф in файли if "/ж2_побачення_вечір/" in ф and "/VIDPOVIDI/" in ф and "хід_розмови" in ф][-3:]
    assert файли
    вих = []
    for ф in файли:
        запис = історія("show", БАЗА + ":" + ф.removeprefix("../"))
        р = М.прийняти_розмову(re.search(r"── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)", запис, re.S).group(1))
        п = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=["побачення в ресторані ввечері, о 19:30"])["паспорт"]
        н, _ = П.з_показу({}, п)
        ч = Суд.чеклісти([], [], **({к: н.get(к) for к in ("господар", "креативне")} if len(sys.argv) == 2 else {}))
        брак = [п["вхід"] for п in ч["надлишок"] if п["вхід"] in ("господар", "креативне") and п["стан"] == "без входу"]
        вих.append(dict(запис=ф, смуга=Ф.смуга_ошатності(н), брак=брак))
    print(json.dumps(вих, ensure_ascii=False))
elif __name__ == "__main__":
    модулі = ("внутрішня_мова", "мовний_шар", "паспорт_поля", "перевірка_образу", "суд_огляд", "суд_чеклісти", "формальність", "оцінка_образу", "протокол", "сценарій", "дріт_моделі")
    with tempfile.TemporaryDirectory(prefix="контекст_до_") as тека:
        for ім in модулі:
            Path(тека, ім + ".py").write_text(історія("show", БАЗА + ":джерела/" + ім + ".py"), encoding="utf-8")
        до = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, тека, "до"], cwd=ДЖ).decode("utf-8"))
        після = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, str(ДЖ)], cwd=ДЖ).decode("utf-8"))
    assert [р["смуга"] for р in до] == [р["смуга"] for р in після]
    assert all(not д["брак"] and п["брак"] == ["господар", "креативне"] for д, п in zip(до, після))
    print("Записів:", len(після), "· смуга незмінна:", [р["смуга"] for р in після], "· названі поля:", [р["брак"] for р in після])
