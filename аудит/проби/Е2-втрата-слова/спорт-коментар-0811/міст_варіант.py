"""Варіант відповіді перекладача коментаря (аргумент — JSON) → `мова` → `паспорт_з_коментаря` з паспортом сцени."""
import json, sys, pathlib
корінь = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(корінь / "джерела"))
import мовний_шар as М
вх = {"вхід": "verdict_comment", "слова": "взуття не моє, хочу без каблука і без принта",
      "речі": [{"id": "ж-04103@sezone.ua", "слот": "верх"}, {"id": "ж-07291@rito.ua", "слот": "низ"},
               {"id": "ж-09741@attico.ua", "слот": "взуття"}]}
м = lambda d: json.loads(М.мова(json.dumps(d, ensure_ascii=False)))
р = м(dict(вх, відповідь_моделі=sys.argv[2]))
print("внутрішня:", json.dumps(р.get("внутрішня"), ensure_ascii=False), "· незнайомі:", р.get("незнайомі"), "· причина:", р.get("причина"), "· повтор:", bool(р.get("повтор")))
д = м(dict({"коментар_з": р.get("внутрішня") or {}}, **({"паспорт": json.loads(sys.argv[3])} if len(sys.argv) > 3 else {})))
п = д.get("паспорт") or {}
print("не_ця:", д.get("не_ця"), "· додано:", json.dumps(д.get("додано"), ensure_ascii=False), "· вето_тверде:", json.dumps(п.get("вето_тверде"), ensure_ascii=False), "· чому:", д.get("чому"))
