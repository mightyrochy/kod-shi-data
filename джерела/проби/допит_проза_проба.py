"""ОЦІНКА-1000 (в): допит під карткою — що вирішує код, коли жива Sonnet відповіла прозою замість {"answer": …}.
Рядки — справжні відповіді Sonnet 02.10 (сід 3, питання «А якщо з чорними ботильйонами?»). Друкує факт."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import оцінка_образу as О

ПРОЗА = ("I can't confirm that swap, because the check hasn't run on the black ankle boots. They're outside "
         "your palette, and they don't obviously solve the weak spot.")
for назва, текст in (("проза без дужок", ПРОЗА), ("JSON за схемою", '{"answer": "%s"}' % ПРОЗА),
                     ("обірваний JSON", '{"answer": "I can\'t confirm'), ("проза в огорожі", "```\n" + ПРОЗА + "\n```"),
                     ("порожня", "  ")):
    в = О.прийняти_допит(текст)
    print("%-16s → відповідь %s · проза %s · причина %s" % (назва, "є (%d симв.)" % len(в["відповідь"]) if в["відповідь"] else "нема", в.get("проза"), в["причина"]))
