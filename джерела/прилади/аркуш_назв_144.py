# -*- coding: utf-8 -*-
"""Аркуш «фото картки + назва ДО/ПІСЛЯ» — по N речей на кожну названу крамницю (рядок 144).

НАВІЩО. Числа проби кажуть, СКІЛЬКИ назв змінилось; вони не кажуть, чи стало
краще. Приймання рядка 144 вимагає аркуша, який куратор і власник дивляться
ОКОМ: знімок речі, назва, яку жінка бачила доти, і назва, яку побачить тепер,
плюс джерело нової назви й причина заміни. Один html, ніякої мережі, крім
знімків самих крамниць.

ЧОМУ ПРИЛАД, А НЕ ПРОБА: проба друкує факт у ≤40 рядках і йде в кожен прогін;
цей файл малює сторінку на 240 рядків і потрібен раз — на огляд.

ПРОГІН:  cd джерела && python3 прилади/аркуш_назв_144.py [вихід.html] [скільки]
"""
import html, os, sys

_тут = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _тут)
os.chdir(_тут)
import feed
import назва_речі as НР

# Крамниці, названі куратором у ручному огляді 23.09.2026 (усі класи дефекту).
КРАМНИЦІ = ("brenda.ua", "gepur.com", "musthave.ua", "feelyou.com.ua", "maxa.ua",
            "morandi.ua", "sunwin-store.com", "favoriteshoes.com.ua", "jecomestudio.com",
            "honchstudio.com", "solmar.com.ua", "stolyarchuk.com.ua", "vovk.com",
            "emmeliedelage.com", "ricamare.com.ua", "kasandra.ua", "nyni.shop",
            "sezone.ua", "fromus.ua", "vittorossi.ua", "attico.ua", "giardini-shoes.com",
            "alot.com.ua", "welfare.ua", "miraton.ua", "25union.com.ua", "bella-bicchi.com")

_СТИЛЬ = """body{font:15px/1.45 system-ui,sans-serif;margin:0;padding:24px;background:#faf8f5;color:#1a1714}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px;padding-top:12px;border-top:2px solid #e2ddd6}
p.під{color:#6d675f;margin:0 0 20px}table{border-collapse:collapse;width:100%;background:#fff}
td,th{border:1px solid #e2ddd6;padding:8px;vertical-align:top;text-align:left}
th{background:#f2eee9;font-weight:600;font-size:13px}
img{width:92px;height:120px;object-fit:cover;background:#f2eee9;display:block}
.до{color:#8a3a2a}.після{font-weight:600}
.джер{font-size:12px;color:#6d675f;white-space:nowrap}
.незмінно{color:#6d675f}"""


def рядки(скільки):
    """(крамниця → [(offer, рішення)]) — перші `скільки` речей кожної названої крамниці."""
    оф = feed.читати_yml(feed.каталог_на_диску())[0]
    карта = НР.читати_назви_карток()
    зібрано = {м: [] for м in КРАМНИЦІ}
    for o in оф:
        сюди = зібрано.get(o["магазин"])
        if сюди is None or len(сюди) >= скільки:
            continue
        сюди.append((o, НР.назва_для_показу(o, карта)))
    return зібрано


def сторінка(зібрано, скільки):
    """Аркуш як один html-рядок: знімок, назва ДО, назва ПІСЛЯ, джерело й причина."""
    ч = html.escape
    шм = ["<!doctype html><meta charset=utf-8><title>Назви товару: ДО і ПІСЛЯ</title>",
          "<style>%s</style>" % _СТИЛЬ,
          "<h1>Назва товару на картці: ДО і ПІСЛЯ</h1>",
          "<p class=під>Рядок 144 дошки. По %d речей на кожну з %d названих крамниць. "
          "«ДО» — назва, як її бачила жінка (<code>&lt;name&gt;</code> фіду); «ПІСЛЯ» — "
          "<code>назва_речі.назва_для_показу</code>. Знімок — той самий, що на картці.</p>"
          % (скільки, len(зібрано))]
    for м in КРАМНИЦІ:
        пари = зібрано.get(м) or []
        якщо_змінилось = sum(1 for o, р in пари if р["назва"] != o["назва"])
        шм.append("<h2>%s <span class=джер>— змінено %d із %d показаних</span></h2>"
                  % (ч(м), якщо_змінилось, len(пари)))
        шм.append("<table><tr><th>знімок</th><th>ДО (фід)</th><th>ПІСЛЯ (картка)</th>"
                  "<th>джерело · причина</th></tr>")
        for o, р in пари:
            фото = (o.get("фото") or [None])[0]
            знімок = ("<a href='%s' target=_blank><img loading=lazy src='%s' alt=''></a>"
                      % (ч(o.get("url") or фото or ""), ч(фото))) if фото else "<i>знімка нема</i>"
            змінено = р["назва"] != o["назва"]
            шм.append("<tr><td>%s</td><td class='%s'>%s</td><td class=після>%s</td>"
                      "<td class=джер>%s<br>%s</td></tr>"
                      % (знімок, "до" if змінено else "незмінно", ч(o["назва"]), ч(р["назва"]),
                         ч(р["джерело"]), ч(р["причина"] or "—")))
        шм.append("</table>")
    return "\n".join(шм)


if __name__ == "__main__":
    вихід = sys.argv[1] if len(sys.argv) > 1 else "аркуш_назв_144.html"
    скільки = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    зібрано = рядки(скільки)
    with open(вихід, "w", encoding="utf-8") as f:
        f.write(сторінка(зібрано, скільки))
    print("ФАКТ · аркуш %s · крамниць %d · рядків %d · змінено назв %d"
          % (вихід, len(зібрано), sum(len(v) for v in зібрано.values()),
             sum(1 for v in зібрано.values() for o, р in v if р["назва"] != o["назва"])))
