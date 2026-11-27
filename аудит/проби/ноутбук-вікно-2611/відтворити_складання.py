"""Відтворює 23 обірвані (max_tokens) виклики складання руки 1 з автоживого 344d840e на LM Studio зі стелею 4000.
«до» — промпт як записано; «після» / «після-з-відступами» — спроби вкоротити відповідь, які вимір не підтвердив і в коді
їх нема (тут вони цілком): «worn» лише на речі без факту типу + підказки «лише де щось каже», без «done» у складанні,
«після» — ще й стислий JSON. Друкує finish_reason, токени, «worn» і скільки образів прочитав суворий розбір.
Запуск з кореня: python <цей файл> до|після|після-з-відступами [до N [від M]] > рядки JSONL."""
import json, sys, time, urllib.request
from pathlib import Path
К = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(К / "джерела"))
import пакет_моделі as П, протокол as ПР
ЗАПИСИ = К / "аудит/проби/автоживий-344d840ef560b897461bbd29b378e1d25652fff4"
def обірвані():
    for ф in sorted(ЗАПИСИ.glob("*/VIDPOVIDI/обмін/*.json")):
        д = json.loads(ф.read_text(encoding="utf-8")); т = д["відповідь"].get("body", "")
        if д["запит"]["model"].startswith("qwen/") and '"stop_reason":"max_tokens"' in т and "outfits_wanted" in str(д["запит"]):
            yield ф, д["запит"]
МІСЦЯ = ("In «worn» name only the items whose kind does not already say where they are on her — not shoes, "
         "socks, tights, earrings, glasses, bracelets, rings, belts or bags.")
СТИСЛО, ТАК_НІ = "Write the JSON compactly: no indentation and no line breaks.", ", one of: yes, no"
ПІДКАЗКИ = {"visible_under_coat": "only for an item under an outer layer" + ТАК_НІ, "unbuttoned": "only for an outer layer"
            + ТАК_НІ, "words": "only what the answers above leave out, in a few words"}
def після(текст):
    і = текст.index('"answer_schema":') + len('"answer_schema":'); с, к = json.JSONDecoder().raw_decode(текст[і:])
    о, складання = с["outfits"][0], "Build outfits" in текст[:400]; о["worn"][0].update({к_: "<%s>" % п for к_, п in ПІДКАЗКИ.items()})
    if складання: о.pop("done", None)       # ремонт (вердикт) «done» має
    текст = текст[:і] + json.dumps(с, ensure_ascii=False, separators=(",", ":")) + текст[і + к:]
    якір = json.dumps(П.РЯДОК_ЛИШЕ_НОМЕР, ensure_ascii=False) + ","
    return текст if not складання else текст.replace(якір, якір + "".join(json.dumps(р, ensure_ascii=False) + "," for р in (МІСЦЯ, СТИСЛО)[:2 if варіант == "після" else 1]), 1)
варіант, межа, від = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 99, int(sys.argv[3]) if len(sys.argv) > 3 else 0
for ф, з in list(обірвані())[від:межа]:
    текст = "".join(б.get("text", "") for б in з["messages"][0]["content"] if б.get("type") == "text")
    текст = після(текст) if варіант.startswith("після") else текст
    кадри = [{"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (б["source"]["media_type"], б["source"]["data"])}}
             for б in з["messages"][0]["content"] if б.get("type") == "image"]       # кадри — як стенд, перед текстом
    тіло = {"model": з["model"], "messages": [{"role": "user", "content": кадри + [{"type": "text", "text": текст}]}], "max_tokens": 4000,
            "temperature": з.get("temperature", 1), "reasoning_effort": "none", "stream": False}
    п = time.time(); р = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions",
        json.dumps(тіло).encode(), {"content-type": "application/json"}), timeout=1800))
    в = р["choices"][0]; відп = в["message"].get("content") or ""; об, чому, _ = ПР.розбір_за_схемою(відп, "ОБРАЗИ_V1")
    print(json.dumps({"запис": str(ф.relative_to(ЗАПИСИ)).replace("\\", "/"), "варіант": варіант, "стеля_запису": з["max_tokens"],
        "finish": в["finish_reason"], "вхід": р["usage"]["prompt_tokens"], "вихід": р["usage"]["completion_tokens"],
        "образів": len((об or {}).get("образи") or []) if isinstance(об, dict) else 0, "чому": чому,
        "підписів": відп.count('"caption"'), "хотіли": int(__import__("re").search(r'"outfits_wanted":(\d+)', текст)[1]),
        "worn": відп.count('"near_face"'), "с": round(time.time() - п), "відповідь": відп}, ensure_ascii=False), flush=True)
