"""Мірило наряду Е2-текст-жінці (вада 10 «питання анкети», 15409; keep_by «zone», 15491) на дереві `джерела`.
Запуск: python3 анкета.py <тека джерела>. Друкує переліки й останнім рядком числа.
1) Джерело: рядкові літерали (не докстрінги) модулів продукту `джерела/*.py` (без `тест_*`), що називають
   «анкету» — вільний текст правила про вхід, якого продукт у неї не питає (анкети в продукті нема).
2) Досяжність: знахідки правил, що несли такий текст (K-EYE-03, ворота розміру п'яти слотів без її виміру,
   `аксесуари_суд.без_входу`), — крізь дріт моделі (`дріт_моделі._знахідка`), «Оціни мій образ»
   (`оцінка_образу.перевірка_для_моделі`) і рядок картки (`внутрішня_мова.повідомлення("card_unchecked")`):
   скільки разів «анкета» доходить до моделі, і скільки заяв жінці про вхід без поля профілю.
3) keep_by: значення в описах заяв для моделі, яких не пише жоден писач (`zone`)."""
import ast, io, json, os, re, sys, tokenize, warnings
warnings.simplefilter("ignore")
Д = os.path.abspath(sys.argv[1]); sys.path.insert(0, Д); os.chdir(Д)
АНК = re.compile(r"\bанкет", re.I)
джерело = []
for ф in sorted(os.listdir(".")):
    if not ф.endswith(".py") or ф.startswith("тест"):
        continue
    код = open(ф, encoding="utf-8").read()
    докс = set()
    for в in ast.walk(ast.parse(код)):
        if isinstance(в, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and в.body \
                and isinstance(в.body[0], ast.Expr) and isinstance(getattr(в.body[0], "value", None), ast.Constant):
            докс.add(в.body[0].lineno)
    for т in tokenize.generate_tokens(io.StringIO(код).readline):
        if т.type == tokenize.STRING and АНК.search(т.string) and т.start[0] not in докс:
            джерело.append("%s:%d %s" % (ф, т.start[0], т.string.strip()[:110]))
print("== 1. джерело: літерали з «анкетою» (%d)" % len(джерело)); print("\n".join("  " + р for р in джерело))

import аксесуари_структура as АС, аксесуари_розмір as АР, аксесуари_суд as АСД
import дріт_моделі as ДМ, оцінка_образу as ОО, внутрішня_мова as ВМ, вердикт_моделі as ВД
зн = АС.рятівник_приобличчя({}, [{"слот": "верх"}], носій={"слот": "окуляри", "id": "о1", "назва": "окуляри"})[1]
for сл, сп in АР.АКСЕСУАР_ВИМІР.items():
    зн.append(АР.ворота_однієї(сл, сп, {"id": "р_" + сл, "слот": сл, "назва": сл, сп["поле"]: 1}, сл, {})[1])
зн += АСД.без_входу()
зн = [dict(з, ід="з%d" % і) for і, з in enumerate(зн)]
# справжній шлях до моделі: знахідки → рядки вердикту (`знахідки_вердикту`, той самий відсів, що в мосту й
# у `оцінка_образу._знахідки`) → дріт / «check» оцінки; картка — питання мосту (`міст_відповіді`) видом card_unchecked
вердикт = ВД.знахідки_вердикту(зн, "о1", {})[0]
дріт = [ДМ._знахідка(з) for з in вердикт]
оцінка = ОО.перевірка_для_моделі({"суд": {"findings": вердикт}})
# без відсіву вердикту — щоб видно було, що сам текст знахідки несе (сторож нижче, а не в тексті)
сирий = [ДМ._знахідка(з) for з in зн]
картка = [ВМ.повідомлення("card_unchecked", *(з.get("заяви") or [])) for з in зн]
до_моделі = [р for р in re.findall(r'"[^"]*"', json.dumps([дріт, оцінка], ensure_ascii=False)) if АНК.search(р)]
ЇЙ_НЕ_ПИТАЄ = {"glasses_pairs_count_unknown", "her_pupil_distance_unknown", "her_wrist_girth_unknown",
               "her_palm_girth_unknown"}
їй = sorted({(с["code"], шлях) for шлях, пп in (("дріт", дріт), ("оцінка", оцінка.get("findings") or []))
             for п in пп for с in п.get("statements") or [] if с["code"] in ЇЙ_НЕ_ПИТАЄ and с.get("recipient") != "journal"}
            | {(с["code"], "картка") for к in картка if к for с in к["statements"]
               if с["code"] in ЇЙ_НЕ_ПИТАЄ and с.get("recipient") != "journal"})
ремонти = sorted({str(з.get("ремонт")) for з in зн if АНК.search(str(з.get("ремонт")) + str(з.get("ламається")))})
сирі_їй = sorted({с["code"] for п in сирий for с in п.get("statements") or []
                  if с["code"] in ЇЙ_НЕ_ПИТАЄ and с.get("recipient") != "journal"})
print("== 2. досяжність: знахідок %d (у вердикт пройшло %d); «анкета» в ремонті/ламається знахідок %d; до моделі "
      "(дріт + оцінка) %d; заяв жінці про вхід без поля профілю %d; без відсіву вердикту (дріт сирих знахідок) — %s"
      % (len(зн), len(вердикт), len(ремонти), len(до_моделі), len(їй), сирі_їй or "—"))
print("\n".join("  ремонт: " + р[:140] for р in ремонти)); print("\n".join("  їй: %s · %s" % х for х in їй))
кб = sorted(к for к, в in ВМ.ЗАЯВИ.items() if re.search(r"keep_by[^)]*\bzone\b", str(в)))
print("== 3. keep_by: опис для моделі називає zone, якої не пише ніхто: %s" % (кб or "—"))
print("ПІДСУМОК: джерело %d · знахідки з «анкетою» %d · до моделі %d · заяв жінці без поля %d · описів keep_by із zone %d"
      % (len(джерело), len(ремонти), len(до_моделі), len(їй), len(кб)))
