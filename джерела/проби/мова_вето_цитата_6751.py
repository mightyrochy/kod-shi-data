"""Межа коментаря без її слів (рядок 6751): replay записаних відповідей перекладача коментаря (`*вхід_коментар*`,
VIDPOVIDI живого прогону) через `прийняти_вхід` і `паспорт_з_коментаря`. Без моделі. Друкує по запису її коментар,
межі відповіді (з уривком / без), взяті межі, зняті (`незнайомі`) і що коментар долив у межі паспорта (`додано.вето`).
Запуск: python3 проби/мова_вето_цитата_6751.py <тека живого прогону>"""
import sys, os, re, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import мовний_шар as МШ

без_цитати = взято_без = долито = 0
for ф in sorted(glob.glob(os.path.join(sys.argv[1], "**", "*вхід_коментар*.txt"), recursive=True)):
    т = open(ф, encoding="utf8").read()
    пр, _, від = т.partition("── ВІДПОВІДЬ")
    п = json.loads(пр[пр.index("{"):].strip())
    від = від.split("\n", 1)[1]
    речі = {р["id"]: р.get("slot") for р in п.get("items") or []}
    сире, _ = МШ._обʼєкт(від)
    межі = сире.get("vetoes") or [] if isinstance(сире, dict) else []
    межі = [межі] if isinstance(межі, dict) else межі
    б = sum(1 for м in межі if not (isinstance(м, dict) and м.get("quote")))
    р = МШ.прийняти_вхід("verdict_comment", від, set(речі), речі, слова=п["her_comment"])
    взяті = р["внутрішня"].get("vetoes") or []
    д = МШ.паспорт_з_коментаря(р["внутрішня"], {})["додано"]["вето"]
    без_цитати += б; взято_без += sum(1 for м in взяті if not м.get("quote") and set(м) <= {"slot", "item_type"})
    долито += bool(д)
    print("==", os.path.relpath(ф, sys.argv[1]))
    print("  її слова:", п["her_comment"])
    print("  межі відповіді: %d (без quote %d) · взято: %s" % (len(межі), б, json.dumps(взяті, ensure_ascii=False)))
    print("  зняті:", [x for x in р["незнайомі"] if x.startswith("vetoes")], "· долито в паспорт:", д)
print("ПІДСУМОК: меж без quote у відповідях %d · взято меж на цілий вид без quote %d · записів, що долили межу %d"
      % (без_цитати, взято_без, долито))
