# -*- coding: utf-8 -*-
"""розбір_відповідей.py — розбір відповідей моделі: образи ОБРАЗИ_V1 з JSON і тексту, свідомі розриви, опис і його перевірка.

Винесено з `pipeline.py` (СТАНДАРТ_КОДУ п.16: файл ≤ 1 500 рядків). `pipeline.py`
лишається фасадом і реекспортує кожне ім'я звідси, тож викликачі (`bridge`, показ через Pyodide,
проби, гейти) не змінюються. Що звідки — карта в шапці `pipeline.py`.
"""
import re
import re as _re_ід
import json as _json_ід
import протокол as _ПР
from пакет_моделі import номери_речей, скелет_схеми


# ОПИС — ЗАДАЧА ЗБИРАЧА (`збирач_промптів`), АНГЛІЙСЬКОЮ (П-2, аудит/ПРОДУКТ.md п.12: «промпти
# функціональної моделі — англійською»). Оголошення побудовано під задачу; дані — ті самі поля `ОПИС_V1`, перекладені в коди
# (`дріт_моделі.опис`). Рядок кожного поля йде в промпт лише тоді, коли поле є.
# ЧОМУ ЦІ РЯДКИ (для людей; моделі це не потрібно):
#   · «з кожного фото бери лише названу річ» — крамниці знімають речі на моделях у повному
#     образі, і модель описувала чуже взуття з кадру;
#   · «лише речі з «outfit»» — порада докупити річ, якої в образі нема;
#   · «склад не міняй» — промпт колись вимагав «ОБРАЗ: id», а id моделі не давали, і
#     найдорожчий крок відкидався; склад знає код, модель лише описує;
#   · «wrong_photos» — межа названа вголос: позначка стояла під сукнею, чиє фото — та сама
#     річ на людині;
#   · «missing» — образ без низу, а опис розповідав про спідницю з фото кардигана (З-1г);
#   · «day» — опис казав «чому це працює» без жодного слова про її день;
#   · «hers» — її річ з її фото, не товар;
#   · «set_half» — половина комплекту: це казала б фраза коду в назві («лише верх із
#     комплекту: …»), тож це поле; слота речі нема (місце речі в образі моделі не прописувати —
#     що це верх, вона бачить сама).
# МОВА ТЕКСТУ (`мова_тексту`): з мовним шаром модель пише внутрішньою мовою (англійською), текст
# жінці робить шар — «Чому цей образ» і «Як це носити» проходять `мовоюКарткуП` (показ);
# без шару показ шле «Ukrainian», бо перекладати нікому (той самий механізм, що П-1).
import збирач_промптів as _ЗП
import дріт_моделі as _Д
import композитор_річ as _КПР
import річ_з_фото as _РФ
import verify as _V
import руки_без_коду as _РБК
import language_gate as _LG
import внутрішня_мова as _ВМ
import фід_слот as _ФС
import feed as _Ф
import colorspace as _cs

ОПИС = _ЗП.Оголошення(
    задача="опис",
    роль="You are the stylist. You describe to her the outfit you chose for her.",
    вхід=(
        # ОПИС-1: «колір» — дані крамниці для читання фото, а не те, що бачить жінка; інакше
        # модель звіряє фото з ним уголос («У назві вказано зелений…», «У коді вказано…»).
        # ПРОЗА-КАРТОК-2: річ без кадру лишалась би без кольору («широкі штани в картатий
        # принт»), хоч крамниця його знає, — колір речі без фото береться звідси, без посилання на джерело
        _ЗП.Поле("outfit", "the chosen outfit: its items with number «n», name and shop, and the shop's data on "
                           "their color («color» as a code, «shop_color» — the shop's own word when it says more, "
                           "«hex») — a hint for reading the photo and the colour of an item that has no photo",
                 треба=True),
        _ЗП.Поле("outfit.items[].photos",
                 "the numbers of this item's photos: every photo stands under its own label «Photo N — …:» "
                 "among the blocks placed before this object, and the label names the item by its «n»; under a "
                 "label with «not delivered» or «not available» there is no image",
                 як="describe what you see on the photos, not the name; from each photo take only the item of "
                    "its «kind» — a belt, a bag or jewelry is often shown worn with a blouse or a dress: describe "
                    "the belt, not the blouse; never take for an item a photo under another number, and when "
                    "all of its photos are not delivered, describe it by its name and «color»",
                 без="There are no item photos: describe the items by their names; leave «wrong_photos» empty."),
        # «Пасок Базовий блакитний» описувався блузою з фото пояса — опис йшов за кадром, а не за
        # річчю; рід речі кодом каже, ЩО на кадрі описувати
        # цілий комплект — родом «set» (від «top, blazer» опис звав його «не включеним»)
        _ЗП.Поле("outfit.items[].kind", "what the item is, as a code (belt, top, dress, shoes, bag…); «type» — "
                                        "its narrower type when the code knows it; «set» — a set sold as one "
                                        "item, its top and its bottom both in the outfit",
                 як="«about_items» describes the item of this «kind» and nothing else from its photo"),
        # Кадр «кемел» пальта — сірий (галерея іншого кольору моделі); код це знає (R-FEED-01 за кнопкою
        # картки), модель — ні, і правило «опиши, як на фото» тягнуло б її проти речі.
        # Другий колір поруч — `photo_colour: green` біля `color: purple` — модель переказувала б жінці
        # («Колір тут здається зеленим, але ми обираємо його як фіолетовий»). Розлад розвʼязує код
        # (`фід_кадр_колір.рішення` → колір речі), тож річ несе ОДИН колір, а кадр — лише позначку.
        # Без цього «бежеві туфлі» в описі йшли б під шоколадним кадром картки — колір не їде зовсім
        _ЗП.Поле("outfit.items[].photo_other_colour", "the shop names one colour of this item and its photos show "
                                                      "another; which one she gets is not known",
                 як="do not name the colour of this item and say nothing about the colour on its photos — no "
                    "«looks …, but …»; this is no reason for «wrong_photos» or «swap»: the card already tells "
                    "her about the photo"),
        _ЗП.Поле("outfit.items[].no_photo", "this item has no photo of its own among the others",
                 як="describe it by its name and «color»; do not take another item's photo for it"),
        _ЗП.Поле("outfit.items[].hers", "her own item from her photo, not a product",
                 як="do not offer to buy it and do not mention a price or a shop; say how the other items "
                    "work with it"),
        _ЗП.Поле("outfit.items[].set_half", "only this half of a set is in the outfit"),
        # «idea» і «your_day_sentence» — підпис і речення моделі про день зі складання й вибору,
        # писані до ремонту й заміни: «Softened by Scarf» без шарфа (зі складу складання лишились
        # 2 речі з 6), «oversized grey cardigan» при пальті, «black skirt», «implied blazer layer».
        # Код слів прози не читає (п.12) і звірити їх зі складом не може, тож опис їх не дістає:
        # склад — лише «outfit» кодами, день — «day» фактами.
        _ЗП.Поле("case", "her occasion: its fields as codes, her own words as quotes; «formality» is an "
                         "internal 1–10 band, for you only"),
        # `goal_zones` в описі йдуть («case» кодами, `випадок_для_пакета`), і правило поля потрібне:
        # правило «body» («where it sets the eye … waist») і спосіб носіння вели б модель далі:
        # «підперезана червоним паском», «щоб пасок підкреслював найвужчу частину тулуба» при
        # «приховати живіт». Названу зону ховає крій, сміливе лишається деінде (п.17).
        _ЗП.Поле("case.goal_zones", "the body zones she wants to draw the eye away from, with any goal",
                 # «no tuck that marks the waist» модель обходила застереженням — «Tuck the front of the
                 # vest slightly … without marking your waist»; тож заборона без умови «marks»
                 як="this comes before «body» and «ways_to_wear»: set the eye on none of these zones — no "
                    "sentence or way to wear that marks, frames or accentuates them; with belly or hips: no tuck "
                    "of any kind (not a front or half tuck, not a top tucked into the bottom, whatever it is "
                    "said to avoid) and no belt at the waist, never «the narrowest part of the torso»; do not name "
                    "them to her as something to hide; say where the outfit leads the eye instead"),
        # «the choice is hers» про БУДЬ-ЩО, що сперечається з днем, модель ставила в кінець більшості
        # карток — про речі, які обрала сама («сітка… наскільки це важливо в церкві, вирішуєш ти»).
        # Своє рішення стилістка не віддає жінці назад.
        _ЗП.Поле("day", "her day as facts; «formality» is the same internal band",
                 як="in the last part of «text» say how this outfit lives through her day; when something "
                    "you chose argues with the day (weather, hours on her feet, the place), say in one plain "
                    "sentence why you still chose it, or what she does about it in the day itself (take the "
                    "layer off, swap the pair); never hand that decision back to her"),
        # ОПИС-1 (K-PAL-11/14/15): «найдальші» й «комбінація», якщо йдуть у КОЖЕН опис, дають
        # «маленька оливкова чи зелена деталь» навіть на похороні й поради додати річ, якої в образі
        # нема. Тож лише те, що стосується речей образу.
        _ЗП.Поле("palette", "her palette",
                 як="in the third part, in your own words and only where it concerns the items of this "
                    "outfit: the metal, when the outfit has jewelry or metal details; a colour «farthest» "
                    "from her only when an item of this outfit carries it (call no other colour farthest "
                    "from her); a combination she can put together — optional, and only from the items of "
                    "this outfit, never by adding an item; not as a list"),
        # K-BOD-02, K-SIL-03 (аудит/ПРОДУКТ.md п.4): її фігура кодами — ті самі, що в брифі складання.
        # П.17: річ образу — вибір стилістки; річ проти фігури — пояснити, рішення не віддавати.
        # «cuts_best_on_her: belted» при вільному светрі без пояса давало «tuck in just the front hem
        # slightly over your belt»; «що з цим робити» — лише речами образу.
        # «your O-shape waist» у записі пальта, «your O-shape figure» у «text» — код фігури
        # (`body.shape`) ішов би жінці; межа — ознаки фігури словами крою, і в записі речі теж
        _ЗП.Поле("body", "her figure as the code measured it: height, shape code, zones, and statements — the cuts "
                         "that sit best on her, where a voluminous outfit takes its anchor, where most conditions "
                         "meet on her body",
                 як="in the last part of «text» say in one or two sentences what this outfit does for her "
                    "figure — which line it draws, where it sets the eye (shoulders, waist, hips, legs, "
                    "height), with the items that do it; speak of what the outfit does, never of what her "
                    "body lacks or what should be hidden; when an item of the outfit works against these "
                    "statements, say so gently and say why you chose it anyway or what to do with it — only "
                    "with the items of «outfit»; «cuts» are cuts of an item, not items to add («belted» — a top "
                    "with its own belt, never a belt she puts on); her figure only in words of the line and the "
                    "cut — her waist, hips, shoulders, legs — never as the shape code, a letter, an «…-shape», "
                    "a body type or a number"),
        _ЗП.Поле("body.shape", _Д.ФІГУРА_КОДИ_EN),
        # ОПИС-1 (K-ACC-12, K-EDG-01): у кожної сумки є три способи (рука, плече, навскоси),
        # і «Як це носити» щоразу казало б про сумку
        _ЗП.Поле("ways_to_wear", "ways the items can be worn: «item» — «n» of the item of «outfit» (none — the "
                                 "whole outfit); each statement is one way — its place, and its effect when the "
                                 "code knows one",
                 як="in «how_to_wear» name a way only when it changes something for this outfit — its effect "
                    "matters here (a line across the torso that already has many, a hem it lands on); a way "
                    "that changes nothing is left out"),
        # «against a condition» без умови — сумку, яку стилістка ДОДАЛА, опис
        # прочитав вадою («не поєднується», «потрібно замінити», `swap`); тепер хід несе заяви своєї знахідки
        _ЗП.Поле("your_declared", "items you kept deliberately although the code found something against them: "
                                  "«item» — its «n», «statements» — what the code found, as statement codes",
                 як="this was your choice, not a flaw of the item: never call it a mismatch and never name it "
                    "in «swap»; in «how_to_wear» say what she does about what the code found"),
        _ЗП.Поле("she_refuses", "what she refused",
                 як="do not advise an item that breaks it and do not call it a compromise; when such an "
                    "item is in the outfit, tell her so plainly"),
        # Ч-1 (аудит/ПРОДУКТ.md п.12): the code no longer writes this as a sentence — it sends the
        # same statement codes the language model turns into the card line; codes are English
        # by construction, so this English prompt carries them as they are.
        _ЗП.Поле("missing", "what this outfit lacks, as statement codes «code» (with «values» where "
                            "a statement carries names or numbers)",
                 як="do not describe it as an item of the outfit, nor from the photo of another item; you "
                    "may say in one sentence that it is missing"),
        # МАК-2 (П-4): порада про рівень макіяжу — заявами; вибір її (п.9)
        _ЗП.Поле("makeup", "a soft note on the level of her make-up today, as statement codes «code»",
                 як="say it in your own words in one gentle sentence in the last part of «text»: advice "
                    "only, nothing in the outfit depends on it; a light «if you like» is enough"),
        # ФОТО-1 (аудит/ПРОДУКТ.md п.17): друга половина заміни — лише коли опис назвав річ, а
        # код знайшов запасні, що пройшли його суд (`заміна_з_фото`); у звичайному виклику поля нема
        _ЗП.Поле("swap_spares", "the item you named for replacement, your reason, and the spares of the "
                                "same kind the code checked in its place; every spare has «photos» like "
                                "the items of the outfit",
                 як="look at the photos of the spares and choose the one that serves this outfit and her "
                    "occasion best, or none; describe the outfit with your choice in place — the chosen "
                    "spare instead of the item; the card tells her separately what you replaced and why, so "
                    "«text» does not; answer «swap» again with «item», «why» and «to»"),
    ),
    правила=(
        # ОПИС-1: вигадані речі («простий світлий топ» без топа, «золоті сережки» без сережок,
        # зачіска моделі з фото) і службові звірки назви з фото
        "Describe only the items of «outfit»: no suggestions to buy or add more, no items it does not contain — "
        "no top, jewelry, gloves or hairstyle that is not an item of «outfit», even when a photo shows it or "
        "she may own it.",
        "Do not change the outfit yourself. Describe each item as its photo shows it: a clearly different item or "
        "colour goes only into «wrong_photos» or «swap».",
        "Say each thing about an item once, and do not state a quality and then doubt it.",
        # ПРОЗА-КАРТОК-2: «На фото є ще й підібрані сірі штани, але до цього образу належить
        # лише жакет», «Фото я не бачу, тому орієнтуюся на назву», «як сказано в назві» — службова мова
        # про кадр у картці; чого бракує на фото, картка вже каже під річчю (п.9).
        # «Не кажи про джерела» не повторюється в полі «outfit», у дужці правила 2 і в «photos» (кадр
        # з чужим одягом — і в підписі кожного кадру): вада трималась не повторами, тож усе це —
        # одним правилом тут, звірка фото з назвою й даними крамниці — теж
        "Talk to her about the items, never about what you were given: no word about photos, frames, what "
        "else a frame shows, a photo you could not see, or the name and shop data you went by, and no comparison "
        "of a photo with them — the card "
        "already shows her the photos and says under an item when it has none.",
        "Give no advice on how to carry the bag (in the hand, on the shoulder, across the body).",
        # відповідальність за вибір речі — на стилістці (аудит/ПРОДУКТ.md п.17: з поясненням — свідомий вибір)
        "Every item of «outfit» is your choice: stand behind it. Do not end a doubt with «the choice is yours», "
        "«it's up to you» or «your call» — say why the item is worth it, or what she does about it. Leave a "
        "decision to her only about what she asked for herself: her words in «case», an item marked «hers».",
        "Only when a photo shows that an item is not what this outfit needs — a clearly different colour, "
        "another kind of item, or unfit for her occasion — and that matters for this outfit, name that one "
        "item in «swap»: the code then looks for a replacement of the same kind. This is rare; when in "
        "doubt, leave «swap» out.",
        _ЗП.КІНЕЦЬ_ВІДПОВІДІ_EN,
    ),
    вихід="ОПИС_ВІДПОВІДЬ_V1",
    поля_виходу={
        # ОПИС-1: «Чому цей образ» без обмеження — 4–5 екранів; частина (2) повторювала (1), а (3)
        # збирала всі поля входу
        # річ за річчю — полем `про_речі` з номером, а не рядком прози: модель називала
        # у «named» усі номери, а текст пропускав пальто чи піджак і описував штани, яких нема
        "про_речі[].н": "«n» of the item of «outfit»: one entry for every item of «outfit», in its order",
        # «styled here with matching wide-leg trousers» при бомбері без штанів, кардиган «поверх
        # в'язаного комплекту» з його фото при сукні — запис речі описував увесь кадр. Код прози не читає (п.12),
        # тож межа — тут: запис має лише свою річ, а як речі поєднуються — «text» (речі образу, звірені «named»)
        "про_речі[].текст": "prose for her about this one item alone: what it is, cut, length, color in words, fabric, "
                            "in one or two sentences, as its photo and data show; it is in her outfit — never say it "
                            "is not included; no other garment, shoe, bag or accessory — neither one its photo shows "
                            "it with nor another item of «outfit»: how the items go together belongs to «text»; her "
                            "figure, if at all, only in words of the line and the cut — never the shape code or an "
                            "«…-shape»",
        "текст": "prose for her after the items: (1) optional, only when it adds something — how the "
                 "shoes, the outer layer and the accessories go with the rest, in one or two sentences; "
                 "(2) why it works — 3–4 sentences, taking from «day», «palette», «makeup» and «missing» "
                 "only what matters most for this outfit and her occasion",
        # «Tuck the blazer in slightly» без адресата — переклад дописав «у штани»
        # при спідниці; порада, що кладе річ у, під чи на іншу, називає й ту, і обидві — речі образу
        "як_носити": "one piece of advice per line, at most three, each changing how the outfit looks or "
                     "lives through her day; advice that puts an item into, under or over another names that "
                     "other item too, and both are items of «outfit»",
        "названо[].н": "«n» of the item of «outfit» that «text» or «how_to_wear» names; a thing that is "
                       "not an item of «outfit» has no «n» — and should not be named at all",
        "названо[].що": "every garment, shoe, bag, jewelry or accessory that «text» or «how_to_wear» names — "
                        "each once, in a few words",
        "фото_не_те": "«n» of an item whose photo shows another item, a clearly different color, a "
                      "placeholder or a logo; the same item on a person, from another angle, close up or "
                      "with other clothes in the frame is no reason; when in doubt, leave it out",
        "заміна.річ": "«n» of the ONE item to replace; leave «swap» out entirely when there is no weighty "
                      "reason — the usual case",
        "заміна.чому": "colour — the photo shows a clearly different colour than the code knows; kind — "
                       "the photo shows another kind of item; occasion — the item on the photo does not "
                       "suit her occasion",
        "заміна.на": "only with «swap_spares» in the input: «n» of the spare you choose; leave it out to "
                     "keep the item",
    },
    межі=("лише_вхід", "для_неї", "без_чисел_тіла", "без_шкал"),
    мова_промпту="en",
)


def укладка_опису(канал_3, речі=None):
    """ТРЕТІЙ КАНАЛ КОРПУСУ ПОЛЕМ `укладка` (K-CRA-11 + K-CHN-01, Т-06 крок 2).

    `accessory.команди_розкладки` віддає ОПЦІЇ з названими компромісами (хустка:
    шия / сумка / запʼясток і наслідок кожного), `outer.команди_укладки` — ЗНАХІДКИ
    (вузол пояса тренча, піднятий комір). Обидві форми тут зводяться до одного
    поля схеми `{річ, опції}`: наслідок місця приклеюється до самого місця («у
    руці — читається як вечірнє»), бо схема дозволяє рядок, а втратити наслідок
    означало б дати вибір без ціни. Ворота формату («лише в приміщенні») ідуть
    останнім рядком опцій — це умова вибору, і модель мусить її бачити.

    ВМ-3б (аудит/ПРОДУКТ.md п.12): поруч із фразами — `заяви` (ті самі опції й ворота
    кодами, `аксесуари_структура.опції_заявами`; команди верхнього шару — їхні заяви й заяви
    ремонту). На дріт опису (`дріт_моделі.опис`) їдуть заяви; фрази лишаються звітові.

    `речі` — речі образу (`н`, `назва`); з ними запис несе `н` речі, якої стосується (дріт
    кладе його в `item` замість назви українською, п.12), а запис про річ поза образом не їде. Канал 3
    називає річ тим самим рядком, що узяв з неї (`назва`, інакше `id`), тож це звірка ключа, а не слів.
    Команда без речі стосується образу цілого — `н` вона не несе.
    """
    к3 = канал_3 or {}
    вих = []
    за_ключем = {}
    for x in (речі or []):
        for к in (x.get("н"), x.get("назва")):
            if к:
                за_ключем.setdefault(str(к), str(x.get("н")))

    def _номер(річ):
        """(`н` речі образу або None, чи лишити запис): річ поза образом — не лишати."""
        if річ is None or not речі:
            return None, True
        н = за_ключем.get(str(річ))
        return н, н is not None
    for о in (к3.get("опції") or [])[:6]:
        # ОПИС-1 (K-ACC-12, K-EDG-01): опції сумки (рука / плече / навскоси) однакові для
        # КОЖНОЇ сумки — образу код не знає, тож чи міняє спосіб щось у ЦЬОМУ образі, сказати не
        # може; з ними в промпті порада про сумку йшла б у кожну картку
        # («тримай у руці, щоб не додавала діагоналі»). Тому сумка в опис не їде зовсім.
        if о.get("клас") == "сумка":
            continue
        опції = []
        наслідки = о.get("наслідок_місця") or {}
        for м in (о.get("допустимі_місця") or []):
            н = str(наслідки.get(м) or "").strip()
            опції.append(("%s — %s" % (м, н[:100])) if н else str(м))
        if о.get("ворота_формату"):
            опції.append(str(о["ворота_формату"])[:110])
        н, лишити = _номер(о.get("річ"))
        if опції and лишити:
            вих.append(dict(річ=str(о.get("річ") or о.get("клас") or "річ")[:60], опції=опції,
                            **({"н": н} if н else {}),
                            **({"заяви": list(о["опції_заяви"])} if о.get("опції_заяви") else {})))
    for c in (к3.get("команди") or [])[:5]:
        суть = str(c.get("суть") or "").strip()
        н, лишити = _номер((c.get("речі") or [None])[0])
        if суть and лишити:
            з = list(c.get("заяви") or []) + list(c.get("ремонт_заяви") or [])
            вих.append(dict(річ=str((c.get("речі") or ["образ"])[0])[:60], опції=[суть[:140]],
                            **({"н": н} if н else {}),
                            **({"заяви": з} if з else {})))
    return вих


def опис_обʼєкт(речі, образ=None, задум=None, випадок=None, свідомі=None, фото_є=True,
                канал_3=None, палітра=None, день=None, день_образу=None, неповний=None,
                межі=None, мова_тексту=None, випадок_коди=None, заміна_запасні=None, макіяж=None,
                тіло=None):
    """Четвертий виклик: `ОПИС_V1` — обраний образ обʼєктом коду (його перевіряє схема,
    його кладе звіт); моделі його несе `промпт_опису` англійським дротом.

    `речі` — `[{н, назва, слот, тип?, частина?, магазин, колір?, hex?, кадр_колір?, фото, фото_номери}]`, як
    віддає `bridge.опис`. Скільки фото: речей — усі, що в
    образі; на річ — одне-двоє. Тому річ і несе `фото_номери`: без них модель не
    знає, котре зображення чиє, і описує чуже взуття. Адреса фото (`фото`) у промпт
    не йде: зображення стоять перед обʼєктом блоками, а рядок адреси моделі нічого не
    дає, крім домену крамниці.

    `день` — її день фактами (`сценарій.день_кодами`), `день_образу` — речення моделі
    про день обраного образу з вибору, `неповний` — ЗАЯВИ коду про те, чого
    в образі нема; без них промпт не несе ні поля, ні його рядка.
    `мова_тексту` — мова вільного тексту відповіді (`завдання.мова`): English з мовним
    шаром, Ukrainian без нього (показ шле `мова_тексту`, як рукам 3–4).
    `заміна_запасні` — ФОТО-1: `{річ: н, чому, запасні: [речі тими самими полями, що образ]}`, лише
    в зайвому виклику, коли опис назвав річ для заміни, а код знайшов запасні (`заміна_з_фото`).
    `тіло` — її фігура кодами (`hypergraph.тіло_для_опису`): без неї промпт не несе поля.
    `свідомі` — `[{н, заяви}]`: річ, яку стилістка поставила проти знахідки коду, і заяви тієї знахідки.
    """
    р = []
    for x in (речі or []):
        з = dict(н=str(x.get("н") or x.get("id") or ""), назва=str(x.get("назва") or ""))
        for к in ("слот", "тип", "частина", "магазин", "колір", "hex", "кадр_колір"):
            if x.get(к):
                з[к] = str(x[к])
        ном = [int(n) for n in (x.get("фото_номери") or [])]
        if ном:
            з["фото_номери"] = ном
        elif any(y.get("фото_номери") for y in (речі or [])):
            # ФОТО-513: коли кадри в образі є, а в цієї речі їх нема, це називається — інакше
            # модель, що лічить зображення, шукала б її кадр серед чужих (`без_кадру` → `no_photo`).
            з["без_кадру"] = True
        if x.get("її_річ"):
            з["її_річ"] = True
        р.append(з)
    об = {"версія": _ПР.ВЕРСІЯ, "образ": {"ід": str(образ or "обраний"), "речі": р}}
    if задум:
        об["задум"] = str(задум)[:120]
    # хід — номер речі з заявами знахідки, проти якої він стоїть; хід без них опис не дістає
    свід = [dict(н=str(с["н"]), заяви=list(с["заяви"])) for с in (свідомі or [])
            if isinstance(с, dict) and str(с.get("н") or "").strip() and с.get("заяви")]
    if свід:
        об["свідомі"] = свід[:4]
    укл = укладка_опису(канал_3, р)
    if укл:
        об["укладка"] = укл
    if випадок:
        об["випадок"] = str(випадок)
    # ВМ-3б (аудит/ПРОДУКТ.md п.12): той самий випадок ПОЛЯМИ (`пакет_моделі.випадок_для_пакета`)
    # — моделі він їде кодами (`дріт_моделі.випадок`), а рядок `випадок` лишається звітові. Межі
    # тут не їдуть: у опису вони окремим полем `межі` (ВМ-1).
    if isinstance(випадок_коди, dict) and випадок_коди.get("подія"):
        об["випадок_коди"] = {к: v for к, v in випадок_коди.items() if к != "вето"}
    if день:
        об["день"] = dict(день)
    if str(день_образу or "").strip():
        об["день_образу"] = str(день_образу).strip()
    # Ч-1 (п.12): «чого в образі нема» приїжджає ПОВІДОМЛЕННЯМ внутрішньою мовою
    # (`повнота_образу._коротко_жінці`) — моделі йдуть самі ЗАЯВИ, тими самими кодами, з
    # яких перекладачка складає рядок картки. Рядок сюди більше не приходить.
    _з_неп = (неповний or {}).get("statements") if isinstance(неповний, dict) else None
    if _з_неп:
        об["неповний"] = [з for з in _з_неп if isinstance(з, dict) and з.get("code")]
    _межі = [str(м).strip() for м in (межі or []) if str(м or "").strip()]
    if _межі:
        об["межі"] = _межі
    # МАК-2 (П-4): порада про рівень макіяжу — ЗАЯВИ коду; опис — єдиний текст, який
    # жінка читає цілком, тож порада, що жила лише в брифі складання, до неї не дійшла б
    # ФІГУРА (аудит/ПРОДУКТ.md п.4 — третє місце правила K-BOD-02/K-SIL-03, пояснення жінці):
    # бриф складання несе крої, якір і вузол тіла, тож опис дістає ті самі коди, щоб казати про
    # тіло; речення пише модель (п.12).
    if isinstance(тіло, dict) and тіло:
        об["тіло"] = dict(тіло)
    _мк = [з for з in (макіяж or []) if isinstance(з, dict) and з.get("code")]
    if _мк:
        об["макіяж"] = _мк
    # ── ПАЛІТРА ЖІНКИ В ОПИСІ (K-PAL-11/14/15 і прийоми) ─────────
    # Опис — єдиний текст, який жінка читає цілком. Тож у ньому метал,
    # «чого уникати» і поєднання: практиковий шар палітри не мусить
    # зникнути до найдорожчого виклику. Склад той самий,
    # що в пакеті (`palettes.для_пакета`), і без чисел — з тієї самої причини.
    if палітра:
        об["палітра"] = dict(палітра)
    if isinstance(заміна_запасні, dict) and заміна_запасні.get("запасні"):
        об["заміна_запасні"] = заміна_запасні
    об["завдання"] = {"мова": str(мова_тексту or _ЗП.МОВА_EN), "відповідь": ОПИС.вихід}
    return об


def промпт_опису(об):
    """`ОПИС_V1` обʼєктом коду → повідомлення моделі: збирач (`ОПИС`, англійською) над тими
    самими фактами кодами (`дріт_моделі.опис`); мова вільного тексту — `завдання.мова`."""
    return _ЗП.зібрати(ОПИС, _Д.опис(об), мова_тексту=((об or {}).get("завдання") or {}).get("мова"))


# ── ПІДПИС КАДРУ: ЧИЯ ЦЕ РІЧ І ЩО ЦЕ КАДР КРАМНИЦІ ─────────────────────
# «a grey wool blazer over a white top, paired with black pants» — білий топ і чорні штани стоять
# на манекені кадру піджака; пальто «worn over a black turtleneck, paired with sheer black
# tights» — з кадру пальта на моделі; «cream sweater tied at the waist … beige trousers» — з
# кадру пояса, вдягненого на светр; «silk scarf at your neck» — хустка моделі з кадру блузи.
# Кадр під голим «Photo N:» не каже, чий він, — це лише в «photos» обʼєкта ПІСЛЯ всіх кадрів.
# Код не знає, котрий кадр на моделі, тож підпис однаковий
# для кожного кадру: номер і рід речі кодами й що решта одягу в кадрі — не її образ. Двокрапку чи «not
# available» дописує показ (`підписатиКадри`): лише він знає, чи кадр дійшов
ПІДПИС_КАДРУ_EN = "Photo {N} — the shop's photo of {n} ({kind}); the other clothes in it are not in her outfit"
ПІДПИС_СВОГО_КАДРУ_EN = "Photo {N} — her own photo of {n} ({kind}); the other clothes in it are not in her outfit"


def підписи_кадрів(об, усього):
    """Підписи кадрів опису для `ОПИС_V1` обʼєктом коду: `усього` рядків, і-й — перед кадром і+1.

    Річ кадру — за «photos» дроту (`дріт_моделі.опис`), рід — її «kind» і «type»; запасна (ФОТО-1)
    має рід речі, яку вона заміняє. Кадр без речі лишається «Photo N»."""
    д = _Д.опис(об)
    рід = lambda x: ", ".join(str(x[к]) for к in ("kind", "type") if x.get(к)) or "item"
    чий = {}
    for x in д["outfit"]["items"]:
        for N in x.get("photos") or ():
            чий[N] = (ПІДПИС_СВОГО_КАДРУ_EN if x.get("hers") else ПІДПИС_КАДРУ_EN).format(N=N, n=x["n"], kind=рід(x))
    зап = д.get("swap_spares") or {}
    рід_зап = рід(next((x for x in д["outfit"]["items"] if x["n"] == зап.get("item")), {}))
    for x in зап.get("spares") or ():
        for N in x.get("photos") or ():
            чий[N] = ПІДПИС_КАДРУ_EN.format(N=N, n=x.get("n"), kind=рід_зап)
    return [чий.get(N, "Photo %d" % N) for N in range(1, int(усього) + 1)]


def опис_v1(речі, образ=None, задум=None, випадок=None, свідомі=None, фото_є=True,
            канал_3=None, палітра=None, день=None, день_образу=None, неповний=None,
            межі=None, мова_тексту=None):
    """Повідомлення моделі для опису (`промпт_опису` над `опис_обʼєкт`) — одним викликом."""
    return промпт_опису(опис_обʼєкт(речі, образ=образ, задум=задум, випадок=випадок, свідомі=свідомі,
                                    фото_є=фото_є, канал_3=канал_3, палітра=палітра, день=день,
                                    день_образу=день_образу, неповний=неповний, межі=межі,
                                    мова_тексту=мова_тексту))


def фото_доведено_коду(запис):
    """Чому КОД вважає доведеним, що на фото речі — саме ця річ; None — доказу нема.

    ЩО ЦЕ ЛІКУЄ. Позначка «фото
    крамниці може не відповідати назві» вішалась на СЛОВО моделі й тільки на
    нього: три речі з п'яти, зокрема сукня, чиє фото очевидно та сама річ. Код
    при цьому мав свідка й мовчав — `каталог_збагачення`: локальна vision-модель
    описала перший кадр КОЖНОЇ речі окремим офлайн-прогоном (`жнива_збагачення`),
    і `фото_номер` там — 1 у 10 718 записах із 10 770, тобто рівно той кадр, який
    `bridge.опис` шле моделі першим.

    ДВІ УМОВИ, І ОБИДВІ ПОТРІБНІ. `збагачення` каже, що на кадрі щось видно
    (впевненість ≥ порога; «річ не видно» — логотип, таблиця розмірів — це 0 і
    до запису не доходить). `фото_слот` каже, що видно саме ЦЕЙ рід речі: опис
    vision-моделі проганяється тим самим словником слотів, яким код судить саму
    річ (`feed.слот`). Без другої умови доказом стала б і каблучка ж-07624, чий
    опис починається «Сукня темно-зеленого кольору» при впевненості 1.0.

    БЕЗ ВХОДУ — ЧЕСНО (аудит/ПРОДУКТ.md п.4): речі без жнив, з «річ не видно» або з
    описом, який у слот не ліг, доказу не мають — позначка моделі проходить як є.
    Доказ є не для кожної речі: решта — опис назвав інший слот, «річ не видно», жнив не було чи
    опис у слот не ліг.
    """
    r = запис or {}
    if not (r.get("збагачення") and r.get("слот") and r.get("фото_слот") == r["слот"]):
        return None
    return ("на першому кадрі vision-модель описала %s — це та сама річ" % r["слот"])


# ОПИС-1 (аудит/ПРОДУКТ.md п.4 і п.12): повтор опису, що назвав річ поза образом. Код слів
# прози не читає: він звіряє лише номери з поля `названо`, яке модель заповнює сама, і повертає
# їй її ж слова («що») тих записів, у яких номера речі образу нема.
ПОВТОР_НАЗВАНОГО_EN = ("Your «text» or «how_to_wear» names things that are not items of «outfit»: %s. "
                       "Rewrite the whole answer without them — describe only the items of «outfit» — "
                       "and return the same JSON object.")


# Повтор опису, що лишив речі образу без власного запису в `про_речі`. Номери — з тієї
# самої нумерації пулу, що бачила модель; слів її прози код не читає (п.12).
ПОВТОР_НЕ_ОПИСАНО_EN = ("Your «about_items» has no entry for these items of «outfit»: %s. Give every item of "
                        "«outfit» its own entry in «about_items» — its «n» and one or two sentences about it — "
                        "and return the same JSON object.")


def _про_речі(про_речі, словник, за_ном, склад):
    """Поле `про_речі` → (рядки [(id, проза)] у порядку образу, id образу без запису, номери поза ним).

    `склад` — id картки: його порядок і є порядок рядків; без складу — порядок моделі й покриття не
    звіряється. Друга проза про ту саму річ дописується до першої, а не губиться."""
    рядки, поза = {}, []
    for x in список(про_речі):
        if not isinstance(x, dict):
            continue
        т = str(x.get("текст") or "").strip()
        н = str(x.get("н") or "").strip()
        ід = розпізнати_речі(н, словник, за_ном, поле=True)[0] if н else []
        ід = [і for і in ід if not склад or і in склад]
        if not ід:
            поза.append(н or "?")
            continue
        if т:
            рядки[ід[0]] = (рядки[ід[0]] + " " + т) if ід[0] in рядки else т
    порядок = list(склад) if склад else list(рядки)
    return ([(і, рядки[і]) for і in порядок if і in рядки],
            [і for і in (склад or []) if і not in рядки], поза)


def _названо_поза_образом(названо, словник, за_ном, склад):
    """Записи `названо` без номера речі образу → [слова моделі]. `склад` — id картки; без нього
    звіряється лише те, що номер резолвиться в річ пулу чи каталогу."""
    поза = []
    for x in список(названо):
        if not isinstance(x, dict):
            continue
        що = str(x.get("що") or "").strip()[:80]
        н = str(x.get("н") or "").strip()
        ід = розпізнати_речі(н, словник, за_ном, поле=True)[0] if н and н.lower() not in ("null", "none") else []
        if not ід or (склад and not set(ід) <= set(склад)):
            поза.append(що or н or "?")
    return поза


def опис_відповідь_з_json(текст, кандидати=None, каталог=None, склад=None, запасні=False):
    """`ОПИС_ВІДПОВІДЬ_V1` → проза для жінки, поради й речі з поганим фото (Т-06, крок 3).

    Повертає `{текст, як_носити, фото_не_те, фото_не_ті, фото_не_ті_знято, проза,
    помилки, повторний_виклик, заміна?, названо_поза_образом?, про_речі, не_описано?}`. `склад` — id речей картки:
    запис `названо` без номера речі образу (`_названо_поза_образом`) — це річ, якої
    в образі нема, і опис просять переписати (`повторний_виклик`, один повтор у показі). `заміна` (ФОТО-1) — пропозиція моделі id-ами
    (`{річ, чому, на?, на_відкинуто?}`) або `{відмова, сире}`, коли номер не резолвився; рішення — `заміна_з_фото`.
    `запасні` — чи у вході були `swap_spares` (другий опис): лише тоді «на» без речі пулу — відмова. `фото_не_ті` — id каталогу, у які резолвились
    номери речей із `фото_не_те`; вони й лягають на картку позначкою під річчю.
    `фото_не_ті_знято` — ті, кому код доказом відмовив (`фото_доведено_коду`),
    разом із причиною: зняття позначки називається, а не робиться мовчки.

    ПРОЗА ДЛЯ МОВНОГО ГЕЙТА — ЛИШЕ ТЕ, ЩО ЧИТАЄ ЖІНКА (`текст` + `як_носити`).
    Гейт над цілим JSON судив би назви полів і номери речей: «#98·29» не є
    українською мовою й не є порушенням, а R-LNG-UA шукає російське саме в прозі.

    ПОВТОРНИЙ ВИКЛИК — ЛИШЕ БЕЗ `текст` (§1(б)): опис без прози показувати нечим,
    а опис без `версія` — робочий. Те саме рішення, що в `вибір_з_json`.

    СЛАБКА МОДЕЛЬ (З-1в). Розбір іде `протокол.розбір_за_схемою`:
    «як_носити» і «фото_не_те» РЯДКОМ ітерувались би символами — на картці
    під «Як це носити» стояли б літери «К · у · р · т · к · у», а «#80·34» у
    «фото_не_те» розсипалось на «#», «8», «0», і жодна річ не діставала
    позначки. Тепер рядок — це список з одного пункту, і кожна така зміна
    лежить у `нормалізовано` (звіт власника). `текст` приймається лише рядком:
    обʼєкт чи список тут жінці не показують, а просять повтор.
    """
    словник = словник_речей(кандидати, каталог)
    за_ном = за_номером(кандидати)
    р = dict(текст=None, як_носити=[], фото_не_те=[], фото_не_ті=[], фото_не_ті_знято=[],
             проза=None, помилки=[], нормалізовано=[], обрізано=False)
    об, причина, нотатки = _ПР.розбір_за_схемою(текст, "ОПИС_ВІДПОВІДЬ_V1")
    р.update(нормалізовано=нотатки["нормалізовано"], обрізано=нотатки["обрізано"])
    if об is None:
        р["помилки"] = [dict(де="корінь", що=причина)]
    else:
        р["помилки"] = _ПР.перевірити(_ПР.СХЕМИ["ОПИС_ВІДПОВІДЬ_V1"], об)
        # ЗВЕРТАННЯ Й РІД ТРИМАЄ МОВНА МОДЕЛЬ: код не переписує «ви» на «ти» словниками
        # (`паспорт_нагоди.жінці`, кошики Б/В п.12); текст іде як є, форму велить межа `для_неї` промпту.
        _т = об.get("текст")
        р["текст"] = _т.strip() if isinstance(_т, str) and _т.strip() else None
        р["як_носити"] = [str(x).strip() for x in список(об.get("як_носити"))
                          if str(x or "").strip()][:6]
        _знято = set()
        for x in список(об.get("фото_не_те")):
            р["фото_не_те"].append(str(x))
            з, _н, _ч = розпізнати_речі(str(x), словник, за_ном, поле=True)
            for і in з:
                if і in р["фото_не_ті"] or і in _знято:
                    continue
                # ДОКАЗ КОДУ ПЕРЕВАЖУЄ СЛОВО МОДЕЛІ, І ЛИШЕ ТУТ. Склад
                # образу від цього не міняється: знімається позначка під річчю, а
                # не річ. Мовчати про зняття не можна — воно їде полем у журнал.
                доказ = фото_доведено_коду(словник.get(і))
                if доказ:
                    _знято.add(і)
                    р["фото_не_ті_знято"].append(dict(id=і, чому=доказ))
                else:
                    р["фото_не_ті"].append(і)
        # ФОТО-1 (аудит/ПРОДУКТ.md п.17): пропозиція заміни — номери стають id тією самою нумерацією пулу;
        # що не резолвилось, лишається сирим із відмовою, а не губиться (звіт власника)
        _зм = об.get("заміна")
        if isinstance(_зм, dict) and str(_зм.get("річ") or "").strip():
            _рі = розпізнати_речі(str(_зм["річ"]), словник, за_ном, поле=True)[0]
            _на = (розпізнати_речі(str(_зм["на"]), словник, за_ном, поле=True)[0]
                   if str(_зм.get("на") or "").strip() else [None])
            _причина_зміни = _зм.get("чому")
            _на_річ = {"на": _на[0]} if _на and _на[0] else {}
            # «на» БЕЗ ЗАПАСНИХ У ВХОДІ — НЕ ВІДМОВА: перший опис міг дописати вигаданий «#239·06», і
            # вся заміна йшла б `number_not_resolved`, хоч сумка резолвилась, — до запасних не
            # доходила б жодна заміна з «на». Обирати «на» можна лише з `swap_spares` (схема
            # поля), тож без них відкидається лише «на» (сирим — у `на_відкинуто`), а річ іде тим самим
            # шляхом, що заміна без «на»; відмова — коли не резолвилась річ або «на» відповіді на запасні
            _на_зайве = not запасні and not _на
            # річ, що резолвилась, лишається й при відмові: її запис `про_речі` знімає `без_прози_заміни`
            р["заміна"] = (dict(річ=_рі[0], чому=_причина_зміни, **_на_річ,
                                **({"на_відкинуто": str(_зм["на"])} if _на_зайве else {}))
                           if len(_рі) == 1 and (_на or _на_зайве) else
                           dict(відмова="number_not_resolved", сире=dict(_зм),
                                **({"річ": _рі[0]} if len(_рі) == 1 else {})))
        _поза = _названо_поза_образом(об.get("названо"), словник, за_ном, склад)
        # ── РІЧ ЗА РІЧЧЮ ─────────────────────────────────────────────────────
        # Одна проза «Чому цей образ» і звірка покриття лише номерами «named» не годилися: модель
        # називала там усі номери, а текст пропускав пальто чи піджак і описував «білі широкі
        # штани» при м'ятних. Тож кожна річ образу має свій запис `про_речі` з номером; картка читає ці записи в порядку образу, а за
        # ними — `текст`. Річ без запису — `не_описано` (номерами) і один повтор, як «named».
        _рядки, _не, _поза_п = _про_речі(об.get("про_речі"), словник, за_ном, склад)
        # Запис `про_речі` несе той самий абзац, що став рядком `текст` (ПЕРЕКЛАД-36): показ віддає мовному шару
        # кожен абзац своїм текстом із номером речі, і поділ звіряється з `текст` знак у знак.
        if _рядки and р["текст"]:
            р["текст"] = "\n".join([т for _і, т in _рядки] + [р["текст"]])
        р["про_речі"] = [dict(id=і, текст=т) for і, т in _рядки]
        _поза = _поза + [н for н in _поза_п if н not in _поза]
        if _поза:
            р["названо_поза_образом"] = _поза
        if _не:
            _ном_ід = {і: "#%s·%s" % (n, к) for n, (і, к) in (за_ном or {}).items()}
            р["не_описано"] = [_ном_ід.get(і, і) for і in _не]
    р["проза"] = "\n".join([р["текст"] or ""] + р["як_носити"]).strip() or None
    if not р["текст"]:
        р["повторний_виклик"] = _ПР.помилка_формату(
            р["помилки"][:8] or [dict(де="текст", що="required_missing")],
            відповідь="ОПИС_ВІДПОВІДЬ_V1")
    elif р.get("названо_поза_образом") or р.get("не_описано"):
        _поза, _не = р.get("названо_поза_образом") or [], р.get("не_описано") or []
        р["повторний_виклик"] = _json_ід.dumps(dict(
            version=_ПР.ВЕРСІЯ, error="named_not_in_outfit" if _поза else "items_not_described",
            **({"named": _поза[:8]} if _поза else {}), **({"not_described": _не[:8]} if _не else {}),
            answer=_ПР.НАЗВИ_ВІДПОВІДІ_EN["ОПИС_ВІДПОВІДЬ_V1"],
            instead=" ".join(([ПОВТОР_НАЗВАНОГО_EN % ", ".join("«%s»" % w for w in _поза[:8])] if _поза else [])
                             + ([ПОВТОР_НЕ_ОПИСАНО_EN % ", ".join("«%s»" % w for w in _не[:8])] if _не else []))),
            ensure_ascii=False)
    return р


def без_прози_заміни(р):
    """Опис назвав річ у `swap`, а заміни з цієї відповіді не буде → той самий розбір без запису `про_речі`
    цієї речі (за її id), з `текст` і `проза` без його абзацу; знятий запис — у `про_речі_знято`.

    `swap` сумки код відхилив, а її запис лишився —
    «Її потрібно замінити для гармонії» під річчю, яка на картці. Слів запису код не читає (п.12), тож знімає
    його цілим, без повторного виклику моделі (п.21). Прийнята заміна сюди не доходить: картку тоді описує
    відповідь на запасні (`від_моделі` з `заміна_запасні`), і цей розбір не показується."""
    ід = str(((р or {}).get("заміна") or {}).get("річ") or "")
    знято = [x for x in (р.get("про_речі") or []) if ід and str(x.get("id")) == ід]
    if not знято:
        return р
    лишились = [x for x in р["про_речі"] if x not in знято]
    _абзаци = "\n".join(x["текст"] for x in р["про_речі"])
    _власний = (р.get("текст") or "")[len(_абзаци) + 1:] if (р.get("текст") or "").startswith(_абзаци + "\n") else None
    р = dict(р, про_речі=лишились, про_речі_знято=[dict(id=ід, чому="swap_not_applied")])
    if _власний is not None:
        р["текст"] = "\n".join([x["текст"] for x in лишились] + [_власний])
        р["проза"] = "\n".join([р["текст"]] + list(р.get("як_носити") or [])).strip() or None
    return р


# домен закінчується літерою/цифрою: кома чи крапка в кінці речення («…@gepur.com.») не
# належить id
ІД_РЕГ = _re_ід.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]{1,3}-\d{2,}@[\w\-]+(?:\.[\w\-]+)*")

# ── РОЗПІЗНАВАННЯ РЕЧЕЙ: ОДНЕ ПРАВИЛО НА ДВА ВХОДИ (Т-04) ────────────────────
# Речі моделі приходять або ПОЛЕМ `речі` обʼєкта ОБРАЗИ_V1 (головний шлях), або
# прозою (рука без каталогу, модель, що не витримала формат). Пара «номер·магазин»,
# словник id і половина комплекту мусять означати ТЕ САМЕ на обох входах, тому
# правило лежить тут одне: перекладати обʼєкт НАЗАД у рядки ПІДПИС/ОБРАЗ/СВІДОМО (як
# робив би `_json_у_рядки`) не можна — поле, назване інакше, зникало б без слова, і
# `свідомо` не доїжджало б нікуди (V33).
# ПРОБІЛИ Й КРАПКА-ДВІЙНИК (З-6). Слабка модель пише «#237 · 12/верх»
# — з пробілами довкола «·» чи іншою крапкою посередині (•, ∙, ⋅, ‧, ・); такий
# номер мусить впізнаватися, інакше образ лишиться без речі. Пара й далі звіряється з
# нумерацією пулу (номер + код магазину), тож ширший запис не впускає чужої речі.
ПАРА_РЕГ = _re_ід.compile(r"#\s*(\d+)\s*[·.\-•∙⋅‧・]\s*(\d{2})(?:\s*/\s*(верх|низ|top|bottom))?(?![0-9A-Fa-f])")
# У ПОЛІ «речі» (і «фото_не_те», «прибрати», «свідомо.річ») рядок — це номер речі за
# означенням поля, тож «237·12» без «#» там однозначний; у прозі — ні (там «#» лишається
# обовʼязковим, бо саме він відрізняє номер від числа в реченні).
_ПАРА_ПОЛЯ_РЕГ = _re_ід.compile(r"^\s*(?:№\s*)?(\d+)\s*[·.\-•∙⋅‧・]\s*(\d{2})(?:\s*/\s*(верх|низ|top|bottom))?(?![0-9A-Fa-f])")
# НОМЕР БЕЗ «·» У ПОЛІ. Слабка модель пише номери складання без крапки: «#41812» замість
# «#418·12», «#45010» — «#450·10», одне «#79» замість «#79·33». Такий елемент мусить
# упізнаватися, інакше зникає навіть з `невідомі`: 0 образів, `no_outfit_in_answer`. Цілим елементом поля він — номер
# речі; прочитань два: «N·MM» без крапки (останні дві цифри — код магазину, бо код завжди з двох
# цифр) і голий «N»; «#» чи «№» обовʼязкові — без них число в полі лишається числом. Річ
# зараховується, лише коли рівно одне прочитання — річ нумерації пулу (номер і, для першого, код
# магазину збіглись); обидва чи жодне — номер іде в `невідомі` під своїм написанням.
_НОМЕР_БЕЗ_КРАПКИ_РЕГ = _re_ід.compile(r"^\s*(?:#|№)\s*(\d+)\s*(?:/\s*(верх|низ|top|bottom)\s*)?$")
# ПОЛОВИНА КОМПЛЕКТУ АНГЛІЙСЬКИМ ДРОТОМ (П-2): промпт складання англійський і просить «/top» чи
# «/bottom»; у складі образу половина лишається словом ядра («верх»/«низ»), як доти.
_ПОЛОВИНА = {"top": "верх", "bottom": "низ"}


def список(v):
    """Поле, яке схема оголошує списком, — списком: рядок стає списком з одного
    (а не літерами), обʼєкт — списком з одного, порожнє — порожнім."""
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, (str, dict)):
        return [v] if v else []
    return []


def словник_речей(кандидати=None, каталог=None):
    """id → запис речі: спершу каталог, далі пул (слот бере з ключа пулу, якщо в записі нема)."""
    словник = {}
    for r in (каталог or []):
        if r.get("id"):
            словник[r["id"]] = r
    for сл, пул in (кандидати or {}).items():
        for r in пул:
            # кандидати пакета не несуть `слот` у записі — слот є ключем пулу
            if r.get("id"):
                словник.setdefault(r["id"], dict(r, слот=r.get("слот") or сл))
    return словник


def за_номером(кандидати=None):
    """номер «#412» → (id, код магазину): та сама нумерація, що бачила модель."""
    if not кандидати:
        return {}
    _ном, _коди = номери_речей(кандидати)
    return {n: (і, к) for і, (n, к) in _ном.items()}


def _номер_без_крапки(де, за_ном):
    """Елемент поля номерів без «·» («#41812», «#79») → (id, номер «№N·MM», половина, написання) або None,
    коли це не такий елемент. id None — номер неоднозначний чи поза нумерацією пулу
    (`_НОМЕР_БЕЗ_КРАПКИ_РЕГ`)."""
    м = _НОМЕР_БЕЗ_КРАПКИ_РЕГ.match(де)
    if not м:
        return None
    ц = м.group(1)
    голий = за_ном.get(int(ц))
    злитий = за_ном.get(int(ц[:-2])) if len(ц) >= 3 else None
    прочитання = ([(голий[0], "#%s·%s" % (ц, голий[1]))] if голий else []) + (
        [(злитий[0], "#%s·%s" % (ц[:-2], ц[-2:]))] if злитий and злитий[1] == ц[-2:] else [])
    і, номер = прочитання[0] if len(прочитання) == 1 else (None, None)
    return і, номер, _ПОЛОВИНА.get(м.group(2), м.group(2)), де.strip()


def розпізнати_речі(де, словник, за_ном=None, поле=False, двічі=None, без_крапки=None):
    """Один рядок (проза або елемент поля `речі`) → (id, невірні пари, половини комплекту).

    `двічі` — необовʼязковий список викликача: сюди падає id, який рядок назвав ДВІЧІ
    (той самий id або той самий номер «#N·MM» удруге). id і
    номер ТІЄЇ САМОЇ речі поруч — одна згадка, не дві, і сюди не йдуть.

    `без_крапки` — так само список викликача: номер без «·», зарахований цілим елементом поля
    (`_номер_без_крапки`), — `{написано, номер}`.

    `поле=True` — рядок є ЕЛЕМЕНТОМ поля, яке схема оголошує номерами речей
    (`речі`, `фото_не_те`, `прибрати`, `свідомо.річ`): там номер без «#» («237·12»)
    теж номер. У прозі «#» лишається обовʼязковим.

    РОЗБІЖНІСТЬ КОДУ МАГАЗИНУ — ПОМИЛКА, А НЕ ПІДКАЗКА. Голий номер резолвився б
    у реальну, але іншу річ, і помилка моделі стала б тихою підміною. Тому пара
    звіряється: номер каже, ЯКА річ, код магазину — чи це та сама річ. Не збіглось
    — річ не зараховується й іде в `невідомі` під власним написанням.

    ПАРА ОБОВʼЯЗКОВА, І ЦЕ НЕ СУВОРІСТЬ, А ЗАХИСТ ВІД HEX. Перша версія приймала
    голий «#412», і регекс ловив `#4a4a4a` як річ номер 4: колір у прозі мовчки
    ставав чужою річчю. Промпт і так просить обидві частини («#412·29»), тож вимога
    збігається з контрактом. Заборона hex-хвоста окремо: «#41·29ab» — не наша пара.
    Без нумерації (`за_ном` порожній) пари не судяться взагалі: сказати «невірна»
    там, де нумерації не існує, означало б звинуватити модель у своїй же відсутності.
    """
    знайдені = [м.group(0) for м in ІД_РЕГ.finditer(де)]
    if двічі is not None:
        двічі += [і for n, і in enumerate(знайдені) if і in знайдені[:n] and і not in двічі]
    # id поза регексом (інший словник магазину) — точний підрядковий збіг
    for і in словник:
        if і not in знайдені and і in де:
            знайдені.append(і)
    невірні, частини = [], {}
    if за_ном:
        пари = list(ПАРА_РЕГ.finditer(де))
        if not пари and поле:
            пари = list(_ПАРА_ПОЛЯ_РЕГ.finditer(де))
        номери = []
        for м in пари:
            n = int(м.group(1)); к = м.group(2)
            пара = за_ном.get(n)
            if пара and к == пара[1]:
                if двічі is not None and n in номери and пара[0] not in двічі:
                    двічі.append(пара[0])    # той самий номер удруге — друга згадка
                номери.append(n)
                if пара[0] not in знайдені:
                    знайдені.append(пара[0])
                if м.group(3):
                    частини[пара[0]] = _ПОЛОВИНА.get(м.group(3), м.group(3))   # половина комплекту названа явно
            else:
                невірні.append(м.group(0).strip())
        # номер без «·»: лише цілим елементом поля; неоднозначний — у невірні, як пара,
        # що не зійшлась, і зараховане теж називається (`без_крапки`) — склад не міняється мовчки
        бк = _номер_без_крапки(де, за_ном) if (поле and not пари and not знайдені) else None
        if бк and бк[0]:
            знайдені.append(бк[0])
            if бк[2]:
                частини[бк[0]] = бк[2]
            if без_крапки is not None:
                без_крапки.append(dict(написано=бк[3], номер=бк[1]))
        elif бк:
            невірні.append(бк[3])
    return знайдені, невірні, частини


def запис_образу(знайдені, невірні, словник, джерело, частини=None, за_назвою=None, чому=None,
                  двічі=None):
    """Спільний контракт виходу обох розборів: що зараховано, що ні і чому.

    `двічі` — речі, які модель назвала в образі двічі: у склад вони йдуть один раз, а зведення
    їде полем, а не зникає.

    НЕВІРНІ ПАРИ ЇДУТЬ ОКРЕМИМ КАНАЛОМ. Змішати їх з `невідомі` означало б
    втратити різницю між «модель назвала річ, якої нема» і «модель назвала номер,
    що не сходиться з магазином» — а це різні хвороби з різним лікуванням.
    """
    ід, невідомі, бачено = [], [], set()
    for і in знайдені:
        if і in бачено:
            continue
        бачено.add(і)
        (ід if і in словник else невідомі).append(і)
    # ── РІЧ ЖІНКИ З ФОТО — У КОЖНОМУ ОБРАЗІ, І ЇЇ СЛОТ ОДИН ───────
    # Тримає КОД, на кожному розборі (JSON і проза обидва ходять сюди): модель, що
    # забула річ, дістає її назад, а друга річ у її слоті знімається — і обидві
    # зміни лягають у запис (`закріплено`), а не зникають мовчки. Без фото в
    # словнику закріплених речей нема, і склад той самий.
    ід, _закріплено = _РФ.закріпити_в_образі(ід, словник)
    слоти = {}
    for і in ід:
        слоти.setdefault(словник[і].get("слот"), []).append(і)
    двічі = [і for і in dict.fromkeys(двічі or []) if і in ід]
    return dict(частини=dict(частини or {}), готово=bool(ід), ід=ід, джерело=джерело,
                невідомі=невідомі + list(невірні), невірні_пари=list(невірні),
                за_назвою=list(за_назвою or []),
                слот_двічі={с: v for с, v in слоти.items() if len(v) > 1},
                **({"двічі": двічі} if двічі else {}),
                чому=(None if ід else (чому or "no_known_id")),
                **({"закріплено": _закріплено} if _закріплено else {}))


def _ехо_записом(ехо):
    """Ехо вхідного вердикта (`протокол._без_ехо`) → запис «образу нема» з причиною.

    Словник порожній навмисно: із реальним `закріпити_в_образі` доклав би її річ з
    фото до порожнього складу, і з ехо вийшов би «образ» з однієї речі. `ехо` —
    ознака для `міст_відповіді.від_моделі`: такий текст не йде шляхом рук без
    каталогу (hex у переписаному чеклісті там прочитався б вигаданою річчю)."""
    код = "verdict_echo:" + ",".join(str(е.get("де")) for е in ехо)
    return dict(запис_образу([], [], {}, "поле «речі»", чому=код),
                ехо=True)


_КЛЮЧ_JSON = _re_ід.compile(r'"([^"\n]{1,24})"\s*:')


def _зламаний_json_образів(текст, причина):
    """Запис «образу нема», коли відповідь — ОБРАЗИ_V1, що не розбирається; інакше None.

    ЩО ЦЕ ЛІКУЄ (Л-4). JSON, який не лагодиться
    (`протокол._закрити`), падав у розбір прози: рядків «ОБРАЗ:» у ньому нема, і
    `ід_з_тексту` збирав УСІ номери тексту в один образ — 20–26 речей із п'яти образів,
    0 помилок схеми, без повторного виклику, і цей злитий образ ішов на картку з рядком
    «лиши по одній у кожному слоті». Тепер відповідь із ключами «образи»/«речі» (з
    латинськими двійниками, `протокол.візерунок_ключа`) — це JSON ОБРАЗИ_V1, і коли він
    не розібрався, образів у ній нема: `від_моделі` називає помилку схеми й просить
    повтор, як на будь-якій відповіді без образів. Проза («ОБРАЗ: …», руки без каталогу)
    сюди не доходить — у ній ключів JSON нема."""
    т = str(текст or "")
    if "{" not in т and "[" not in т:
        return None
    # КЛЮЧІ ДРОТУ — ТЕЖ ОБРАЗИ_V1 (РЕМОНТ-2). Модель пише англійським дротом («outfits»,
    # «items»), тож впізнаються й вони, а не лише «образи»/«речі» з латинськими двійниками:
    # інакше зламана англійська відповідь ремонту падала б в `ід_з_тексту`, і з п'яти
    # образів складався б один на 25 речей.
    візерунки = (_ПР.візерунок_ключа("образи"), _ПР.візерунок_ключа("речі"),
                 _re_ід.compile("^(?:%s|%s)$" % (_ПР.КЛЮЧІ_ВІДПОВІДІ_EN["образи"],
                                                 _ПР.КЛЮЧІ_ВІДПОВІДІ_EN["речі"])))
    if not any(в.match(к.strip().lower()) for к in _КЛЮЧ_JSON.findall(т) for в in візерунки):
        return None
    return dict(запис_образу([], [], {}, "JSON ОБРАЗИ_V1",
                              чому="outfits_json_unparsed"),
                json_не_розібрано=True)


def це_образи(об):
    """Чи це відповідь із образами: ОБРАЗИ_V1 (`образи`) або ОДИН образ обʼєктом
    (`речі`/`образ`). Вибір сюди з Т-06 не заходить: `ВИБІР_V1` несе `обрано`, а не
    склад, і його читає `вибір_з_json`."""
    return isinstance(об, dict) and bool(об.get("образи") or об.get("речі") or об.get("образ"))


def образи_з_json(об, кандидати=None, каталог=None):
    """ОБРАЗИ_V1 (`протокол.ОБРАЗИ_V1`) → той самий запис на образ, що й розбір прози.

    Читає ПОЛЯ, не рядки: `речі` — номери «#12·03» або id, `підпис` — задум,
    `свідомо` — оголошені ходи `[{річ, чому}]`. Один образ обʼєктом теж приймається.

    ЩО ЦЕ ЛІКУЄ (Т-04, V33). Доти JSON ішов крізь `_json_у_рядки`: кожен обʼєкт
    розкладався назад у рядки, `свідомо` перетворювалось на `str(dict)`, і адресата
    оголошення в тому рядку не було — тобто на JSON-шляху оголошений хід НІКОЛИ
    нічого не послаблював, хоч модель його й казала. Тепер адресат їде полем `ід`
    розриву (`_свідомі_з_json`), а не вгадується з тексту.

    `ід` образу від моделі — полем `ід_відповіді`: ремонт називає ним образ вердикта, який
    лагодив, і `номер` запису (позиція у відповіді) цього не каже; читачі — міст (які образи взяти, коли
    відповідь дала більше, ніж просили) і запис образу, тобто звіт і заміри.
    ЧОГО ТУТ НАВМИСНО НЕ ПЕРЕНОСИТЬСЯ: `полюс` образу від моделі — читача в
    ньому ще нема (полюси набору — Т-10), а поле без читача виглядає як робочий канал
    і мовчки ним не є. `виконано` читача вже має, але ЧИТАЄ ЙОГО НЕ ЗВІДСИ:
    `перевірити_виконання` (Т-05) бере поле з самого обʼєкта ОБРАЗИ_V1, бо йому
    потрібні ще два входи, яких у записі образу нема й не буде, — попередній вердикт
    і новий суд. Дублювати поле в запис означало б другий канал для одного факту.
    """
    словник = словник_речей(кандидати, каталог)
    за_ном = за_номером(кандидати)
    образи = об.get("образи") if isinstance(об.get("образи"), list) else [об]
    вих = []
    for о in образи:
        if not isinstance(о, dict):
            continue
        речі = о.get("речі") or о.get("образ") or []
        if isinstance(речі, str):
            речі = [речі]
        знайдені, невірні, частини, двічі, половини, без_крапки = [], [], {}, [], {}, []
        голі, з_елементів = [], []
        for x in речі:
            _бк = len(без_крапки)
            з, н, ч = розпізнати_речі(str(x), словник, за_ном, поле=True, двічі=двічі, без_крапки=без_крапки)
            # голий «N» — прочитання без коду магазину: цифри написаного й є номером (злите «N·MM» — ні)
            if len(без_крапки) > _бк and без_крапки[-1]["номер"][1:].split("·")[0] == \
                    _НОМЕР_БЕЗ_КРАПКИ_РЕГ.match(без_крапки[-1]["написано"]).group(1):
                голі.append((без_крапки[-1], з[-1]))
            з_елементів.append(з)
            двічі += [і for і in з if і in знайдені and і not in двічі]
            for і in з:
                половини.setdefault(і, set()).add(ч.get(і) or "")
            знайдені += [і for і in з if і not in знайдені]
            невірні += н
            частини.update(ч)
        # ГОЛИЙ «№N» ПОРУЧ ІЗ НОМЕРАМИ ПОЗА ПУЛОМ — ЗБІГ, А НЕ РІЧ: «#79» зараховано б як «#79·33»,
        # а решта образу — «#4230», «#3038», «#2960» — поза пулом: вигадане число випадково
        # влучило в нумерацію. Код судить лише номери: коли бодай один
        # номер образу не резолвився, голий «N» без коду магазину річчю не стає й іде в `невірні` під своїм
        # написанням; злите «N·MM» без крапки (код магазину збігся) лишається
        if голі and невірні:
            for бк, і in голі:
                if sum(і in з for з in з_елементів) == 1:
                    знайдені.remove(і)
                    частини.pop(і, None)
                    половини.pop(і, None)
                    без_крапки.remove(бк)
                    невірні.append(бк["написано"])
        # КОМПЛЕКТ, НАЗВАНИЙ ДВІЧІ РІЗНИМИ ПОЛОВИНАМИ («/верх» і «/низ», або цілим і
        # половиною), — це цілий комплект: інакше мовчки перемагала б остання
        # половина, і образ судився б без другої. Зведення назване полем `двічі`.
        for і, п in половини.items():
            if len(п) > 1:
                частини.pop(і, None)
        запис = запис_образу(знайдені, невірні, словник, "поле «речі»", частини,
                              чому="items_field_no_id",
                              двічі=двічі)
        if без_крапки:
            запис["без_крапки"] = без_крапки
        # ПІДПИС — 3–5 слів задуму, не пояснення. Друга ітерація відрізняє за ним
        # свідомий експеримент від огріху; без нього вона бачить лише номери.
        if о.get("підпис"):
            запис["підпис"] = str(о["підпис"]).strip()[:60]
        if str(о.get("ід") or "").strip():
            запис["ід_відповіді"] = str(о["ід"]).strip()
        # ДЕНЬ ОБРАЗУ — речення моделі, як цей образ проживе її день. Читачі:
        # ремонт і вибір (`ОБРАЗ_ВЕРДИКТУ.день`), опис обраного (`ОПИС_V1.день_образу`),
        # звіт власника; і мовний гейт — це проза моделі, як підпис і «чому».
        if str(о.get("день") or "").strip():
            запис["день"] = str(о["день"]).strip()
        # Склад — той, що вийшов після закріплення її речі (`_запис_образу`): оголошення
        # мусить стосуватись речі цього складу, а не пулу (Л-4).
        _поза = []
        запис["свідомі"] = свідомі_з_json(о.get("свідомо"), словник, за_ном,
                                           склад=запис.get("ід") or [], поза=_поза)
        if _поза:
            запис["свідомі_поза"] = _поза
        # `текст` лишається в записі, але на JSON-шляху несе ЛИШЕ ПРОЗУ моделі
        # (підпис, «чому», причини оголошених ходів): єдиний його читач —
        # мовний гейт (`перевірити_від_моделі`), а він судить саме прозу. Номери й
        # поля туди не йдуть: «#12·03» не є українською мовою й не є порушенням.
        проза = [str(о[k]).strip() for k in ("підпис", "чому", "день") if str(о.get(k) or "").strip()]
        проза += [str(с.get("чому") or "").strip() for с in запис["свідомі"] + _поза if с.get("чому")]
        запис["текст"] = "\n".join(проза) or None
        вих.append(запис)
    return вих


def образи_з_тексту(текст, кандидати=None, каталог=None):
    """N образів з ОДНІЄЇ відповіді: по розбору на кожен рядок «ОБРАЗ: id, id, …».

    ЩО ЦЕ МІНЯЄ (правило 3): `ід_з_тексту` бере ОСТАННІЙ рядок «ОБРАЗ:» і мовчки
    викидає попередні — це було правильно, поки пакет просив один образ, і стало
    блокером, щойно цикл став «ші пропонує N, код судить кожен».

    Порядок у списку — порядок появи в тексті, НЕ ранг: кількість зауважень не є
    оцінкою (R-ABC-08), і менше ремонту не робить кандидата кращим.

    Порожній список НЕ повертається: якщо жодного рядка «ОБРАЗ:» нема, віддається
    один розбір по всьому тексту — рівно те, що робила `ід_з_тексту`, бо «модель
    не вжила формат» не те саме, що «модель нічого не запропонувала».

    ФОРМА НЕ ВАЖИТЬ БІЛЬШЕ ЗА НАМІР. JSON читає
    `протокол.розбір_за_схемою`: «обрazi» — це «образи», масив образів без
    обгортки — теж образи, а з відповіді, що обірвалась об стелю виводу,
    беруться ЦІЛІ образи (недописаний — ні). Доти будь-що з цього ішло в розбір
    прози, і з десяти образів виходив один «образ» з усіх речей підряд.

    JSON — ГОЛОВНИЙ ШЛЯХ, ПРОЗА — ЗАПАС (Т-04). Доти будь-яка відповідь спершу
    йшла крізь `_json_у_рядки` (обʼєкт → рядки → регулярки), і поле, назване
    інакше, зникало без слова. Тепер обʼєкт читає `образи_з_json` полями, а розбір
    рядків лишається там, де він єдиний можливий: відповідь прозою.
    """
    об, _чому, нот = _ПР.розбір_за_схемою(текст, "ОБРАЗИ_V1")
    if це_образи(об):
        return образи_з_json(об, кандидати=кандидати, каталог=каталог)
    # ЕХО ВХОДУ ПРОЗОЮ НЕ ЧИТАЄТЬСЯ (Т-7). Вердикт, переписаний назад, — це JSON без
    # жодного образу відповіді, і розбір прози склав би з нього один «образ» з усіх
    # номерів, що стоять у знахідках і вітрині, — з речей, яких модель не обирала.
    if нот.get("ехо"):
        return [_ехо_записом(нот["ехо"])]
    текст = str(текст or "")
    рядки_т = текст.split("\n")
    _обр = [i for i, l in enumerate(рядки_т)
            if _re_ід.match(r"\s*ОБРАЗ\s*[:：]", l, _re_ід.I)]
    if not _обр:
        _злам = _зламаний_json_образів(текст, _чому)
        if _злам:
            return [_злам]
        return [ід_з_тексту(текст, кандидати=кандидати, каталог=каталог)]
    # ── БЛОК НА ОБРАЗ, А НЕ ОДИН ТЕКСТ НА ВСІХ ────────────────────────────────
    # ЩО ЦЕ МІНЯЄ (правило 3, before/after). Рядок «СВІДОМО: <річ> — <чому>» —
    # єдиний спосіб, яким ші каже «це не огріх, це хід». Код його читає
    # (`свідомі_розриви`) і послаблює відповідну знахідку в 0.6 раза.
    #   before — `_вердикти_образів` судив кожен образ БЕЗ тексту взагалі, тож на
    #            N образів жоден свідомий розрив не доходив нікуди: ші пояснила,
    #            код не почув, і друга ітерація діставала свій же навмисний хід у
    #            списку «що знайшов код» — тобто її просили полагодити те, що вона
    #            зробила навмисно. Рівно те, від чого підпис і рядок СВІДОМО й
    #            вигадувались.
    #   after  — кожен образ несе свій блок тексту, і його розрив judиться його ж
    #            поясненням. Передати натомість УВЕСЬ текст було б не краще, а
    #            гірше: пояснення третього образу мовчки послаблювало б знахідку в
    #            сьомому, і сила правила поповзла б без жодного сліду.
    # МЕЖА БЛОКУ. Усе до рядка «ОБРАЗ:» включно (з його ПІДПИСОМ) належить цьому
    # образу; рядки «СВІДОМО:» одразу ПІСЛЯ нього — теж йому, бо саме там їх
    # природно писати. Перший непорожній рядок іншого роду закриває блок.
    # ПОЗИЦІЙНЕ ПРАВИЛО ЖИВЕ ТІЛЬКИ ТУТ — У РОЗБОРІ ПРОЗИ (Н-V33-061, крок 4). Доти
    # цей абзац стояв ще й у `_формат_відповіді`, тобто код ПРОСИВ модель ставити
    # рядок під «ОБРАЗ:» — і тим самим промптом вимагав JSON, де позицію задає
    # структура. Просити більше нема кому: ПАКЕТ_V1 називає поле «свідомо», і в
    # обʼєкті оголошення стоїть УСЕРЕДИНІ свого образу — позицію задає структура,
    # а не порядок рядків (Т-04: `образи_з_json`). Правило лишається робочим для
    # відповідей, які ВСЕ Ж приходять прозою (рука без каталогу, модель, що не
    # витримала формат), і в цьому його єдиний сенс.
    блоки, поч = [], 0
    for i in _обр:
        кін, j = i, i + 1
        while j < len(рядки_т):
            л = рядки_т[j].strip()
            if not л:
                j += 1; continue
            if СВІДОМО_РЕГ.match(рядки_т[j]):
                кін = j; j += 1; continue
            break
        блоки.append("\n".join(рядки_т[поч:кін + 1]))
        поч = кін + 1
    вих = []
    for б in блоки:
        о = ід_з_тексту(б, кандидати=кандидати, каталог=каталог)
        п = _re_ід.search(r"ПІДПИС\s*[:：]\s*(.+)", б, _re_ід.I)
        # ПІДПИС — 3–5 слів задуму, не пояснення. Друга ітерація відрізняє за ним
        # свідомий експеримент від огріху; без нього вона бачить лише id.
        if п: о["підпис"] = п.group(1).strip()[:60]
        о["текст"] = б
        о["свідомі"] = свідомі_розриви(б)
        вих.append(о)
    return вих


def ід_з_тексту(текст, кандидати=None, каталог=None):
    """Модель відповідає ТЕКСТОМ; код чекає список id. Це і є шов, якого не було:
    `перевірити_від_моделі` брав готовий `ід`, і стенду довелося б парсити прозу
    самому — на кожній платформі по-своєму.

    Порядок розпізнавання, від найпевнішого:
      1. рядок «ОБРАЗ: id, id, …» (його просить пакет) — беремо ЛИШЕ його;
      2. усі id словника каталогу, що трапились у тексті;
      3. назви кандидатів (нормалізовані, ≥ 12 символів) — лише коли для слота ще
         нема id, і це ПОЗНАЧАЄТЬСЯ («за_назвою»), бо збіг назви слабший за id.
    Не вигадує: id поза словником іде в `невідомі`, два id в одному слоті — у
    `слот_двічі` (модель обрала «або», а не «і»), порожня відповідь — `готово=False`.

    JSON СЮДИ ТЕЖ ДОХОДИТЬ (Т-04) — від викликача, який має лише текст. Тоді
    береться ОСТАННІЙ образ: верхній рівень `перевірити_від_моделі` і є вердиктом
    по останньому образу (`bridge.від_моделі`, коментар біля `в["образи"]`), і так
    само поводився розбір прози — він брав останній рядок «ОБРАЗ:»."""
    об, _чому, нот = _ПР.розбір_за_схемою(текст, "ОБРАЗИ_V1")
    if це_образи(об):
        образи = образи_з_json(об, кандидати=кандидати, каталог=каталог)
        return (образи[-1] if образи else
                запис_образу([], [], {}, "поле «речі»",
                              чому="json_without_outfit_items"))
    if нот.get("ехо"):          # вердикт, переписаний назад, — не проза з образом (Т-7)
        return _ехо_записом(нот["ехо"])
    if not _re_ід.search(r"ОБРАЗ\s*[:：]", str(текст or ""), _re_ід.I):
        _злам = _зламаний_json_образів(текст, _чому)   # Л-4: зламаний JSON — не проза
        if _злам:
            return _злам
    текст = str(текст or "")
    частини = {}     # id → «верх»|«низ», коли модель узяла ПОЛОВИНУ комплекту («#12·03/низ»)
    словник = словник_речей(кандидати, каталог)
    рядок = None
    for м in _re_ід.finditer(r"ОБРАЗ\s*[:：]\s*(.+)", текст, _re_ід.I):
        рядок = м.group(1)                     # останній такий рядок — фінальний
    джерело = "рядок ОБРАЗ" if рядок else "id у тексті"
    _де = рядок if рядок else текст
    # НОМЕР+МАГАЗИН І СЛОВНИК id — ОДНЕ ПРАВИЛО НА ОБА ВХОДИ (`_розпізнати_речі`).
    двічі = []
    знайдені, невірні, _част = розпізнати_речі(_де, словник, за_номером(кандидати), двічі=двічі)
    частини.update(_част)
    ід = [і for і in dict.fromkeys(знайдені) if і in словник]
    за_назвою = []
    # НАЗВА — ЛИШЕ КОЛИ РЯДКА «ОБРАЗ:» НЕМА. Рядок і є контракт;
    # добирати до нього речі з прози означало б, що згадана в поясненні й
    # ВІДКИНУТА річ («сумку лишаю вдома») мовчки стає частиною образу — і
    # тестувальниця судила б річ, якої модель не обирала.
    if кандидати and not рядок:
        зайняті = {словник[і].get("слот") for і in ід}
        норм = lambda s: _re_ід.sub(r"\s+", " ", str(s or "").lower()).strip()
        т = норм(текст)
        # Її річ з фото за назвою не шукається: у руках 1–2 її ставить закріплення
        # (`річ_з_фото.закріпити_в_образі`), а в тексті руки без каталогу (3–4) її назва
        # перемкнула б розбір вигаданих речей на каталожний — з однією річчю замість образу.
        for сл, пул in кандидати.items():
            if сл in зайняті: continue
            збіги = [r for r in пул if r.get("назва") and len(норм(r["назва"])) >= 12 and норм(r["назва"])[:40] in т
                     and not str(r.get("id") or "").startswith(_РФ.ПРЕФІКС_ІД)]
            if len(збіги) == 1:
                ід.append(збіги[0]["id"]); за_назвою.append(збіги[0]["id"]); зайняті.add(сл)
            elif len(збіги) > 1:
                за_назвою.append(dict(слот=сл, неоднозначно=[r["id"] for r in збіги]))
    return запис_образу(ід + [і for і in знайдені if і not in словник], невірні, словник,
                         джерело, частини, за_назвою,
                         чому="text_no_id_no_candidate_name",
                         двічі=двічі)


СВІДОМО_РЕГ = _re_ід.compile(r"^\s*(?:СВІДОМО|Свідомо|свідомо|НАВМИСНО|Навмисно|навмисно)\s*[:—–-]\s*(.+?)\s*$", _re_ід.M)
_СЛУЖБОВИЙ_НОМЕР = _re_ід.compile(r"#(?![0-9a-fA-F]{6}\b)\d+")   # шестизначний hex-колір не є службовим номером
СВІДОМИЙ_МНОЖНИК = 0.6   # той самий коефіцієнт, що K-KOH-03 дає ОДНОМУ свідомому розриву (T3)

def свідомі_розриви(текст):
    """Рядки «СВІДОМО: <річ> — <чому>» з ПРОЗОВОЇ відповіді моделі. Бриф давно велить
    моделі «умову порушуй свідомо й скажи одним рядком, яку саме і чому» — але
    зворотного шляху має бути: `від_моделі` читає цей рядок, інакше оголошений розрив
    судився б як неоголошений; формат і є контрактом.

    JSON СЮДИ НЕ ЗАХОДИТЬ (Т-04): в ОБРАЗИ_V1 оголошення — це поле `свідомо` образу,
    і читає його `_свідомі_з_json`. Доти обʼєкт доїжджав сюди рядком «СВІДОМО:
    {'річ': …, 'чому': …}» від `_json_у_рядки` — розрив ЗНАХОДИВСЯ, але адресата в
    ньому не було (номер речі не дорівнює id каталогу), тож він не послаблював
    нічого. Саме це й є V33: код чув оголошення й мовчки його втрачав."""
    return [dict(текст=м.group(1)) for м in СВІДОМО_РЕГ.finditer(str(текст or ""))]


def свідомі_з_json(свідомо, словник, за_ном=None, склад=None, поза=None):
    """Поле `свідомо` образу (`[{річ, чому}]`) → ті самі розриви, що дає проза, плюс
    АДРЕСАТ полем: `ід` — id речі, яку модель назвала номером «#12·03».

    Чому адресат полем, а не пошуком у тексті: номер речі — це нумерація ПАКЕТА, а
    знахідки коду стоять над id і назвами каталогу. Пошук номера в тексті розриву
    не знаходив нічого й тихо давав `без_адресата` — оголошення зникало (V33).
    Оголошення про образ у цілому (`річ` порожня або «образ») лишається без `ід`:
    його адресата шукає `_застосувати_свідомі` словами, як і в прозі.

    `текст` — НАЗВОЮ РЕЧІ, а не номером, коли номер резолвився. Його читають промпт
    вибору (`_шапка_вибору`) і журнал: у кожного з них свій виклик і свіжий контекст,
    де «#26·28» нічого не значить — нумерація живе в ПАКЕТІ, а не у всіх промптах.
    Машинний адресат від цього не залежить: він у `ід`, а номер, як його написала
    модель, лишається в `річ`. НАЗВА — ЦІЛА (Л-4): стеля `[:40]` різала б її
    посеред слова («…бантом м'»), і цей обрубок дійшов би до жінки через опис.

    ОГОЛОШЕННЯ ПРО РІЧ ПОЗА ОБРАЗОМ — НЕ ОГОЛОШЕННЯ ОБРАЗУ (Л-4). `склад` — id
    речей образу: адресат, якого в ньому нема, знімається; оголошення, в якого адресата
    не лишилось зовсім, у вихід не йде, а дописується в `поза` (список викликача) — у
    звіт, не мовчки. Без цього ремонт міг оголосити «#48·14» (берет) при образі без
    берета, і берет доїхав би через вибір до опису: «Чому цей образ» двічі про річ, якої
    на картці нема. Без `склад` адресата шукають по всьому пулу."""
    вих = []
    _склад = set(склад) if склад is not None else None
    # РЯДОК ЗАМІСТЬ СПИСКУ: «свідомо»: "сукня — навмисно" ітерувалось би символами й давало
    # б оголошення на кожну літеру; це одне оголошення.
    for с in список(свідомо):
        якщо_рядок = isinstance(с, str)
        річ = "" if якщо_рядок else str((с or {}).get("річ") or "").strip()
        чому = str(с if якщо_рядок else (с or {}).get("чому") or "").strip()
        if not річ and not чому:
            continue
        if _СЛУЖБОВИЙ_НОМЕР.search(чому):
            if поза is not None:
                поза.append(dict(річ=річ, чому=чому, код="service_id_in_reason"))
            continue
        р = dict(чому=чому)
        # АДРЕСА ХОДУ — КОД ЗНАХІДКИ: `знахідка` — ід, яким модель назвала знахідку
        # вердикта («з-о5-2»); `правило` — її код, коли оголошення складає сам код («відхилено»
        # ремонту, «прийнято» вибору). Ід у код переводить `адресувати_знахідками` — там, де
        # вердикт, на який модель відповідала, ще під рукою.
        for _к in ("знахідка", "правило"):
            if not якщо_рядок and str((с or {}).get(_к) or "").strip():
                р[_к] = str(с[_к]).strip()
        назва = річ
        if річ:
            р["річ"] = річ
            знайдені, _невірні, _ч = розпізнати_речі(річ, словник, за_ном, поле=True)
            ід = [і for і in знайдені if і in словник]
            if ід and _склад is not None:
                _свої = [і for і in ід if і in _склад]
                if not _свої:
                    if поза is not None:
                        поза.append(dict(річ=річ, чому=чому, ід=list(ід)))
                    continue
                ід = _свої
            if ід:
                р["ід"] = ід[0]
                # ОГОЛОШЕННЯ НАД КІЛЬКОМА РЕЧАМИ МАЄ СТІЛЬКИ Ж АДРЕСАТІВ. Перший id
                # для поля `свідомо` — майже завжди одна річ, і різниці не видно. Але хід,
                # оголошений через «виконано: відхилено», стоїть над ЗНАХІДКОЮ, а
                # знахідка буває над двома-трьома речами: один адресат із трьох
                # означав би, що код послаблює третину того, що ші оголосила.
                if len(ід) > 1:
                    р["ід_речей"] = list(ід)
                # назва ТА САМА, ЩО НА КАРТЦІ Й У ПУЛІ: не сира назва фіду з
                # HTML-сутностями й артикулом, а та, якою річ бачать жінка й модель
                назва = ", ".join(_ФС.назва_для_людини(словник[і]) or річ for і in ід)
        р["текст"] = ("%s — %s" % (назва, чому)).strip(" —") if назва else чому
        вих.append(р)
    return вих


def адресувати_знахідками(розриви, вердикт):
    """Оголошення, що назвало знахідку вердикта (`знахідка`), → те саме оголошення з її кодом
    (`правило`). `вердикт` — ВЕРДИКТ_V1, на який модель відповідала: ід «з-о5-2» живе лише в
    ньому, а новий суд нумерує знахідки наново, тож переклад — тут, а не в суді.

    Модель може назвати знахідку й кодом заяви, під яким бачила її на дроті
    («open_zones_over_limit»): тоді код — правило знахідок вердикта з цією заявою, коли воно
    одне. Ід, якого у вердикті нема, лишається без `правило` — оголошення читається, але не
    послаблює нічого (`_застосувати_свідомі`), і звіт це називає (`без_коду`)."""
    if not розриви or not isinstance(вердикт, dict):
        return розриви
    зн = [z for о in (вердикт.get("образи") or []) if isinstance(о, dict)
          for z in (о.get("знахідки") or []) if isinstance(z, dict)]
    зн += [z for z in ((вердикт.get("набір") or {}).get("знахідки") or []) if isinstance(z, dict)]
    за_ід = {str(z.get("ід") or ""): z for z in зн if z.get("ід")}
    вих = []
    for р in розриви:
        к = str((р or {}).get("знахідка") or "").strip() if isinstance(р, dict) else ""
        if к and not р.get("правило"):
            z = за_ід.get(_ПР.ід_з_дроту(к))
            правила = ({str(z.get("правило") or "")} if z else
                       {str(x.get("правило") or "") for x in зн
                        if any(isinstance(w, dict) and w.get("code") == к for w in (x.get("заяви") or []))})
            правила.discard("")
            if len(правила) == 1:
                р = dict(р, правило=правила.pop())
        вих.append(р)
    return вих


def заяви_ходу(хід, знахідки):
    """Оголошений хід → заяви знахідки, проти якої він стоїть (`{code, values}`): знахідки того самого
    `правило` серед `знахідки` суду, що судив склад картки. Хід без коду чи з кодом, якого в цьому
    суді нема, — `[]`: умови, проти якої річ стоїть, опис не дістане."""
    пр = str((хід or {}).get("правило") or "") if isinstance(хід, dict) else ""
    вих = []
    for z in (знахідки or []) if пр else []:
        if isinstance(z, dict) and str(z.get("правило") or "") == пр:
            вих += [w for w in (z.get("заяви") or []) if isinstance(w, dict) and w.get("code") and w not in вих]
    return вих


def застосувати_свідомі(знахідки, розриви, речі):
    """Оголошений хід ПОСЛАБЛЮЄ ЛИШЕ ЗНАХІДКУ, ЯКУ НАЗВАВ КОДОМ (×0.6, як K-KOH-03), не ховає
    її: сила лишається видимою, знахідка несе `свідомий`. Код — `правило` оголошення; річ, коли
    названа, звужує адресу до знахідок над нею. Оголошення без коду не послаблює нічого
    (`без_коду` у звіті): «свідомо» лишається інформацією для стилістки й жінки (п.17).

    ЧОМУ КОД, А НЕ РІЧ. Якби адресою була річ, хід над нею послаблював би БУДЬ-ЯКУ
    не-блокуючу знахідку над тією ж річчю: стилістка приймає на виборі регістровий гейт над
    усіма речами («register gates… accepted»), і цей хід послабив би K-KOH-10 «відкритих
    зон 1 при межі 0» над светром з відкритими плечима, хоча про відкриті плечі в ньому
    не було ні слова.

    Чого це не робить, і навмисно: не торкається БЛОКЕРІВ (розмір, вето людини, погода —
    вимірний провал не оголошується) і знахідки над межею, яку поставив паспорт —
    її власна межа чи норма події (`межа_паспорта`, п.9: явний вибір жінки сильніший за хід
    стилістки). `адресати` (id, назви, слоти названих речей) звіт лишає як доти: ними фокус
    K-CRA-02 і K-KOH-07 читають, які речі стилістка пояснила."""
    if not розриви: return знахідки, []
    норм = lambda s: _re_ід.sub(r"\s+", " ", str(s or "").lower()).strip()
    звіт = []
    for р in розриви:
        т = норм(р["текст"])
        адресати = set()
        # Адресат, названий полем, сильніший за збіг у тексті (Т-04): номер пакета не дорівнює
        # id каталогу, тож `_свідомі_з_json` уже перевів його в `ід`/`ід_речей`.
        ід_р = str(р.get("ід") or "")
        _ід_усі = {str(x) for x in (р.get("ід_речей") or ([ід_р] if ід_р else []))}
        if _ід_усі:
            for rr in речі:
                _і = str(rr.get("id") or "")
                if _і in _ід_усі:
                    адресати |= {_і, rr.get("назва"), rr.get("слот")}
        # Проза (руки 3–4) адресата полем не має — лише словами; кодом знахідки вона не адресує,
        # тож нічого не послаблює, але речі, які назвала, лишаються названими.
        for rr in (речі if not адресати else ()):
            norm_id = str(rr.get("id") or "")
            назва = норм(rr.get("назва"))
            if (norm_id and norm_id.lower() in т) or (len(назва) >= 8 and (назва[:24] in т or назва.split(" ")[0] in т.split(" "))):
                адресати |= {norm_id, rr.get("назва"), rr.get("слот")}
            elif rr.get("слот") and (" %s" % rr["слот"]) in (" " + т):
                адресати |= {norm_id, rr.get("назва"), rr.get("слот")}
        адресати.discard(None); адресати.discard("")
        р = dict(р, адресати=sorted(a for a in адресати if a), послаблено=0)
        if not адресати:
            р["без_адресата"] = True
        if not р.get("правило"):
            р["без_коду"] = True
        звіт.append(р)
    вих = []
    for z in знахідки:
        z = dict(z)
        речі_зн = {str(x) for x in (z.get("речі") or [])}
        if (not z.get("блокує") and z.get("сила") != "питання" and z.get("сила_нп")
                and not z.get("межа_паспорта")):
            for р in звіт:
                if р.get("без_коду") or str(р["правило"]) != str(z.get("правило") or ""):
                    continue
                # річ названа — знахідка мусить стояти над нею; не названа — досить коду
                _речі_р = {str(x) for x in (р.get("ід_речей") or ([р["ід"]] if р.get("ід") else []))}
                if _речі_р and not (_речі_р & речі_зн):
                    continue
                z["сила_нп"] = round(z["сила_нп"] * СВІДОМИЙ_МНОЖНИК, 3)
                z["свідомий"] = р["текст"]
                z["сила_нп_джерело"] = (z.get("сила_нп_джерело") or "") + "; свідомий розрив ×%.1f (K-KOH-03, T3)" % СВІДОМИЙ_МНОЖНИК
                р["послаблено"] += 1
                break
        вих.append(z)
    return вих, звіт


HEX_РЕГ = _re_ід.compile(r"#[0-9a-fA-F]{6}\b")
# огородження ```json на кінцях відповіді окремого виклику (Т-8)
_ОГОРОДЖЕННЯ_JSON = _re_ід.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")

# ── ЗАГОЛОВОК РОЗДІЛУ — НЕ НАЗВА РЕЧІ ──────────
# `brief.ФОРМАТ` просить відповідь трьома розділами, і другий зветься «Взуття й
# аксесуари». Модель пише його заголовок у тому самому рядку, що й першу річ, —
# і назвою речі ставало «Взуття й аксесуари: лофери» (видно на картці руки 3).
# Перелік іменований і короткий: тут лише ЗАГОЛОВКИ, яких просить сам ФОРМАТ, і
# їхні звичні написання. Рольова мітка речі («Сумка: плетена», «Базовий топ:
# сорочка лляна») сюди не входить свідомо — вона несе слово, з якого код виводить
# слот, і зняти її означало б загубити слот замість заголовка.
ЗАГОЛОВКИ_РОЗДІЛІВ = ("речі", "взуття й аксесуари", "взуття та аксесуари",
                      "аксесуари", "верхній шар")


def _без_заголовка(рядок):
    """«Взуття й аксесуари: лофери, чорні (hex 111111)» → («лофери, чорні (hex 111111)», «Взуття й аксесуари»).

    Повертає пару: рядок без заголовка і сам заголовок (або None). Заголовок не
    викидається, а віддається викликачеві: він єдиний носій слова, з якого код
    іноді виводить слот («човники» самі по собі слота не дають, «Взуття й
    аксесуари: човники» дають), і мовчки втратити його означало б обміняти
    охайну назву на загублену річ.

    Знімається лише заголовок із `ЗАГОЛОВКИ_РОЗДІЛІВ` і лише коли після
    двокрапки щось лишається: рядок «Взуття й аксесуари:» без речей — це сам
    заголовок, і робити з нього порожню назву означало б вигадати річ, якої
    модель не назвала.
    """
    г, є_двокрапка, хвіст = str(рядок or "").partition(":")
    if є_двокрапка and хвіст.strip() and г.strip().lower().rstrip(" .") in ЗАГОЛОВКИ_РОЗДІЛІВ:
        return хвіст.strip(), г.strip()
    return str(рядок or "").strip(), None


def _речі_рядка(рядок):
    """Один рядок відповіді моделі → одна річ або кілька, списком.

    ЩО ЦЕ МІНЯЄ. `ФОРМАТ` просить «по рядку на кожну», але розділ
    «2. Взуття й аксесуари» модель пише ОДНИМ рядком через «;»: «лофери, чорні
    (hex 111111), шкіра; сумка через плече, коньячна (hex 8b5a2b), шкіра». Коли рядок = річ,
    сумка з ВЛАСНИМ hex гине мовчки — на картці 3 речі замість 4, а проза
    під ними про сумку говорить.

    ПОДІЛ ТІЛЬКИ ТОДІ, КОЛИ ВІН ДОВЕДЕНИЙ: частин із власним hex має бути
    щонайменше дві. Один hex на рядок — старий шлях байт у байт, разом із
    «рядок без hex → `без_кольору`»: крапка з комою всередині опису однієї речі
    не має права розбивати її надвоє.
    Частина без свого hex між двома кольоровими — хвіст попередньої речі
    («…, шкіра»), і вона доклеюється до неї, а не стає річчю без кольору.
    """
    чистий, заг = _без_заголовка(рядок)
    частини = [ч.strip(" .") for ч in чистий.split(";")]
    частини = [ч for ч in частини if ч]
    if sum(1 for ч in частини if HEX_РЕГ.search(ч)) < 2:
        # БАЙТ У БАЙТ СТАРИЙ ШЛЯХ: рядок віддається таким, яким його читав
        # попередній розбір, разом із кінцевою крапкою — її бачить `без_кольору`.
        return [(чистий, заг)] if чистий else []
    вих = []
    for ч in частини:
        if HEX_РЕГ.search(ч) or not вих:
            вих.append([ч, заг])
        else:
            вих[-1][0] = вих[-1][0] + ", " + ч
    return [(т, з) for т, з in вих]


# ── ПЕРЕЛІК РЕЧЕЙ ДАЄ МОДЕЛЬ ОКРЕМИМ ВИКЛИКОМ (Т-8) ─────────────
# ЧОМУ: проза рук 3–4 мала 7 речей, а на картці лишалось 2. Розбір прози брав річчю лише рядок із hex, тож гинуло все
# без числа кольору («Взуття: білі кеди на плоскій підошві», «Аксесуари: шовкова
# хустка…») і друга річ на зайнятий слот («Тонкий кардиган» після «Блузки»: обом
# `feed.слот` дає «верх»).
# ЧОМУ НЕ ШАБЛОНИ Й НЕ ОБʼЄКТ JSON. Дописувати шаблони — ганятися за мовою
# словником; мову розуміє модель. А просити всю відповідь руки обʼєктом JSON
# коштує ПРОЗИ: вона коротшає на чверть. Тому проза руки
# лишається вільною, як на main, а перелік речей дає окремий короткий виклик над
# уже готовим текстом (`brief.ПРОМПТ_ПЕРЕЛІК_РЕЧЕЙ`), і код бере його як є.
# НЕ ВИЙШЛО — ЯК НА MAIN: виклик упав, відповідь не список, список порожній —
# працює розбір прози, байт у байт, і показ каже про це рядком у звіт власника.
def речі_переліку(перелік):
    """Відповідь окремого виклику → список рядків речей (або None).

    Читається як JSON: огородження ```json знімаються лише на КІНЦЯХ, усередину
    відповіді ця функція не заглядає й нічого в ній не шукає. Береться список
    рядків; `{"речі": [...]}` теж приймається — та сама структура, лише названа.
    None означає РІВНО «переліку нема», і далі йде розбір прози.
    """
    т = _ОГОРОДЖЕННЯ_JSON.sub("", str(перелік or "").strip())
    try:
        об = _json_ід.loads(т)
    except Exception:
        return None
    if isinstance(об, dict):
        об = об.get("речі")
    if not isinstance(об, list):
        return None
    речі = [str(р).strip() for р in об if str(р or "").strip()]
    return речі or None


def _кандидат(повна, заголовок):
    """Рядок речі → (назва, повна, hex|None, парам, заголовок).

    Назва — перший сегмент до коми (інакше «довжина в підлогу» з опису робила зі
    штанів вечірню сукню); решта сегментів розкладається тими самими словниками
    `verify`, що й доти. `hex` тут може бути None: перелік від моделі несе й речі,
    яким вона кольору числом не дала (розділ «Взуття й аксесуари» його й не
    просить), і губити їх через це — те саме, що губити їх через шаблон.
    """
    м = HEX_РЕГ.search(повна)
    сегменти = [с.strip(" .") for с in повна.split(",")]
    назва = сегменти[0]
    парам = {}
    for с in сегменти[1:]:
        if not с or HEX_РЕГ.search(с): continue
        if "тканина" not in парам and _V.тканина_зі_слова(с).get("за_чим"): парам["тканина"] = с
        elif "крій" not in парам and _V.крій_зі_слова(с).get("крій"): парам["крій"] = с
        elif "довжина" not in парам and any(w in с.lower() for w in ("довжин", "міді", "максі", "міні", "до колін", "до стегон", "в підлогу", "по щиколотку", "укорочен")):
            парам["довжина"] = с
    return (назва, повна, (м.group(0).lower() if м else None), парам, заголовок)


def _кандидати_з_прози(текст):
    """РОЗБІР ПРОЗИ — те, що стояло в тілі `речі_з_тексту`, побайтово, разом із
    вимогою hex на рядок. Працює, коли переліку нема."""
    рядки = [l.strip(" \t-\u2022\u00b7*") for l in str(текст or "").splitlines()]
    кандидати, без_кольору = [], []
    for l in рядки:
        if not _re_ід.match(r"^\s*\d+[.)]\s*\S", l) and not HEX_РЕГ.search(l): continue
        if l.upper().startswith(("ЧАСТИНА", "ОБРАЗ:", "СВІДОМО")): continue
        # ЗАГОЛОВОК РОЗДІЛУ ЗНЯТО, А РЯДОК МОЖЕ НЕСТИ КІЛЬКА РЕЧЕЙ 
        for повна, заголовок in _речі_рядка(_re_ід.sub(r"^\s*\d+[.)]\s*", "", l)):
            if not HEX_РЕГ.search(повна):
                без_кольору.append(повна[:80]); continue
            кандидати.append(_кандидат(повна, заголовок))
    return кандидати, без_кольору


def _кандидати_з_переліку(речі):
    """Рядки переліку → кандидати. Жодної звірки: що модель назвала, те й іде."""
    вих = []
    for р in речі:
        for повна, заголовок in _речі_рядка(_re_ід.sub(r"^\s*\d+[.)]\s*", "", str(р).strip(" \t-\u2022\u00b7*"))):
            if повна:
                вих.append(_кандидат(повна, заголовок))
    return вих


def _речі_структурою(структ):
    """Перелік кодами (`руки_без_коду.речі_переліку`) → той самий словник, що й розбір рядків.

    Id — «м-%03d» за місцем у переліку (той самий слід, що знімає чистка показу); річ без
    кольору йде з `колір_невідомий`, як доти; друга річ на слот лишається на картці й стоїть
    у `надлишок` (перелік переказує образ, який вона читає, а не збирає його — Т-8). Код
    слота поза таблицею — `без_слота` з назвою й кодом: річ не зникає мовчки (В-4)."""
    речі, без_слота, надлишок, зайняті, не_потрібні = [], [], [], set(), []
    for i, р in enumerate(структ, 1):
        if not р.get("носить", True):
            # слот, який опис називає непотрібним (`worn` false): на картку не йде, у звіті — названий
            не_потрібні.append(dict(слот=р["слот"], назва=р["назва"][:60]))
            continue
        if not р["слот"]:
            без_слота.append(dict(назва=р["назва"][:60], код=р["код_слота"]))
            continue
        if р["слот"] in зайняті:
            надлишок.append(dict(слот=р["слот"], назва=р["назва"][:60], лишено=True))
        зайняті.add(р["слот"])
        c = dict(id="м-%03d" % i, слот=р["слот"], назва=р["назва"], ціна=0, group_id=None,
                 набір=False, hex=р["hex"], джерело="модель")
        if not р["hex"]:
            c["колір_невідомий"] = True
        for к in ("деталі", "own"):
            if р.get(к):
                c[к] = р[к]
        речі.append(c)
    причина = None if речі else ("all_items_unneeded" if не_потрібні else "no_item_slot_code")
    return dict(речі=речі, без_кольору=[], без_слота=без_слота, надлишок=надлишок, не_потрібні=не_потрібні,
                перелік_моделі=dict(названо=len(структ), не_потрібних=len(не_потрібні),
                                    без_слота=[str(б["код"]) for б in без_слота],
                                    джерело="окремий виклик ITEM_LIST, слот кодом"),
                чому=причина)


def речі_з_тексту(текст, перелік=None):
    """Образ, який модель ВИГАДАЛА (руки 3 і 4 сліпої проби — каталогу вони не бачать),
    → речі коду тим самим шляхом, що й каталог. ФОРМАТ відповіді просить по рядку на
    річ «що це, крій, довжина, колір + hex, тканина»; кожен такий рядок стає
    псевдо-оффером тимчасового YML: назва = перший сегмент до коми (інакше «довжина в
    підлогу» з опису робила зі штанів вечірню сукню — спіймано на першому ж тесті),
    решта сегментів розкладаються в params тими самими словниками (тканина / крій /
    довжина), колір іде з hex через кеш кольорів по СПРАВЖНІХ id після читати_yml
    (кваліфікація @магазин не вгадується — спіймано там само: кеш мимо, і «коньячна»
    сумка випадала, бо слова у словнику нема). Впевненість 0.8: модель назвала точку,
    не слово. Слот, тип, крій, довжина, тканина далі витягуються функціями feed.прогін
    — щоб вердикт по руках без каталогу лягав у лог зі знахідками коду.
    Рядок без hex → `без_кольору`; без слота → `без_слота`; другий рядок на той самий
    слот → `надлишок` (образ — по одній речі на слот).

    `перелік` (Т-8) — відповідь ОКРЕМОГО короткого виклику, у якій модель
    сама назвала речі цієї ж прози. Коли він є, речі беруться З НЬОГО, і два обмеження
    розбору прози там не діють, бо жодне з них не про мову: hex на рядку не
    обовʼязковий (без нього річ їде без кольору, а не в нікуди), а друга річ на
    зайнятий слот лишається на картці, лише позначена в `надлишок` (`лишено`).
    Переліку нема — розбір прози, байт у байт як на main.

    КЕШ КОЛЬОРІВ БУДУЄТЬСЯ ТУТ, А НЕ ПРИЙМАЄТЬСЯ: параметр `кеш` стояв у сигнатурі й
    не вживався (ніхто його й не передавав) — кеш читається з тимчасового YML по
    СПРАВЖНІХ id уже після `читати_yml`, інакше квалификація @магазин не збігається."""
    import tempfile as _tf
    import xml.sax.saxutils as _sx
    import os as _os
    import json as _js
    # ПЕРЕЛІК КОДАМИ (П-1): слот — кодом внутрішньої мови, її річ — id у `own`.
    # Тоді код не вгадує слот словником (`feed.слот` не знав «козаків», В-3) і не
    # шукає мітку в назві (В-1). Не вийшло — список рядків або розбір прози.
    # Перелік назвав опис не образом (`is_outfit` no — відмова, питання) — речей нема, і проза
    # розбором їх не дає: інакше вигаданий моделлю приклад став би карткою під текстом відмови
    if перелік is not None and _РБК.опис_образ(перелік) is False:
        return dict(речі=[], без_кольору=[], без_слота=[], надлишок=[], чому="description_not_outfit")
    _структ = _РБК.речі_переліку(перелік)
    if _структ:
        return _речі_структурою(_структ)
    _перелік = речі_переліку(перелік)
    кандидати = _кандидати_з_переліку(_перелік) if _перелік else []
    з_переліку = bool(кандидати)
    звіт_переліку = dict(названо=len(_перелік), джерело="окремий виклик «випиши речі»") if з_переліку else None
    без_кольору = []
    if not з_переліку:
        кандидати, без_кольору = _кандидати_з_прози(текст)
    if not кандидати:
        return dict(речі=[], без_кольору=без_кольору, без_слота=[], надлишок=[],
                    чому="no_hex_line")
    # ── ЗАГОЛОВОК РОЗДІЛУ — У КАТЕГОРІЮ, А НЕ В НАЗВУ ──
    # Знявши «Взуття й аксесуари:» з назви, ми забрали й ЄДИНЕ слово, з якого код
    # виводив слот у речей, чия власна назва слота не дає: «човники» самі по собі
    # дають None, «Взуття й аксесуари: човники» дають «взуття» (виміряно
    # `feed.слот`). Класти заголовок назад у назву означало б лишити на картці
    # рядок розділу; класти його КАТЕГОРІЄЮ КОЖНІЙ речі розділу — збрехати про
    # сумку («сумка плетена» в категорії «Взуття й аксесуари» стає взуттям,
    # виміряно там само). Тому категорія ставиться РІВНО тим речам, чия чиста
    # назва слота не дала: назва лишається охайною, а слот не губиться.
    офери_xml, категорії = [], {}
    for i, (назва, повна, hex_, парам, заголовок) in enumerate(кандидати, 1):
        п = "".join('<param name="%s">%s</param>' % (_sx.escape(k), _sx.escape(v)) for k, v in парам.items())
        кат = 1
        if заголовок and not _Ф.слот({"id": "м-%03d" % i, "назва": назва, "категорія": ""}):
            кат = категорії.setdefault(заголовок, len(категорії) + 2)
        офери_xml.append('<offer id="м-%03d" available="true"><name>%s</name><price>0</price>'
                         '<currencyId>UAH</currencyId><categoryId>%d</categoryId>%s</offer>'
                         % (i, _sx.escape(назва), кат, п))
    категорії_xml = '<category id="1">образ вигаданий моделлю</category>' + "".join(
        '<category id="%d">%s</category>' % (н, _sx.escape(з)) for з, н in sorted(категорії.items(), key=lambda t: t[1]))
    yml = ('<?xml version="1.0" encoding="UTF-8"?><yml_catalog><shop><name>модель</name><categories>'
           '%s</categories><offers>%s</offers></shop></yml_catalog>'
           % (категорії_xml, "".join(офери_xml)))
    fd, шлях = _tf.mkstemp(suffix=".xml"); _os.close(fd)
    fd2, кеш_ш = _tf.mkstemp(suffix=".json"); _os.close(fd2)
    try:
        open(шлях, "w", encoding="utf-8").write(yml)
        # справжні id (з кваліфікацією магазину, якщо феєд її дасть) — ключі кешу кольору
        оф = _Ф.читати_yml(шлях)[0]
        кеш_д, hex_за_ід = {}, {}
        for o, (назва, повна, hex_, парам, заголовок) in zip(оф, кандидати):
            # РІЧ БЕЗ ЧИСЛА КОЛЬОРУ — НЕ РІЧ БЕЗ РЕЧІ (Т-8): запису в кеші просто нема,
            # і колір цієї речі далі рахується зі слова назви, як у будь-якого оффера.
            if not hex_:
                continue
            кеш_д[o["id"]] = dict(lab=list(_cs.hx(hex_)), впевненість=0.8, розкид=None)
            hex_за_ід[o["id"]] = hex_
        _js.dump(кеш_д, open(кеш_ш, "w", encoding="utf-8"))
        # файл одноразовий — базу справжнього фіду з кеша не витісняє (Ш-1, `фід_каталог`)
        пр = _Ф.прогін(шлях, [[]], ліміт_фото=0, кеш=кеш_ш, кеш_бази=False)
    finally:
        for f in (шлях, кеш_ш):
            try: _os.remove(f)
            except OSError: pass
    речі, зайняті, надлишок = [], set(), []
    у_каталозі = set()
    for c in пр["каталог"]:
        у_каталозі.add(c["id"])
        if c["слот"] in зайняті:
            # ДРУГА РІЧ НА СЛОТ: у розборі прози вона й далі випадає (образ — по одній
            # речі на слот), а в переліку від моделі ЛИШАЄТЬСЯ. Причина в тому, що
            # перелік не збирає образ, а переказує те, що модель уже написала жінці:
            # «Тонкий кардиган» після «Блузки» — обом `feed.слот` дає «верх», і мовчки
            # зняти кардиган означало б показати їй не той образ, який вона читає.
            надлишок.append(dict(слот=c["слот"], назва=c["назва"][:60], лишено=з_переліку))
            if not з_переліку:
                continue
        зайняті.add(c["слот"])
        c = dict(c); c["hex"] = hex_за_ід.get(c["id"]); c["джерело"] = "модель"
        речі.append(c)
    без_слота = [dict(назва=(назва or повна)[:60]) for (назва, повна, hex_, парам, заголовок), o in zip(кандидати, оф)
                 if o["id"] not in у_каталозі]
    # ── РІЧ, ЯКІЙ МОДЕЛЬ НЕ ДАЛА ЖОДНОГО КОЛЬОРУ (Т-8) ────────────────────────
    # `фід_каталог` кладе в каталог лише річ, у якої є lab: каталог крамниць — пул за
    # кольором, і без кольору річ там не потрібна нікому. Але «шовкова хустка для
    # волосся» й «маленька сумка через плече» — це речі, які модель НАПИСАЛА жінці, і
    # слот у них є (`feed.слот`: шарф, сумка). Мовчки не показати їх на картці
    # означало б показати не той образ, який вона щойно прочитала. Тому на шляху
    # переліку вони йдуть на картку з тим, що відомо, — назвою і слотом, без
    # вигаданого кольору; у пул каталогу вони не потрапляють.
    if з_переліку:
        _відомі = {c["id"] for c in речі}
        for (назва, повна, hex_, парам, заголовок), o in zip(кандидати, оф):
            if o["id"] in _відомі:
                continue
            _сл = _Ф.слот(o)
            if not _сл:
                continue
            речі.append(dict(id=o["id"], слот=_сл, назва=назва or повна, ціна=0,
                             group_id=o.get("group_id"), набір=False,
                             hex=None, джерело="модель", колір_невідомий=True))
        без_слота = [b for b in без_слота
                     if not any(b["назва"] == (c.get("назва") or "")[:60] for c in речі)]
        # ПОРЯДОК — ЯК У ПРОЗІ: жінка читає перелік під тим самим текстом, і картка,
        # переставлена по слотах, читалась би як інший образ.
        речі.sort(key=lambda c: int(str(c["id"]).split("-")[-1] or 0))
    return dict(речі=речі, без_кольору=без_кольору, без_слота=без_слота, надлишок=надлишок,
                перелік_моделі=звіт_переліку,
                чому=None if речі else "no_item_with_slot_and_colour")


def перевірити_образ_моделі(текст, тіло, перелік=None):
    """Рука без каталогу (3/4): текст моделі → речі. СУДУ НАД НИМИ НЕМА.

    РІШЕННЯ ВЛАСНИКА, дослівно: «навіщо робити суд рукам 3-4? Суд
    тільки для системи код + ші, руки 1-2. Там де коду немає суду не повинно
    бути.» Тож тут нема повного суду над ВИГАДАНИМИ речами (`композитор_оцінка.оцінити`
    — знахідки й блокери, `graph.граф` + `вузол_напруги`, послаблення оголошених
    розривів): мотив «інакше вердикти цих рук лягали б у лог без знахідок коду»
    власник скасував: руки
    3 і 4 на те й є контролем, що коду в них нема, тож їхні вердикти МУСЯТЬ
    лягати без знахідок коду. Судити вигадані речі означало міряти те, чого
    продукт не робить, і мішати контроль із продуктом у тому самому журналі.

    ЩО ЦЕ МІНЯЄ В РІШЕННІ (виміряно стендом рв6, 12 сідів).
      before — руки 3/4 несли знахідки, блокери, вузол напруги й 6 питань «код
               не знає» на картку та в колонку `питання_коду`; серед них рядки
               з вигаданим id (««м-001» на «груди»: нижче мінімуму носіння»),
               бо суд називає річ так, як її назвав розбір тексту.
      after  — `знахідки`, `блокує`, `граф`, `вузол` порожні за побудовою;
               `в.питання` в `міст_відповіді` виходить порожнім, тож блок «код
               не знає» на картках рук 3/4 не з'являється зовсім, а колонка
               звіту в них порожня. Руки 1 і 2 не змінюються нічим.

    ЩО ЛИШАЄТЬСЯ, І ЧОМУ ЦЕ НЕ СУД. `речі` — РОЗБІР тексту, а не вирок: без нього
    на картці руки 3/4 не було б жодної речі (`показ` читає назву, слот і колір
    саме звідси). `мова` — ярус R-LNG-UA над текстом моделі: це гейт про мову
    для жінки, не про образ, і цикл перепису рук 3/4 тримається на ньому.
    `свідомі` — оголошені ходи САМОЇ моделі, її ж слова; послаблювати ними нема
    чого, бо знахідок нема, тож вони їдуть як прочитані.
    `перевірено=True` тут і доти значило «розбір удався, є що показати» (показ
    читає його рівно так: `в.перевірено !== false && в.речі.length`), а не «код
    перевірив образ», — тому лишається як є.

    `F` (колірні ознаки людини) і `сценарій` пішли з підпису разом із судом: їх
    читав ТІЛЬКИ `_оцінити`. Лишати їх означало б обіцяти, що функція дивиться
    на людину й на випадок, — а вона тепер лише розбирає текст."""
    р = речі_з_тексту(текст, перелік=перелік)
    вих = dict(перевірено=False, розбір=р, знахідки=[], граф=None, вузол=None, блокує=[], рядок_вузла=None, мова=None)
    if перелік is not None:
        # код переліку «опис — образ» (True / False / None — не названо) — картку руки 3–4 показ
        # ставить лише на True; слів опису код не читає (п.12)
        вих["опис_образ"] = _РБК.опис_образ(перелік)
    # (п.12) причина — код, не фраза з числом; які речі й скільки
    # їх розібрано (із кольором і слотом), видно з `розбір["речі"]` вище
    if len(р["речі"]) < 2:
        вих["чому"] = "замало_речей"; return вих
    готові = [_КПР.у_річ(dict(c), c["слот"], тіло) for c in р["речі"]]
    # `own` і `деталі` (П-1) — з переліку кодами: `own` читає `річ_з_фото.впізнати_в_тексті`,
    # `деталі` — картка й приміряння (крій, довжина, тканина словами опису)
    вих.update(перевірено=True, речі=[dict(id=r["id"], слот=r["слот"], назва=r["назва"], hex=r.get("hex"),
                                          **{к: r[к] for к in ("own", "деталі") if r.get(к)}) for r in готові],
               свідомі=свідомі_розриви(текст))
    # П.14 (СТАНДАРТ §4): `мова = None` показ читає як «гейта не було»
    # (`показ.html` розрізняє `''`, «гейт впав» і вирок), тож ковтати сюди
    # поломку мовного гейта означало б мовчки зняти Т-07 з усього прогону —
    # і рівно на тій руці, де він потрібен найбільше.
    # режим названий явно з тієї самої причини, що в `перевірити_від_моделі`
    # (Т-07 крок 1); руки 3/4 реагують лише на ярус української — межа
    # записана в `language_gate` біля `ЯРУС_УКРАЇНСЬКОЇ` і в показі.
    вих["мова"] = (_LG.перевірити(текст, режим="блокувати")
                   if hasattr(_LG, "перевірити") else None)
    return вих



# ═══════════════════════ обмін, відсічення, паспорт ═══════════════════════

# `_json_у_рядки` СТОЯЛА ТУТ І ЗНЕСЕНА (Т-04). Вона перекладала обʼєкт моделі НАЗАД
# у рядки ПІДПИС/ОБРАЗ/СВІДОМО/ЧОМУ/ПОТРІБНО, щоб його розібрали регулярки прози.
# Ціна перекладу: `свідомо` ставало `str(dict)` і втрачало адресата (V33), `потрібно`
# їхало в пошук разом з іменами полів, а поле, назване інакше, зникало без слова.
# Тепер обʼєкт читають полями (`образи_з_json`, `запити_речей_з_тексту`), а розбір
# прози лишається окремим шляхом для рук без каталогу. Одна точка РОЗБОРУ тексту —
# `протокол.розбір_за_схемою` (суворий `розбір` плюс однозначний намір
# слабкої моделі — ключ із латиницею, масив без обгортки, обрив об стелю виводу).


def запити_речей_з_тексту(текст):
    """Прохання моделі про річ ПОЗА пулом → `[{опис, слот}]`: поле `потрібно` ОБРАЗИ_V1
    (`[{слот, опис}]` або рядок), а в прозовій відповіді — рядки «ПОТРІБНО: …» (там
    `слот` — None). Це право ші, про яке домовлялися: код шукає по всьому каталогу
    (`bridge.від_моделі` → `шукати_словами`).

    Поле читається ПРЯМО (Т-04): доти обʼєкт ішов крізь `_json_у_рядки`, де
    `{"слот": "шарф", "опис": "червоний шарф"}` ставав рядком `str(dict)` — і в
    пошук їхав разом із дужками й іменами полів.

    СЛОТ — ПОЛЕ СТРУКТУРИ, А НЕ СЛОВО ОПИСУ (Т-7). Якби звідси їхав лише опис, то на {"слот": "сумка", "опис": "Для прогулянки з собаками
    сумка є обовʼязковою…»} пошук словами давав би джемпер-поло й піджак: «прогулянка»
    і «зручність» стоять у назвах одягу частіше, ніж «сумка»."""
    об = _ПР.розбір_за_схемою(текст, "ОБРАЗИ_V1")[0]
    if isinstance(об, dict) and (це_образи(об) or "потрібно" in об):
        вих = []
        for п in (об.get("потрібно") or []):
            опис, слот = ((п.get("опис") or п.get("слот")), п.get("слот")) if isinstance(п, dict) else (п, None)
            if str(опис or "").strip():
                з = dict(опис=str(опис).strip(), слот=(str(слот).strip() or None) if слот else None)
                # ФРАЗА ПОШУКУ — З КОДІВ (П-2): промпт англійський, і речення «опис» теж англійське;
                # тип, колір і тканину модель дає кодами, а розбір дроту вже переклав їх у ключі
                # ядра (`протокол.з_дроту_en`) — українські слова каталогу, якими й шукає
                # `шукати_словами`. Код поза таблицею (латиниця) у фразу не йде.
                ключі = {к: str(п.get(к)).strip() for к in ("тип", "колір", "тканина")
                         if isinstance(п, dict) and _re_ід.search(r"[а-яіїєґ]", str(п.get(к) or ""), _re_ід.I)}
                if ключі:
                    з["фраза"] = " ".join(ключі.values())
                з["коди"] = _коди_запиту(ключі, з["слот"])
                вих.append(з)
        return вих[:5]
    return [dict(опис=м.group(1).strip(), слот=None, коди=_коди_запиту({}, None)) for м in
            re.finditer(r"^\s*ПОТРІБНО\s*[:：]\s*(.+)$", str(текст or ""), re.M)][:5]


def _коди_запиту(ключі, слот):
    """Що модель назвала в «needed» — кодами (п.12): знайдена річ несе їх стилістці
    як `found_for`, так само як `for_her_wish` (`внутрішня_мова.бажання_кодом`). Фраза пошуку —
    ключі ядра українськими словами («светр хакі вʼязане») — в англійський промпт не йде;
    вона лишається пошуку й звіту. Тип, колір, тканина; без типу — слот; без жодного коду
    (проза «ПОТРІБНО: …») — "unknown"."""
    return _ВМ.бажання_кодом(dict(ключі, слот=слот)) or _ВМ.UNKNOWN
