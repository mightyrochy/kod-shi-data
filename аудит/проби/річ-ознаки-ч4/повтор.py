"""Повтор дев'яти записаних профілів на базі та правці без мережі й моделі."""
import copy
import importlib
import json
import pathlib
import subprocess
import sys

К = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
БАЗА = "805178a37ecddde0dedee5800e512db9c04e3b25"
ІМЕНА = ("face_features", "face_contrast", "вибір_палітри", "помада", "колір_хрома",
         "суд_блиск", "міст_основи")


def повтор():
    """Звіряє утримання оцінок і зберігає результати фізичних джерел для порівняння."""
    import colorspace as cs
    import face_features as о
    import face_contrast as к
    import вибір_палітри as в
    import міст_вхід as м
    import помада as п
    import palette
    import bases
    import міст_основи as мо
    ряд = п.сходинки(мо.hex_lch)
    база = json.loads((К / "джерела/стенд_вх.json").read_text("utf-8"))
    фізичні, оцінки = [], []
    профілі = sorted((К / "аудит/проби/жінки").glob("*.json"))
    assert len(профілі) == 9
    for шлях in профілі:
        ж = json.loads(шлях.read_text("utf-8"))
        for дж in ("model_hex", "uncontrolled", "protocolized", "spectro"):
            F = м.features(dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж))[0]
            з = о.ознаки(F)
            контраст = з["контраст"]
            пер = dict(особа=контраст, палітри=dict(температура=palette.температура(F)))
            дріт = в._особа(F, пер)
            if дж != "model_hex":
                дріт = copy.deepcopy(дріт)
                for значення in дріт.values():
                    if isinstance(значення, dict):
                        значення.pop("source", None)
                        значення.pop("confidence", None)
            поділ = п.поділ(ряд, F, контраст)
            свій = п.свій("#b3202a", F, контраст)
            факт = dict(контраст=контраст, бік=з["бік_очей"], дріт=дріт,
                        для_моделі=о.для_моделі(з), опора=к.опора_стрибка(F),
                        світлота=к.value_обличчя(F), домінантність=к.домінантність(F),
                        поділ=поділ, свій=свій,
                        очі=в._до_очей(dict(ахром=False, hex="#947856"), F),
                        ранг=bases.ранг(F, {"чорний": ("#111111", "чорний")}, ["чорний"])[0])
            if дж != "model_hex":
                фізичні.append(факт)
                continue
            первісні = copy.deepcopy(F)
            помилки = dict(
                бік=з["бік_очей"].get("b_очей") is not None,
                світлота=факт["світлота"] is not None,
                опора=факт["опора"] is not None,
                домінантність=факт["домінантність"]["рід"] != "невідомо",
                поділ=поділ["є"], свій=свій["рекомендована"] is not None,
                дріт=any("family" in дріт.get(ключ, {}) for ключ in ("eyes", "hair", "skin")),
                дріт_контраст=дріт["contrast"]["light_dark_gap"] is not None,
                значення_моделі=any(р["value"] is not None for р in факт["для_моделі"].values()))
            # Вихід без шкіри означає брак виміру, а не фізичне чорне L*=0.
            if hasattr(о, "виміряні_риси"):
                assert "шкіра" not in о.виміряні_риси(F)
                assert F == первісні
                assert о.перевага_температури(F, {"метал": "срібло"})["джерело"] == "її слово"
            оцінки.append(dict(профіль=шлях.stem, порушення=помилки))
    return dict(фізичні=фізичні, оцінки=оцінки,
                порушень=sum(sum(з["порушення"].values()) for з in оцінки))


def межа():
    """Відтворює зовнішнього читача, якому потрібне числове поле контрасту."""
    import colorspace as cs
    import face_features as о
    import bases
    F = cs.features(cs.hx("#deb295"), cs.hx("#523321"), cs.hx("#735632"), джерело="model_hex")
    початкова = о._контраст
    def утриманий(риси, джерело):
        """Підставляє контракт невідомого контрасту лише в пам'яті цього досліду."""
        return dict(доступно=False, рівень="невідомо", значення=None, value_gap=None,
                    L_шкіри=None, джерело="оцінка моделі", довіра=0.0)
    try:
        о._контраст = утриманий
        о._КЕШ.clear()
        try:
            bases.ранг(F, {"чорний": ("#111111", "чорний")}, ["чорний"])
        except ValueError as помилка:
            return dict(читач="джерела/bases.py", помилка=str(помилка))
        raise AssertionError("зовнішній читач уже вміє утримання; переглянь знахідку")
    finally:
        о._контраст = початкова
        о._КЕШ.clear()


def main():
    """Виконує базу й голову в тих самих модулях, відновлюючи правку після порівняння."""
    модулі = {ім: importlib.import_module(ім) for ім in ІМЕНА}
    після = {ім: (К / "джерела" / (ім + ".py")).read_text("utf-8") for ім in ІМЕНА}
    try:
        for ім, модуль in модулі.items():
            до = subprocess.check_output(["git", "show", БАЗА + ":джерела/" + ім + ".py"], cwd=К).decode("utf-8-sig")
            exec(compile(до, модуль.__file__, "exec"), модуль.__dict__)
        було = повтор()
    finally:
        for ім, модуль in модулі.items():
            exec(compile(після[ім], модуль.__file__, "exec"), модуль.__dict__)
    стало = повтор()
    відмінності = [(і, к) for і, (а, б) in enumerate(zip(було["фізичні"], стало["фізичні"]))
                   for к in а if а[к] != б[к]]
    assert not відмінності, "поведінка фізичних джерел змінилась: " + repr(відмінності)
    assert стало["порушень"] == 0
    результат = dict(база=БАЗА, профілів=9, фізичних_випадків=len(стало["фізичні"]),
                     фізичні_тотожні=True, до=було["порушень"], після=стало["порушень"],
                     контракти=межа(), оцінки=стало["оцінки"])
    print(json.dumps(результат, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
