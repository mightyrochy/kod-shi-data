"""Корінь Е2-частина-дня, крок 2 (г): записані перші ходи розмови крізь шов без моделі — що бачать читачі суду й дроту.
Паспорт → сцена (`з_показу`) → суд блиску вдень (`доповнення_судді`, K-KOH-06, річ із паєтками) і випадок стилістки
(`міст_стилістка._випадок`: чи є година на дроті). argv[1] — корінь дерева коду (типово — це)."""
import sys, os, json, glob, warnings, io, contextlib
warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(sys.argv[1] if len(sys.argv) > 1 else ТУТ, "джерела"))
import мовний_шар as М, паспорт_нагоди as ПН, суд_від_моделі as СВ, міст_стилістка as МС

ПАЄТКИ = [dict(id="p1", назва="Топ з паєтками", слот="верх", тип="top")]
лік = dict(записів=0, блиск_вдень=0, без_пори_з_годиною=0, година_на_дроті=0, пора_на_дроті=0)
for ф in sorted(glob.glob(os.path.join(ТУТ, "аудит/**/VIDPOVIDI/seed*_01_мовний_шар_хід_розмови.txt"), recursive=True)):
    т = open(ф, encoding="utf8", errors="replace").read().split("── ВІДПОВІДЬ", 1)[-1]
    т, ім = т[т.find("{"):т.rfind("}") + 1], os.path.relpath(ф, ТУТ).replace("/VIDPOVIDI/seed", " s")[:-30]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            п = М.паспорт_з_шару(М.прийняти_розмову(т)["внутрішня"], {}, слова_ходу=[])["паспорт"]
            н = ПН.з_показу({}, п)[0]
            блиск = any(з.get("правило") == "K-KOH-06" for з in СВ.доповнення_судді(ПАЄТКИ, н))
            дріт = МС._випадок(п, {})
    except Exception as e:                                      # запис не JSON — рядок, не падіння
        print(ім, "| виняток", type(e).__name__)
        continue
    лік["записів"] += 1
    лік["блиск_вдень"] += блиск
    лік["без_пори_з_годиною"] += н.get("година") is not None and not н.get("пора")
    лік["година_на_дроті"] += "start_hour" in дріт
    лік["пора_на_дроті"] += "part_of_day" in дріт
    print(ім, "| сцена година=%s пора=%s | блиск удень=%s | дріт: %s" % (
        н.get("година"), н.get("пора"), блиск, sorted(к for к in дріт if к in ("start_hour", "part_of_day"))))
print(json.dumps(лік, ensure_ascii=False))
