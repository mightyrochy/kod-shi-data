"""Рядок 3315: скільки разів код ДОБРАВ сукню до образу, де вже був верх (а низу нема), у вердиктах
ЖИВІ-12 Б (`аудит/живі_12/Б/*/вердикти.txt`, усі руки). Запуск із теки `джерела`."""
import glob, json, os
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
усього = сукня = при_верху = 0
for ф in sorted(glob.glob(os.path.join(ТУТ, "..", "аудит", "живі_12", "Б", "*", "вердикти.txt"))):
    for р in open(ф, encoding="utf-8"):
        р = р.strip().rstrip(",")
        if not р.startswith('{"рука"'):
            continue
        д = json.JSONDecoder().raw_decode(р)[0]
        слот = {r["id"]: r.get("слот") for r in d_ if isinstance(r, dict)} if (d_ := д.get("речі_образу")) else {}
        усього += 1
        for в in (д.get("етапи") or {}).get("виклики") or []:
            for x in ((в.get("повнота") or {}).get("дібрані") or []):
                if x.get("слот") == "сукня":
                    сукня += 1
                    інші = {слот.get(i) for i in слот if i != x["id"]}
                    if "верх" in інші and "низ" not in інші:
                        при_верху += 1
                        print("  ", os.path.basename(os.path.dirname(ф))[:3], "рука", д["рука"], sorted(інші - {None}))
print("вердиктів %d · дібрана сукня %d · з них при наявному верху без низу %d" % (усього, сукня, при_верху))
