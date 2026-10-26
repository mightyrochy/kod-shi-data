import sys, io, contextlib, json
sys.path.insert(0, sys.argv[1]+"/джерела")
with contextlib.redirect_stdout(io.StringIO()):
    import паспорт_нагоди as ПН
def j(**k): return json.dumps(k, ensure_ascii=False)
def пп(текст, сц, слова, досі=None):
    with contextlib.redirect_stdout(io.StringIO()):
        return ПН.паспорт_з_json(текст, сц, слова, паспорт_досі=досі)
к = lambda п: json.dumps((п.get("картка_запиту") or {}).get("нагода"), ensure_ascii=False)
a = пп(j(нагода="спорт"), {}, "йога зранку")
print("хід1:", a.get("нагода"), к(a), (a.get("звідки") or {}).get("occasion"))
b = пп(j(нагода="робота"), {}, "ні, я йду на роботу", досі=a)
print("хід2:", b.get("нагода"), к(b), (b.get("звідки") or {}).get("occasion"))
c = пп(j(), {}, "додай сумку", досі=b)
print("хід3 (порожня):", c.get("нагода"), к(c))
