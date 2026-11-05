"""ДО/ПІСЛЯ продовження 8 (клас 5624): з кореня репозиторію, ДО — з `git show <коміт>:`, ПІСЛЯ — робоче дерево."""
import collections, gzip, io, json, re, subprocess, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, "zhnyvarka")
import складальник as с
from жнива_каталог import адреса

коміт = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
def розпакувати(б): return [json.loads(р) for р in gzip.decompress(б).splitlines()]
ДО = розпакувати(subprocess.check_output(["git", "show", коміт + ":каталог_записи_v1.jsonl.gz"]))[1:]
ПІСЛЯ = розпакувати(open("каталог_записи_v1.jsonl.gz", "rb").read())[1:]
xml_до = gzip.decompress(subprocess.check_output(["git", "show", коміт + ":каталог_повний.xml.gz"])).decode()
xml_після = gzip.decompress(open("каталог_повний.xml.gz", "rb").read()).decode()
склад = lambda р: any(п[0] in ("Склад", "склад") and п[1] for п in р["параметри"])
def oldprice(текст):
    return {о.get("id") or о.findtext("id"): о.findtext("oldprice") for о in ET.fromstring(текст).iter("offer")}
для_ід = lambda зап: {р["ід"]: р for р in зап}
до_ід, після_ід = для_ід(ДО), для_ід(ПІСЛЯ)
давні_лише = [р for р in ДО if р.get("ціна_стара") and not р.get("стара_ціна")]
різні = [р for р in ДО if р.get("ціна_стара") and р.get("стара_ціна") and float(р["ціна_стара"]) != float(р["стара_ціна"])]
def стара(зап, р): return (зап.get(р["ід"]) or {}).get("стара_ціна")
print("записів", len(ДО), "→", len(ПІСЛЯ))
print("старих цін у записі (`стара_ціна`):", sum(bool(р.get("стара_ціна")) for р in ДО), "→", sum(bool(р.get("стара_ціна")) for р in ПІСЛЯ))
print("`<oldprice>` у XML:", sum(1 for _ in re.finditer("<oldprice>", xml_до)), "→", sum(1 for _ in re.finditer("<oldprice>", xml_після)))
print("1943 старі ціни, що губились (ціна_стара без стара_ціна), у ДО:", len(давні_лише),
      "; з них у ПІСЛЯ з `стара_ціна`:", sum(bool(стара(після_ід, р)) for р in давні_лише),
      "; запису нема:", sum(р["ід"] not in після_ід for р in давні_лише),
      "; знижки нема (стара ≤ ціна):", sum(р["ід"] in після_ід and not стара(після_ід, р) for р in давні_лише))
print("19 застарілих (обидва поля, суми різні), у ДО:", len(різні), "; у ПІСЛЯ суму свіжої картки мають:",
      sum(стара(після_ід, р) and float(стара(після_ід, р)) == float(р["ціна_стара"]) for р in різні), "; запису нема:",
      sum(р["ід"] not in після_ід for р in різні))
знято = [р for р in ДО if р.get("стара_ціна") and not р.get("ціна_стара") and р["ід"] in після_ід and not після_ід[р["ід"]].get("стара_ціна")]
print("записів лише з `стара_ціна` адаптера, яку свіжа картка зняла (нема знижки):", len(знято))
print("втрачено нормалізованих адрес:", len({адреса(р["адреса"]) for р in ДО} - {адреса(р["адреса"]) for р in ПІСЛЯ}))
print("зі складом:", sum(map(склад, ДО)), "→", sum(map(склад, ПІСЛЯ)), "; стерто складів у збережених ід:",
      sum(склад(р) and not склад(після_ід[р["ід"]]) for р in ДО if р["ід"] in після_ід))
print("theoriginals:", sum("theoriginals.com.ua" in р["адреса"] for р in ДО), "→", sum("theoriginals.com.ua" in р["адреса"] for р in ПІСЛЯ))
знятих = [р for р in ДО if р["ід"] not in після_ід]
print("знято записів (ід нема в ПІСЛЯ):", len(знятих), collections.Counter(р["збирач"] for р in знятих).most_common(3))
