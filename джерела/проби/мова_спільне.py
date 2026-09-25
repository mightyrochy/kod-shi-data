# -*- coding: utf-8 -*-
"""Спільне для проб мовного шару — не проба (як `поділ_спільне`): збережені тексти і виклик
локальної моделі шару. Модель — будь-який сервер форми OpenAI (LM Studio на ноутбуці,
llama.cpp `llama-server`), міст до справжньої моделі не використовується.

Змінні оточення (латиницею: оболонка кириличних імен не має):
  MODEL      — ід моделі шару (`mamaylm-gemma-3-12b-it-v2.0`, Lapa…); без неї модель не кличеться;
  MODEL_URL  — адреса сервера, типово http://127.0.0.1:1234/v1;
  MODEL_TEMP — температура; без неї — та, що стоїть на сервері.
"""
import json
import os
import re
import sys
import time
import urllib.request

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ТУТ))
import мовний_шар as М            # noqa: E402
import паспорт_нагоди as ПН        # noqa: E402

ЗБЕРЕЖЕНІ = os.path.join(ТУТ, "мова_збережені.json")
МОДЕЛЬ = os.environ.get("MODEL") or None
АДРЕСА = (os.environ.get("MODEL_URL") or "http://127.0.0.1:1234/v1").rstrip("/")


def групи(шлях=None):
    """[{де, шлях, тексти}] — з фікстури `мова_збережені.json` (або іншого JSON тієї ж
    форми) чи з теки викликів стенда (`VIDPOVIDI=<тека>`: кожен файл — одна група)."""
    if шлях and os.path.isdir(шлях):
        return [г for ф in sorted(os.listdir(шлях)) if ф.endswith(".txt")
                for г in [з_виклику(os.path.join(шлях, ф))] if г and г["тексти"]]
    with open(шлях or ЗБЕРЕЖЕНІ, encoding="utf-8") as ф:
        return json.load(ф)


def з_виклику(файл):
    """Тексти для жінки з одного збереженого виклику стенда: опис і «як носити» (ОПИС_V1),
    слова стилістки з паспорта (виклик 0), проза рук 3–4. Решта викликів — None."""
    with open(файл, encoding="utf-8") as ф:
        сире = ф.read().split("\n\n── ВІДПОВІДЬ", 1)
    if len(сире) < 2:
        return None
    відп, ім = сире[1].split("\n", 1)[-1].strip(), os.path.basename(файл)
    об = М._ПР.розібрати_json(відп)
    if "ОПИС" in ім and isinstance(об, dict):
        return dict(де=ім, шлях="опис", тексти=[str(об.get("текст") or "")]
                    + [str(x) for x in (об.get("як_носити") or []) if isinstance(об.get("як_носити"), list)])
    if "паспорт" in ім and isinstance(об, dict):
        return dict(де=ім, шлях="чат", тексти=[str(об.get(к) or "") for к in ("відповідь_людині", "порада_людині")]
                    + [str(x) for x in (об.get("питання_людині") or []) if isinstance(об.get("питання_людині"), list)])
    if "рука" in ім and "проза" in ім:
        return dict(де=ім, шлях="проза", тексти=[re.sub(r"\(?\s*(?:hex\s*)?#[0-9a-fA-F]{6}\s*\)?", "", р).strip()
                                                  for р in відп.split("\n") if р.strip()])
    return None


def як_бачить_жінка(група):
    """Тексти групи такими, якими жінка бачить їх БЕЗ шару: слова чату й опис — після
    `паспорт_нагоди.жінці()` (так робить продукт на розборі), решта — як є."""
    return [ПН.жінці(т) if група.get("шлях") in ("чат", "опис") else т
            for т in група["тексти"] if str(т or "").strip()]


def модель(промпт):
    """(текст відповіді моделі шару, секунд) або (None, 0) без MODEL."""
    if not МОДЕЛЬ:
        return None, 0.0
    тіло = dict(model=МОДЕЛЬ, messages=[dict(role="user", content=промпт)], max_tokens=4000, stream=False)
    if os.environ.get("MODEL_TEMP"):
        тіло["temperature"] = float(os.environ["MODEL_TEMP"])
    запит = urllib.request.Request(АДРЕСА + "/chat/completions", data=json.dumps(тіло).encode("utf-8"),
                                   headers={"Content-Type": "application/json"})
    т0 = time.time()
    with urllib.request.urlopen(запит, timeout=3600) as в:
        дані = json.loads(в.read().decode("utf-8"))
    return ((дані.get("choices") or [{}])[0].get("message") or {}).get("content") or "", time.time() - т0


def прогнати(група):
    """Одна група — один виклик шару, як картка чи репліка в показі: (розмітка, результат
    `мовний_шар.прийняти` або None без моделі, секунд виклику)."""
    тексти = {str(і): т for і, т in enumerate(як_бачить_жінка(група))}
    р = М.розмітити(тексти)
    відп, с = модель(М.промпт(р)) if р else (None, 0.0)
    return р, (М.прийняти(р, відп) if відп is not None else None), с
