"""Порівнює справжні промпти й читачі фото з базою на записаних відповідях, без моделей."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[2]


def git(*арг):
    """Читає версіоновані джерела й записи без зміни робочого дерева."""
    return subprocess.run(["git", "-C", str(КОРІНЬ), "-c", "core.quotepath=false", *арг],
                          capture_output=True, check=True).stdout


def вимір(джерела, записи):
    """Збирає обидва запити й читає ті самі відповіді окремим процесом для кожної версії."""
    sys.path[:0] = [джерела, str(КОРІНЬ / "джерела")]
    import річ_з_фото as Р
    import оцінка_образу as О
    фото = [dict(ід="ф1", ширина=600, висота=900)]
    власні = [dict(name="White sandals", status="has", slot="shoes")]
    запити = {"розмова": Р.промпт_фото(фото), "власні": Р.промпт_фото(фото, власні),
              "повтор": Р.промпт_фото(фото, власні, "no_json_object"), "оцінка": О.промпт_речей(фото)}
    контроль = {}
    for назва, текст in запити.items():
        п = json.loads(текст)
        с = п["task"]["answer_schema"]["items"][0]
        контроль[назва] = dict(довжина=len(текст), поля=list(с), правил=len(п["task"]["rules"]),
            лише_коди=any("Field values are only codes" in р for р in п["task"]["rules"]),
            привязка_слота="within its" in текст, вид_за_формою="shape" in текст,
            підказки_власності=any('owner "mine"' in р for р in п["task"]["input"]))
    результати = []
    for з in записи:
        п = з["промпт"]
        ф = [dict(ід=ф["id"], ширина=ф.get("width"), висота=ф.get("height")) for ф in п["photos"]]
        if з["оцінка"]:
            новий = О.промпт_речей(ф)
            вих = О.речі_з_відповіді(з["відповідь"], ф)
        else:
            новий = Р.промпт_фото(ф, п.get("her_items_in_words"), п.get("format_error"))
            вих = Р.речі_з_відповіді_фото(з["відповідь"], ф, власні=п.get("her_items_in_words"))
        результати.append(dict(файл=з["файл"], оцінка=з["оцінка"], довжина=len(новий), вихід=вих))
    return dict(контроль=контроль, записи=результати)


def головна():
    """Ізолює імпорти двох версій і вимагає незмінності всіх результатів читання."""
    if len(sys.argv) > 1 and sys.argv[1] == "--вимір":
        print(json.dumps(вимір(sys.argv[2], json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))),
                         ensure_ascii=False))
        return
    база = sys.argv[1] if len(sys.argv) > 1 else "aa1c2bdce176233da50d5b2fce77107fbfd40f5c"
    записи = []
    for гілка, тека, оцінка in (("origin/claude/zhyvi-1016-1", "аудит/живі_1016_1", True),
                                (база, "аудит/живі_12/Б", False)):
        for файл in git("ls-tree", "-r", "--name-only", гілка, "--", тека).decode().splitlines():
            if "/VIDPOVIDI/" not in файл or not файл.endswith(
                    "_ОЦІНКА_речі_на_фото.txt" if оцінка else "_речі_з_фото_шар_.txt"):
                continue
            текст = git("show", гілка + ":" + файл).decode()
            до, після = текст.split("── ВІДПОВІДЬ", 1)
            промпт = json.JSONDecoder().raw_decode(до[до.index("{"):])[0]
            записи.append(dict(файл=файл, оцінка=оцінка, промпт=промпт,
                               відповідь=після.split("\n", 1)[1].strip()))
    assert any(з["оцінка"] for з in записи) and any(not з["оцінка"] for з in записи), "Немає записів обох викликів"
    with tempfile.TemporaryDirectory(prefix="е2-фото-") as тека:
        т = Path(тека)
        for ім in ("річ_з_фото", "оцінка_образу"):
            (т / (ім + ".py")).write_bytes(git("show", база + ":джерела/" + ім + ".py"))
        вхід = т / "записи.json"
        вхід.write_text(json.dumps(записи, ensure_ascii=False), encoding="utf-8")
        виходи = [json.loads(subprocess.run([sys.executable, __file__, "--вимір", str(ш), str(вхід)],
                  capture_output=True, check=True, text=True, encoding="utf-8").stdout)
                  for ш in (т, КОРІНЬ / "джерела")]
    пари = list(zip(виходи[0]["записи"], виходи[1]["записи"]))
    assert all(а["вихід"] == б["вихід"] for а, б in пари), "Результат читання змінився"
    assert all(б["довжина"] < а["довжина"] for а, б in пари), "Запит не скоротився"
    for назва, к in виходи[1]["контроль"].items():
        assert not к["лише_коди"] and not к["привязка_слота"] and к["вид_за_формою"]
        assert ("in_outfit" in к["поля"]) == (назва == "оцінка")
        assert ("owner" in к["поля"]) == (назва != "оцінка")
    print(json.dumps(dict(база=база, однаково_прочитано=len(пари),
        оцінок=sum(а["оцінка"] for а, _ in пари), розмов=sum(not а["оцінка"] for а, _ in пари),
        довжини_записів=[sum(з["довжина"] for з in в["записи"]) for в in виходи],
        контроль_до=виходи[0]["контроль"], контроль_після=виходи[1]["контроль"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    головна()
