# -*- coding: utf-8 -*-
"""Рядки 6452, 6459: записи ЖИВІ (`*_ОЦІНКА_відповідь.txt` + перекладачка картки за ним) — ДО: картки з ід фото,
формулювання «нема на фото»; ПІСЛЯ: ті самі відповіді через `прийняти_оцінку` і сталий напис показу (`node`).
Запуск із `джерела`: python3 -W ignore проби/оцінка_картка_6452.py <тека записів>"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import оцінка_образу as О, протокол as П, суд_чеклісти as С

ІД = re.compile(r"\b[pр]\d+(?:-\d+)?\b|\([chсн]\d+\)")
РЯДОК = r'((?:[^"\\]|\\.)*)'


def записи(тека):
    """[(сцена, ім'я, промпт ОЦІНКИ, відповідь моделі, вхід перекладачки {н: текст}, вихід {н: текст})]."""
    for ф in sorted(Path(тека).rglob("*_ОЦІНКА_відповідь.txt")):
        запит, _, відп = ф.read_text(encoding="utf-8").partition("── ВІДПОВІДЬ")
        промпт = json.JSONDecoder().raw_decode(запит[запит.index('{"task"'):])[0]
        шари = [ш for ш in sorted(ф.parent.glob("*_мовний_шар.txt")) if ш.name > ф.name
                and "not judged, absent" in ш.read_text(encoding="utf-8")]
        вх, вих = {}, {}
        if шари:
            з, _, в = шари[0].read_text(encoding="utf-8").partition("── ВІДПОВІДЬ")
            вх = {int(н): json.loads('"%s"' % т) for н, т in re.findall(r'\{"н": (\d+), "текст": "%s"' % РЯДОК, з)}
            пари = (re.findall(r'"н":\s*(\d+),\s*"текст":\s*"%s"' % РЯДОК, в)
                    or re.findall(r'"(\d+)":\s*"%s"' % РЯДОК, в))
            вих = {int(н): json.loads('"%s"' % т) for н, т in пари}
        yield ф.parents[1].name[:2], ф.name[:8], промпт, П.розбір(відп.split("\n", 1)[-1])[0], вх, вих


def тексти(к):
    """Тексти картки `прийняти_оцінку`: відповідь, «що вдало», «що змінити»."""
    return [к.get("відповідь", "")] + [х["текст"] for х in к.get("вдало", []) + к.get("змінити", [])]


def суд_з_промпту(п):
    """Суд для `прийняти_оцінку` з даних промпту ОЦІНКИ (ід — назад з дроту)."""
    з = О.ід_з_дроту
    зміни = [dict(ід=з(с["id"]), ціль=з(с["replace"][0]), звідки="own" if "with_own" in с else "shop",
                  нова=з(с.get("with_own") or "") or None, вид=(с.get("with_shop") or {}).get("kind"), річ={})
             for с in п.get("changes") or []]
    знахідки = [dict(ід=з(f["id"]), ремонт_заяви=f.get("fix")) for f in (п.get("check") or {}).get("findings") or []]
    return dict(образ=[з(і) for і in п["outfit"]], запасні=[з(і) for і in п.get("alternatives") or []], зміни=зміни,
                суд=dict(findings=знахідки), речі=[dict(ід=з(р["id"])) for р in п["items"]], рівень="remark")


if __name__ == "__main__":
    функція = re.search(r"const НЕМА_НА_ФОТО_П[\s\S]*?\n}\n", Path("показ.html").read_text(encoding="utf-8")).group(0)
    коди = [[к for к in п.get("not_in_photo") or [] if к not in С._НЕ_РЕЧІ_КАРТКИ] for *_, п, _о, _в, _и in
            записи(sys.argv[1])]
    рядки = subprocess.run(["node", "-e", функція + "process.stdin.on('data', d => console.log(JSON.stringify("
                            "JSON.parse(d).map(к => рядокНемаНаФотоП({коди: к})))))"],
                           input=json.dumps(коди), capture_output=True, text=True).stdout
    до_ід, після_ід, до_нема = [], [], set()
    після_нема = {re.sub(r"нема [^:]*:", "нема …:", р) for р in json.loads(рядки)}
    for сц, ім, п, об, вх, вих in записи(sys.argv[1]):
        if any(ІД.search(т) for т in вих.values()):
            до_ід.append(сц + " " + ім)
        до_нема |= {т.split(":")[0].strip().lower() for т in вих.values() if re.search(r"фото", т)}
        к = О.прийняти_оцінку(json.dumps(об), суд_з_промпту(п))["картка"] or {}
        if any(ІД.search(т) for т in тексти(к)):
            після_ід.append(сц + " " + ім)
    допит = [(ф.parents[1].name[:2], П.розбір(ф.read_text(encoding="utf-8").partition("── ВІДПОВІДЬ")[2]
                                              .split("\n", 1)[-1])[0])
             for ф in sorted(Path(sys.argv[1]).rglob("*_ОЦІНКА_допит.txt"))]
    print("допит з ід: ДО %s · ПІСЛЯ %s" % (
        [с for с, о in допит if ІД.search(str((о or {}).get("answer")))],
        [с for с, о in допит if ІД.search(О.прийняти_допит(json.dumps(о))["відповідь"])]))
    print("картки з ід фото: ДО %d %s · ПІСЛЯ %d %s" % (len(до_ід), до_ід, len(після_ід), після_ід))
    print("формулювань «нема на фото»: ДО %d · ПІСЛЯ %d %s" % (len(до_нема), len(після_нема), sorted(після_нема)))
