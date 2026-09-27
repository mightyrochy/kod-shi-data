# -*- coding: utf-8 -*-
"""К-4: скільки входу прогону читається з кешу і скільки він коштує — за записами стенда
(`рв6_стенд.js`, VIDPOVIDI=<тека>). Кеш ловить спільний ПОЧАТОК промптів одного типу; влучає
він лише з другого виклику типу, бо перший той кеш пише. Пороги провайдерів різні, тож вони —
змінною: POROH (типово 1024 — Anthropic Sonnet 5; Opus 5 — 512; Gemini 2.5 — 2048, 3.x — 4096),
ZAPYS — ціна запису (1.25 Anthropic, 1.0 неявний кеш Gemini), читання скрізь 0.10.
Ціна — в одиницях базової ціни входу, тобто «скільки токенів ми оплатимо».
Запуск: GEMMA_TOKENIZER=… POROH=1024 python3 проби/кеш_ціна.py <тека сіда> [<тека> …]"""
import os, re, sys, collections
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else len(s)
ПОРІГ, ЗАПИС, ЧИТАННЯ = int(os.environ.get("POROH") or 1024), float(os.environ.get("ZAPYS") or 1.25), 0.10

def промпти(тека):
    """{тип виклику: [промпт, …]} однієї теки стенда: заголовок і відповідь відрізані."""
    г = collections.defaultdict(list)
    for ім in sorted(os.listdir(тека)):
        т = open(os.path.join(тека, ім), encoding="utf-8").read()
        г[re.sub(r"^seed\d+_\d+_", "", ім)[:-4]].append(т.split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0])
    return г

теки = [промпти(а) for а in sys.argv[1:]]
преф = {т: ток(os.path.commonprefix([п for г in теки for п in г.get(т, [])]))
        for т in {т for г in теки for т in г}}
print("поріг %d · запис ×%.2f · читання ×%.2f%s"
      % (ПОРІГ, ЗАПИС, ЧИТАННЯ, "" if Т else " · ТОКЕНІЗАТОРА НЕМА: числа в символах"))
print("%-26s %5s %9s %9s %9s %6s %9s %7s" % ("тека", "викл", "вхід", "пишеться", "з кешу", "кеш %", "ціна", "Δ ціни"))
for шлях, г in zip(sys.argv[1:], теки):
    вхід = sum(ток(п) for пс in г.values() for п in пс)
    пише = sum(преф[т] for т, пс in г.items() if преф[т] >= ПОРІГ)
    чита = sum(преф[т] * (len(пс) - 1) for т, пс in г.items() if преф[т] >= ПОРІГ)
    ціна = (вхід - пише - чита) + пише * ЗАПИС + чита * ЧИТАННЯ
    print("%-26s %5d %9d %9d %9d %5.1f%% %9.0f %+6.1f%%"
          % (os.path.basename(шлях.rstrip("/"))[:26], sum(len(п) for п in г.values()), вхід, пише, чита,
             100.0 * чита / вхід, ціна, 100.0 * (ціна - вхід) / вхід))
