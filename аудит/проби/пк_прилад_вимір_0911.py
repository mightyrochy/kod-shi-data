#!/usr/bin/env python3
"""Проба приладу кореня ПК-дотримання-правил (вади з «Вимір диспетчера 09.11» паспорта): К27 не лічить архів субагента
(`parent_tool_use_id`), К9 — `rerun_workflow_run`, К3 — лист попередникові менеджера (`--менеджер a,b`).
Запуск: python3 -I аудит/проби/пк_прилад_вимір_0911.py. ДО: К27 2, К9 2, К3-порушень 1; ПІСЛЯ: 1, 1, 0."""
import importlib.util
import os
import sys

шлях = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела", "прилади", "корінь_пк_дотримання.py")
сп = importlib.util.spec_from_file_location("прилад", шлях)
м = importlib.util.module_from_spec(сп)
сп.loader.exec_module(м)
А = "mcp__claude-code-remote__"


def подія(тіло, час, батько=None):
    д = {"uuid": час, "internal_anthropic_catchall": {"message": {"content": тіло}}}
    if батько:
        д["parent_tool_use_id"] = батько
    return {"created_at": час, "assistant": д}


def виклик(ід, ім, вх):
    return [{"type": "tool_use", "id": ід, "name": ім, "input": вх}]


список = [
    подія(виклик("a", А + "archive_session", {"session_id": "s1"}), "2026-11-09T01:00:00Z", "p1"),
    подія(виклик("b", А + "archive_session", {"session_id": "s2"}), "2026-11-09T01:01:00Z"),
    подія(виклик("c", "mcp__github__actions_run_trigger", {"method": "rerun_workflow_run"}), "2026-11-09T01:02:00Z"),
    подія(виклик("d", "mcp__github__actions_run_trigger", {"method": "run_workflow"}), "2026-11-09T01:03:00Z"),
    подія(виклик("e", А + "send_message", {"session_id": "mgr_old", "message": "x"}), "2026-11-09T01:04:00Z"),
    {"created_at": "2026-11-09T01:05:00Z", "result": {"internal_anthropic_catchall": {
        "result": "—", "num_turns": 1, "origin": {"kind": "human"}}}},
]
дії, _ = м.аналіз("диспетчер", список, "d1", "mgr_new,mgr_old", "", "")
число = {к: sum(1 for д in дії if д.правило == к and д.порушення) for к in ("К27", "К9", "К3")}
чекано = {"К27": 1, "К9": 1, "К3": 0}
print(f"К27 {число['К27']}, К9 {число['К9']}, К3-порушень {число['К3']} (чекано {чекано})")
sys.exit(0 if число == чекано else 1)
