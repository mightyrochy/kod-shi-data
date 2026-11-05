"""Повтор записаних профілів: клас на виході моста, ранги основ і схеми палітри."""
import json, pathlib, sys
К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(К))
import міст_вхід as М, міст_основи as О, palette as П, colorspace as С, outfit as В


def main():
    """Друкує порівнюваний зріз на профілях ж1–ж9 без викликів моделей."""
    база = json.loads((К / "стенд_вх.json").read_text("utf8"))
    підсумок = []
    for шлях in sorted((К.parent / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text("utf8"))
        F = М.features(dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source="model_hex"))[0]
        основи = О.основи(F)
        підсумок.append(dict(профіль=шлях.stem, клас=основи["клас"], метал=основи["метал"],
            основи=[р["ключ"] for р in основи["рекомендовані"]],
            схеми=[р["схема"] for р in П.розвилка(В.контраст_особи(F))["гілки"]]))
    # Контрольна фікстура spectro: оливкова ознака й окремий її вибір металу.
    вимір = С.features(С.hx("#deb295"), С.hx("#523321"), С.hx("#735632"), джерело="spectro")
    олива = П.температура(вимір, самозвіт={"метал": "срібло"})
    assert олива["клас"] == "оливкова" and олива["метал"] == "срібло"
    print(json.dumps(підсумок, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
