"""Порівнює контекст і смугу записаних відповідей на базі кроку та голові."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ДЖ = Path(__file__).resolve().parents[1]
БАЗА = "df1f1a2aa8c44d6cea23503cac049a5f8e219154"
ПОЛЯ = ("роль", "супутник_рівень", "сезон", "гардероб", "життєвий_перехід", "заявлений_злам", "тон_колготи", "заявлена_колона")


def історія(*арг):
    """Читає точні UTF-8 байти модуля чи запису з бази кроку."""
    return subprocess.check_output(["git", *арг], cwd=ДЖ).decode("utf-8")


if __name__ == "__main__" and len(sys.argv) > 1:
    sys.path[:0] = [sys.argv[1], str(ДЖ)]
    import мовний_шар as М, паспорт_нагоди as П, суд_образу as С, формальність as Ф
    файли = історія("ls-tree", "-r", "--name-only", БАЗА, "--", "../аудит").splitlines()
    файли = [ф for ф in файли if "/ж2_побачення_вечір/" in ф and "/VIDPOVIDI/" in ф and "хід_розмови" in ф][-3:]
    assert файли
    вих = []
    for ф in файли:
        запис = історія("show", БАЗА + ":" + ф.removeprefix("../"))
        р = М.прийняти_розмову(re.search(r"── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)", запис, re.S).group(1))
        п = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=["побачення в ресторані ввечері, о 19:30"])["паспорт"]
        н, _ = П.з_показу({}, п)
        ч = С.чеклісти([], [], **({"контекст": н} if len(sys.argv) == 2 else {}))
        вих.append(dict(смуга=Ф.смуга_ошатності(н), брак=[п["вхід"] for п in ч["надлишок"] if п["вхід"] in ПОЛЯ and п["стан"] == "без входу"]))
    print(json.dumps(вих, ensure_ascii=False))
elif __name__ == "__main__":
    модулі = [ім for ім in історія("ls-tree", "--full-tree", "-z", "--name-only", БАЗА + ":джерела").split("\0") if ім.endswith(".py")]
    assert модулі, "Git не дав жодного модуля бази"
    with tempfile.TemporaryDirectory(prefix="контекст_решта_до_") as тека:
        for ім in модулі: Path(тека, ім).write_text(історія("show", БАЗА + ":джерела/" + ім), encoding="utf-8")
        до = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, тека, "до"], cwd=ДЖ).decode("utf-8"))
        після = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, str(ДЖ)], cwd=ДЖ).decode("utf-8"))
    assert [р["смуга"] for р in до] == [р["смуга"] for р in після]
    assert all(not д["брак"] and set(п["брак"]) == set(ПОЛЯ) for д, п in zip(до, після))
    print("Записів:", len(після), "· смуга незмінна:", [р["смуга"] for р in після], "· названих входів:", 0, "→", sum(len(р["брак"]) for р in після))
