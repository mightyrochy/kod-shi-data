"""Порівняння id та походження знімків бази PR і голови."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / "джерела"))
import колір_річ as К

до, після = ({р["id"]: р for р in json.loads(Path(п).read_text(encoding="utf-8"))["каталог"]}
              for п in sys.argv[2:4])
група = json.loads((Path(sys.argv[1]) / "аудит/перевірка/2.13_тип_кольору/каталог.json").read_text(encoding="utf-8"))["група_59"]
print(json.dumps(dict(до=len(до), після=len(після), втрачено_id=len(до.keys() - після.keys()),
    додано_id=len(після.keys() - до.keys()), група=len(група),
    збережено_фото=sum(bool(після.get(і, {}).get("колір_вимір")) for і in група),
    група_вимір=sum(К.тип_кольору(після.get(і)) == "вимір" for і in група),
    приклади={і: dict(тип=К.тип_кольору(після[і]), lab=К.точка_кольору(після[і]),
        вимір=після[і].get("колір_вимір")) for і in ("ж-00378@vilni.store", "ж-00260@25union.com.ua")}),
    ensure_ascii=False, indent=2))
