#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Відтворюваний витяг дій для оцінки іншою моделлю (вибірка наряду ПК-дотримання-правил-прилад-усі).

Бере сторінки історій `list_events` (`<тека>/NNNN.json`), дії `tool_use` доби, сортує за sha256(`tool_use.id`) у
зростанні (рівні — за сесією) і друкує перші N: час, роль, сесія, інструмент, вхід (до 1500 знаків), результат
(до 800), текст ходу перед дією (до 600) та останнє слово зі стисненням (до 400) — досить, щоб судити про дію за
правилом рядка переліку. Запуск: python3 -I аудит/проби/пк_вибірка_витяг.py --від 2026-10-29T09:00 --до 2026-10-30T09:00
виконавець=/tmp/ccr/виконавець/<id> … > витяг.md; той самий вхід дає той самий вивід.
"""
import argparse
import glob
import hashlib
import json
import os
import sys


def події(тека):
    бачені, дані = set(), []
    for файл in sorted(glob.glob(os.path.join(тека, "*.json"))):
        for е in json.load(open(файл, encoding="utf-8"))["data"]:
            ключ = next((v.get("uuid") for k, v in е.items() if k != "created_at" and isinstance(v, dict)), None)
            if ключ in бачені:
                continue
            бачені.add(ключ)
            дані.append(е)
    дані.sort(key=lambda е: е["created_at"])
    return дані


def блоки(е):
    for к, в in е.items():
        if к != "created_at" and isinstance(в, dict):
            м = (в.get("internal_anthropic_catchall") or {}).get("message") or в.get("message")
            зміст = м.get("content") if isinstance(м, dict) else None
            return к, [б for б in зміст if isinstance(б, dict)] if isinstance(зміст, list) else []
    return None, []


def текст(зміст):
    if isinstance(зміст, str):
        return зміст
    return " ".join(б.get("text", "") for б in зміст if isinstance(б, dict) and б.get("type") == "text") \
        if isinstance(зміст, list) else ""


def обрізати(с, н):
    с = " ".join(str(с).split())
    return с if len(с) <= н else с[:н] + f"… [+{len(с) - н} знаків]"


def зібрати(теки, від, до):
    дії = []
    for роль, тека in теки:
        сесія = os.path.basename(тека.rstrip("/"))
        ходи, результати, попередній = [], {}, ""
        for е in події(тека):
            вид, бл = блоки(е)
            for б in бл:
                if б.get("type") == "tool_result":
                    результати[б.get("tool_use_id")] = текст(б.get("content"))
        попередній = ""
        for е in події(тека):
            вид, бл = блоки(е)
            if вид == "assistant":
                слова = " ".join(б.get("text", "") for б in бл if б.get("type") == "text").strip()
                if слова:
                    попередній = слова
                for б in бл:
                    if б.get("type") == "tool_use" and від <= е["created_at"][:16] <= до:
                        дії.append((hashlib.sha256(б["id"].encode()).hexdigest(), сесія, роль, е["created_at"], б,
                                    результати.get(б["id"], "(результату в історії нема)"), попередній))
    дії.sort(key=lambda д: (д[0], д[1]))
    return дії


def головна(арг=None):
    п = argparse.ArgumentParser()
    п.add_argument("--від", required=True)
    п.add_argument("--до", required=True)
    п.add_argument("-n", type=int, default=30)
    п.add_argument("сесії", nargs="+", help="роль=тека")
    а = п.parse_args(арг)
    теки = [tuple(с.split("=", 1)) for с in а.сесії]
    дії = зібрати(теки, а.від, а.до)
    print(f"# Витяг дій для оцінки: перші {а.n} з {len(дії)} за sha256(tool_use.id)\n")
    for н, (хеш, сесія, роль, час, б, результат, контекст) in enumerate(дії[:а.n], 1):
        print(f"## {н}. {час[:19]} · {роль} · …{сесія[-8:]} · {б.get('name')} · `{б['id']}`")
        print(f"- вхід: `{обрізати(json.dumps(б.get('input'), ensure_ascii=False), 1500)}`")
        print(f"- результат: `{обрізати(результат, 800)}`")
        print(f"- слова ходу перед дією: {обрізати(контекст, 600) or '(нема)'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(головна())
