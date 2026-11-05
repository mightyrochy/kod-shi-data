"""Повторює записані відповіді побачення на базі й голові без викликів моделей."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ДЖ = Path(__file__).resolve().parents[1]
БАЗА = "ce3a1bb62628bb4b5f2509b184a1e96db6bc6ddd"


def історія(*арг):
    """Читає точний запис чи модуль з історії UTF-8."""
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
        відповідь = re.search(r"── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)", запис, re.S).group(1)
        р = М.прийняти_розмову(відповідь)
        п = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=["побачення в ресторані ввечері, о 19:30"])["паспорт"]
        н, _ = П.з_показу({}, п)
        ч = Суд.чеклісти([], [], **({"сонце": н.get("сонце")} if len(sys.argv) == 2 else {}))
        вих.append(dict(запис=ф, смуга=Ф.смуга_ошатності(н), брак=any(п["вхід"] == "сонце" and п["стан"] == "без входу" for п in ч["надлишок"])))
    print(json.dumps(вих, ensure_ascii=False))
elif __name__ == "__main__":
    # Історичні модулі й дані мають бути однієї версії: залежність із голови спотворює ДО.
    знімок = [ф for ф in історія("ls-tree", "-r", "--name-only", "--full-tree", БАЗА, "--", ".").splitlines() if Path(ф).parent.as_posix() == "джерела" and Path(ф).suffix in (".py", ".json", ".md")]
    with tempfile.TemporaryDirectory(prefix="сонце_до_") as тека:
        assert Path(тека).resolve().parent == Path(tempfile.gettempdir()).resolve()
        for ф in знімок:
            Path(тека, Path(ф).name).write_text(історія("show", БАЗА + ":" + ф), encoding="utf-8")
        до = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, тека, "до"], cwd=ДЖ).decode("utf-8"))
        після = json.loads(subprocess.check_output([sys.executable, "-X", "utf8", __file__, str(ДЖ)], cwd=ДЖ).decode("utf-8"))
    assert [р["смуга"] for р in до] == [р["смуга"] for р in після]
    assert all(not д["брак"] and п["брак"] for д, п in zip(до, після))
    print("Записів:", len(після), "· смуга незмінна:", [р["смуга"] for р in після], "· назване поле сонце:", sum(р["брак"] for р in до), "→", sum(р["брак"] for р in після))
