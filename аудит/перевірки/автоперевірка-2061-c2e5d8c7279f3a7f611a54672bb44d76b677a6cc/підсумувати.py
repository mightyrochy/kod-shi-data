"""Звести лише завершені команди власної незалежної перевірки."""
import collections
import json
from pathlib import Path


def головна():
    """Звірити батарею, сім нових проб, AST та відомі відхилення без маскування кодів."""
    тека = Path(__file__).resolve().parent
    читати = lambda ім: json.loads((тека / ім).read_text(encoding="utf-8"))
    р = читати("результати.json")
    for x in р:
        x["журнал"] = (("середовище-" if x["режим"] == "ДО" else "первинне-")
                       if x["назва"] == "pal_K-PAL-16" else "") + x["режим"] + "-" + x["назва"] + ".txt"
    (тека / "результати.json").write_text(json.dumps(р, ensure_ascii=False, indent=2), encoding="utf-8")
    після = [x for x in р if x["режим"] == "ПІСЛЯ"]
    до = [x for x in р if x["режим"] == "ДО"]
    батарея = {"дим", "живий_шлях", "протокол", "розділи", "контракти", "показ"}
    ast = [x for x in після if x["назва"].startswith("поділ_")]
    нові = {режим: [x for x in р if x["режим"] == режим and x["назва"].startswith("колір_тип_213_")]
            for режим in ("ДО", "ПІСЛЯ")}
    історія = читати("історичні-результати.json")
    непередбачені = [x for x in після if x["код"] and x["назва"] != "pal_K-PAL-16"]
    непередбачені += [x for x in історія if x["код"] and x["назва"] not in {"колір_прози_шар", "колір_ярлик_hex"}]
    підсумок = dict(
        основна_серія={режим: dict(команд=len(xs), коди=dict(collections.Counter(x["код"] for x in xs)))
                       for режим, xs in (("ДО", до), ("ПІСЛЯ", після))},
        батарея=[dict(назва=x["назва"], код=x["код"]) for x in після if x["назва"] in батарея],
        AST=dict(усього=len(ast), успішних=sum(x["код"] == 0 for x in ast)),
        сім_нових_проб={режим: {x["назва"]: x["код"] for x in xs} for режим, xs in нові.items()},
        історичні=[dict(режим=x["режим"], назва=x["назва"], код=x["код"]) for x in історія],
        нейтралі=читати("нейтралі-300.json"),
        pal16_фіксовані=читати("pal16-порівняння.json"),
        непередбачені_відхилення=непередбачені)
    текст = json.dumps(підсумок, ensure_ascii=False, indent=2)
    (тека / "підсумок.json").write_text(текст, encoding="utf-8")
    print(текст)
    assert {x["назва"] for x in після if x["назва"] in батарея} == батарея
    assert all(x["код"] == 0 for x in після if x["назва"] in батарея)
    assert len(ast) == 14 and all(x["код"] == 0 for x in ast)
    assert all(len(xs) == 7 for xs in нові.values())
    assert all(x["код"] != 0 for x in нові["ДО"]) and all(x["код"] == 0 for x in нові["ПІСЛЯ"])
    assert len(історія) == 14 and підсумок["нейтралі"]["код"] == 0
    assert not непередбачені


if __name__ == "__main__":
    головна()
