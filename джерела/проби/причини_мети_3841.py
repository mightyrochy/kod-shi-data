"""3841/4390: чинні мети, числа, дослівна цитата і означення на живому збирачі промпта."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge as Б, profile as П, міст_основи as О, дріт_моделі as Д
import пакет_моделі as М, збирач_промптів as З, розбір_відповідей as Р

def main():
    вх = json.load(open("стенд_вх.json", encoding="utf-8"))
    Ф, Т, зріст, к = Б._збірка(вх)
    for ваги in (None, {}, {"unknown": 1}, {"помітність": .5, "непомітність": .5},
                {"помітність": .6, "непомітність": .45}, {"помітність": 1},
                {"непомітність": 1}, {"комфорт": 1}, {"легкість_збирання": 1}, {"доречність": 1}):
        print(json.dumps(dict(weights=ваги, result=П.мета_з_ваг(ваги)), ensure_ascii=False))
    цитата = '  Жінка: “хочу уваги. K-IO-02 (цитата)”\n' + 'точна цитата ' * 20
    for мета, зони, слова, ваги in ((None, None, None, None), ("невідомо", None, None, None),
            ("експресія", None, цитата, None), ("приховати", ["живіт"], "сховати живіт", {"помітність": 1}),
            ("приховати", None, "не привертати уваги", None), ("вище", None, "вище", None)):
        п = О._пакет(Ф, Т, зріст, dict(к, мета=мета, мета_зони=зони, мета_слова=слова, ваги_цілей=ваги))
        л = п["людина"]; дріт = Д.людина(л)
        промпт = З.зібрати(М.СКЛАДАННЯ, dict(person=дріт, pool=[dict(n="fixture-id", name="Річ моделі")],
                                          outfits_wanted=1))
        коди = З.коди_заяв(промпт)
        print(json.dumps(dict(goal=л["мета"], reason=л["чому_мети"], quote=л.get("цитата_мети"),
                              wire=дріт, codes=коди, definitions=промпт["task"].get("statement_codes")), ensure_ascii=False))
    for кількість in (0, 1, 2):
        items = [dict(name="Річ моделі", slot=s, color_hex="#000000") for s in ("top", "bottom")[:кількість]]
        в = Р.перевірити_образ_моделі("", None, перелік=json.dumps(dict(items=items)))
        print(json.dumps(dict(count=len(в["розбір"]["речі"]), checked=в["перевірено"], reason=в.get("чому")), ensure_ascii=False))
if __name__ == "__main__":
    main()
