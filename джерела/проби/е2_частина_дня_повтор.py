"""Корінь Е2-частина-дня, крок 1: записані перші ходи розмови (`аудит/**/VIDPOVIDI/seed*_01_мовний_шар_хід_розмови.txt`)
крізь шов без моделі — пора паспорта й `part_of_day`/`start_hour` дня рук. argv[1] — корінь дерева коду (типово — це)."""
import sys, os, json, glob, warnings
warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(sys.argv[1] if len(sys.argv) > 1 else ТУТ, "джерела"))
import мовний_шар as М, паспорт_нагоди as ПН, сценарій as СЦ


def цитати(x):
    if isinstance(x, dict):
        return ([x["quote"]] if isinstance(x.get("quote"), str) else []) + sum((цитати(v) for v in x.values()), [])
    return sum((цитати(v) for v in x), []) if isinstance(x, list) else []


значення = lambda v: v.get("value") if isinstance(v, dict) else v
for ф in sorted(glob.glob(os.path.join(ТУТ, "аудит/**/VIDPOVIDI/seed*_01_мовний_шар_хід_розмови.txt"), recursive=True)):
    т = open(ф, encoding="utf8", errors="replace").read().split("── ВІДПОВІДЬ", 1)[-1]
    т, ім = т[т.find("{"):т.rfind("}") + 1], os.path.relpath(ф, ТУТ).replace("/VIDPOVIDI/seed", " s")[:-30]
    try:
        у = json.loads(т).get("update") or {}
        п = М.паспорт_з_шару(М.прийняти_розмову(т)["внутрішня"], {}, слова_ходу=[" ".join(цитати(у))])["паспорт"]
        н = ПН.з_показу({}, п)[0]
        д, теми = СЦ.день_кодами(н), ПН.порада_коду(dict(н, пора=п.get("пора")), {}, всі=True)
    except Exception as e:                                      # запис не JSON — рядок, не падіння
        print(ім, "| виняток", type(e).__name__)
        continue
    print(ім, "| модель hour=%s part=%s" % (значення(у.get("hour")), значення(у.get("part_of_day"))),
          "| паспорт година=%s пора=%s | день start_hour=%s part=%s | вечірні теми=%s" % (
              п.get("година"), п.get("пора"), д.get("start_hour"), д.get("part_of_day"),
              sorted(x for x, _ in теми if x in ("мета", "макіяж"))))
