"""Проба: хук слів власника ставить час enqueue (надсилання), а не доставки; шапка не переказує правила ядра."""
import importlib.util, io, json, os, subprocess, sys, tempfile
шлях = ".claude/хуки/слова_власника.py"
рядки = [
    {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-29T05:15:08.000Z", "content": "перше"},
    {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-29T05:21:00.000Z", "content": "друге"},
    {"type": "user", "uuid": "a", "timestamp": "2026-10-29T05:17:56.000Z", "origin": {"kind": "human"}, "message": {"content": "перше"}},
    {"type": "attachment", "timestamp": "2026-10-29T05:25:09.000Z", "attachment": {"type": "queued_command", "origin": {"kind": "human"}, "prompt": "друге", "source_uuid": "b"}},
    {"type": "user", "uuid": "c", "timestamp": "2026-10-29T05:30:00.000Z", "origin": {"kind": "human"}, "message": {"content": "без enqueue"}},
    {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-29T05:31:00.000Z", "content": "<cross-session-message x>"},
    {"type": "user", "uuid": "d", "timestamp": "2026-10-29T05:32:00.000Z", "origin": {"kind": "human"}, "message": {"content": "<cross-session-message x>"}},
]
with tempfile.TemporaryDirectory() as д:
    т = os.path.join(д, "t.jsonl")
    open(т, "w", encoding="utf-8").write("\n".join(json.dumps(р, ensure_ascii=False) for р in рядки))
    вивід = subprocess.run([sys.executable, "-X", "utf8", шлях], input=json.dumps({"source": "compact", "transcript_path": т}),
                           capture_output=True, text=True, encoding="utf-8").stdout
print(вивід)
доставка = sum(х in вивід for х in ("05:17 UTC", "05:25 UTC"))
переказ = "інша роль шле" in вивід
print(f"слів із часом доставки: {доставка}; переказів правила в шапці: {int(переказ)}")
