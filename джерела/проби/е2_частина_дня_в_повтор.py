"""Корінь Е2-частина-дня, крок 2 (в): записані перші ходи розмови крізь шов без моделі — вечір і світло, якими
судять сцена, погода й бриф (`день_кодами`, `потреба_події`, `формальність.сценарій`, `порада_з_випадку`).
argv[1] — корінь дерева коду (типово — це); з годиною чи порою — за сигнатурою дерева."""
import sys, os, json, glob, warnings, inspect
warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(sys.argv[1] if len(sys.argv) > 1 else ТУТ, "джерела"))
import мовний_шар as М, паспорт_нагоди as ПН, сценарій as СЦ, occasion as О, формальність as Ф, brief as Б
ПОРОЮ = "пора" in inspect.signature(Ф.сценарій).parameters
значення = lambda v: v.get("value") if isinstance(v, dict) else v
for ф in sorted(glob.glob(os.path.join(ТУТ, "аудит/**/VIDPOVIDI/seed*_01_мовний_шар_хід_розмови.txt"), recursive=True)):
    т = open(ф, encoding="utf8", errors="replace").read().split("── ВІДПОВІДЬ", 1)[-1]
    т, ім = т[т.find("{"):т.rfind("}") + 1], os.path.relpath(ф, ТУТ).replace("/VIDPOVIDI/seed", " s")[:-30]
    try:
        у = json.loads(т).get("update") or {}
        п = М.паспорт_з_шару(М.прийняти_розмову(т)["внутрішня"], {}, слова_ходу=[])["паспорт"]
        н = ПН.з_показу({}, п)[0]
        д, оп = СЦ.день_кодами(н), О.потреба_події(н)
        фс = Ф.сценарій(нагода=н.get("нагода"), **({"пора": н.get("пора")} if ПОРОЮ else {"година": н.get("година")}))
        мк = Б.порада_з_випадку("низький", н)
    except Exception as e:
        print(ім, "| виняток", type(e).__name__)
        continue
    print(ім, "| модель hour=%s part=%s" % (значення(у.get("hour")), значення(у.get("part_of_day"))),
          "| сцена година=%s пора=%s | день start_hour=%s part=%s light=%s until_night=%s | потреба=%s"
          " | формальність вечір=%s | макіяж=%s" % (
              н.get("година"), н.get("пора"), д.get("start_hour"), д.get("part_of_day"), д.get("light"),
              д.get("until_night"), оп["світло"], фс["вечір"], bool(мк)))
