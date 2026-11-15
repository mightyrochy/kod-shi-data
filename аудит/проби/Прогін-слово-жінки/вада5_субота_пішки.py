"""Вада 5 повтором записаних обмінів: відповідь моделі ходу → прийняти_розмову → паспорт_з_шару; чи «слово» є в паспорті
й у словах картки (`подія`, `цитати_полів`, `решта`). argv: корінь_джерел обміни.jsonl.gz слово…"""
import sys, json, gzip
sys.path.insert(0, sys.argv[1])
import мовний_шар as М
слова_ходу, досі = [], None
for л in gzip.open(sys.argv[2], 'rt', encoding='utf8'):
    з = json.loads(л)
    try:
        т = json.loads(з["відповідь"])["content"][0]["text"]
        запит = json.loads(з["запит"])["messages"][0]["content"][-1]["text"]
    except Exception:
        continue
    if '"update"' not in т or 'You are the stylist of a styling app in a live chat' not in запит:
        continue
    вх = json.loads(запит[:запит.rindex('}') + 1])
    нове = ((вх.get("conversation_new") or вх.get("new_message") or {}) if isinstance(вх, dict) else {})
    р = М.прийняти_розмову(т)
    if not р.get("внутрішня") or not any(с in т for с in sys.argv[3:]):
        continue
    п = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=[x for x in sys.argv[3:]] + [json.dumps(вх, ensure_ascii=False)],
                         частини=р.get("частини"), не_записано_ходу=р.get("не_записано"))["паспорт"]
    картка = [п.get("подія")] + list((п.get("цитати_полів") or {}).values()) + list(п.get("решта") or [])
    for с in sys.argv[3:]:
        print("«%s»: у паспорті %s, у словах картки %s" % (с, с in json.dumps(п, ensure_ascii=False),
              any(с in json.dumps(x, ensure_ascii=False) for x in картка)))
    print("  рух:", п.get("рух"), "| подія:", п.get("подія"), "| цитати:", json.dumps(п.get("цитати_полів"), ensure_ascii=False)[:200])
    break
