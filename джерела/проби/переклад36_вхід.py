"""ПЕРЕКЛАД-36 (рядки 4683, 4687, 4689): що бачить мовна модель на вході перекладу опису руки 1–2 — ДО (записаний промпт
шару) і ПІСЛЯ (той самий опис: абзац `about_items` своїм текстом, біля речі — код кольору й «about it: text н=M»).
Аргументи — теки VIDPOVIDI записів. Друкує на кожен опис: речей, ДО (рядків переліку, кодів, зв'язків абзац↔річ),
ПІСЛЯ (те саме) і рядки переліку ПІСЛЯ."""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import мовний_шар as МШ

for тека in sys.argv[1:]:
    шари = {ф: ф.read_text() for ф in sorted(pathlib.Path(тека).glob("*мовний_шар.txt"))}
    for ф in sorted(pathlib.Path(тека).glob("*.txt")):
        т = ф.read_text()
        if '"about_items"' not in т.split("── ВІДПОВІДЬ")[-1] or '"outfit"' not in т:
            continue
        вх, _ = json.JSONDecoder().raw_decode(т[т.index('{"version"'):])
        відп, _ = json.JSONDecoder().raw_decode(т[т.index("{", т.index("── ВІДПОВІДЬ")):])
        речі, про = вх["outfit"]["items"], відп.get("about_items") or []
        if not про:
            continue
        до = next((с for с in шари.values() if про[0]["text"][:60] in с.split("── ВІДПОВІДЬ")[0]), "")
        до_п = до.split("── ВІДПОВІДЬ")[0]
        місце = {р["n"]: і for і, р in enumerate(речі)}
        тексти = {"про_річ.%d" % місце[а["n"]]: а["text"] for а in про if а.get("n") in місце}
        тексти["опис"] = (відп.get("answer_schema") or {}).get("text") or відп.get("text") or ""
        перелік = [dict(н=і + 1, назва=р["name"], колір=р.get("color"), hex=р.get("hex"),
                        **({"опис": "про_річ.%d" % і} if "про_річ.%d" % і in тексти else {})) for і, р in enumerate(речі)]
        пр = МШ.промпт(МШ.розмітити(тексти), перелік)
        рядки = [л for л in пр.splitlines() if re.match(r"\d+ — ", л)]
        print("%s/%s · речей=%d · ДО: перелік=%d кодів=%d зв'язків=%d · ПІСЛЯ: перелік=%d кодів=%d зв'язків=%d" % (
            ф.parent.parent.name, ф.name[:8], len(речі), len(re.findall(r"(?m)^\d+ — ", до_п)),
            до_п.count("colour code"), до_п.count("about it"), len(рядки),
            sum("colour code" in л for л in рядки), sum("about it" in л for л in рядки)))
        for л in рядки:
            print("   ", л)
