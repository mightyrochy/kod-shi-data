"""Увесь каталог: допуск за місцем без суду кольору й носії K-ACC-07, ДО → ПІСЛЯ."""
def головна():
    """Зіставляє стару формулу допуску з записом місця на одному читанні каталогу."""
    import os, sys, json, collections, subprocess, types
    from pathlib import Path
    корінь = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / "джерела")); os.chdir(корінь / "джерела")
    import фід_каталог as ФК, feed as Ф, колір_річ as К, місце_речі as М
    import аксесуари_структура as А
    sha = "d911187265b4a2696df5dbb2d1665e1611339333"
    до = types.ModuleType("аксесуари_до")
    exec(subprocess.check_output(["git", "show", f"{sha}:джерела/аксесуари_структура.py"], encoding="utf-8"), до.__dict__)
    кат = ФК.прочитати_каталог(Ф.каталог_на_диску(), 0)["каталог"]
    print("Прочитано весь каталог:", len(кат), flush=True)
    до_ліч, після, слоти = collections.Counter(), collections.Counter(), collections.Counter()
    for р in кат:
        if not р.get("слот"):
            слоти["без слота"] += 1; continue
        слоти[р["слот"]] += 1
        # Формула K-CLR-02 / R-COL-16 бази: near елемента, а без виміру — таблиця слота.
        вага = р.get("near")
        if вага is None: вага = К.SLOT_NEAR_FALLBACK.get(р["слот"], 0.2)
        до_ліч["біля обличчя"] += вага >= К.NEAR_МІН
        бік = М.бік_межі(р)
        після["біля обличчя"] += бік is True
        після["далеко"] += бік is False
        після["невідомо"] += бік is None
        до_ліч["носій K-ACC-07"] += до.носій_приобличчевого_поля([р]) is not None
        після["носій K-ACC-07"] += А.носій_приобличчевого_поля([р]) is not None
    print(json.dumps(dict(мірило="допуск за місцем, без суду кольору", каталог=len(кат),
        ДО=dict(до_ліч), ПІСЛЯ=dict(після), слоти=dict(слоти)), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    головна()
