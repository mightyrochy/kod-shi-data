"""7503: безвтратний фактичний replacement у двох живих читачах."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import пакет_моделі as П
import уважний_вибір as У
import знання_дріт as К


def головна():
    """Справжні оцінка й турнір: кодоване знання відновлює кожне вхідне поле."""
    канон = lambda р: json.dumps(р, ensure_ascii=False, sort_keys=True)
    річ = П._річ_пулу(dict(id="candidate", тип="dress_generic", lab=(20, 1, 2)), {})
    вікно = П._річ_пулу(dict(id="fixed", тип="dress_generic", hex="#123456",
                            колір_не_вимір={"вікно": [10, 30, 0, 5, None]}), {})
    пак = dict(пул={"сукня": [річ]}, заміна={"ід": "old", "слот": "сукня", "речі": [
        dict(річ, id="old", слот="сукня"), dict(вікно, слот="шарф")]})
    штатна, перевірено = К.ущільнити, []

    def зі_свідком(дані, *арг):
        """Перехопити саме живий стиковий виклик, без ручної копії його читача."""
        дріт = штатна(дані, *арг)
        назад = К.відновити(дріт)
        назад[арг[0]][арг[1]].remove(К.ОПИС)
        assert канон(назад) == канон(дані)
        assert "/replacement/rejected" in дріт["knowledge_legend"]["sections"]
        перевірено.append(дріт["knowledge_legend"]["sections"])
        return дріт

    К.ущільнити = зі_свідком
    try:
        У.запити_оцінки(пак, {річ["н"]}, 1, 0)
        У.запити_турніру(пак, {"dress-1": [річ["н"]]}, {"dress-1"}, 1, 0)
    finally:
        К.ущільнити = штатна
    assert len(перевірено) == 2
    print("replacement: rejected/fixed_outfit + items/groups, 2 живі roundtrip без втрат")

if __name__ == "__main__": головна()
