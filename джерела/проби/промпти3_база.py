# -*- coding: utf-8 -*-
"""Сім'я промпти3 (рядки 6206–6213): скрипт проби на коді ДО (дерево `ref`, типово origin/main) і на цьому дереві —
ті самі входи, два промпти; скрипт із `--json` друкує останнім рядком JSON того, що міряє. `записи` — записи стенда
гілки живих прогонів (`аудит/живі_*/<сцена>/VIDPOVIDI`): промпт і відповідь окремо."""
import json, os, re, subprocess, sys, tempfile

ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_git = lambda *а: subprocess.run(["git", "-C", ДЖЕРЕЛА, "-c", "core.quotepath=off", *а], capture_output=True,
                                 text=True, check=True).stdout


def база(ref="origin/main"):
    """Тека `джерела` дерева `ref` (git worktree у тимчасовій теці, одна на коміт)."""
    sha = _git("rev-parse", ref).strip()
    тека = os.path.join(tempfile.gettempdir(), "промпти3_" + sha[:12])
    if not os.path.isdir(тека):
        _git("worktree", "add", "--detach", "-f", тека, sha)
    return os.path.join(тека, "джерела")


def до_після(скрипт, ref=os.environ.get("БАЗА", "origin/main")):
    """(ДО, ПІСЛЯ): JSON останнього рядка `скрипт --json` у `джерела` дерева `ref` і цього дерева."""
    def _прогін(тека):
        р = subprocess.run([sys.executable, os.path.abspath(скрипт), "--json"], cwd=тека, capture_output=True,
                           text=True, env=dict(os.environ, PYTHONPATH=тека))
        if р.returncode:
            raise SystemExit(р.stderr[-2000:])
        return json.loads(р.stdout.strip().splitlines()[-1])
    return _прогін(база(ref)), _прогін(ДЖЕРЕЛА)


def записи(маска, ref="origin/claude/zhyvi-pachka-15"):
    """[(шлях, промпт, відповідь)] записів стенда гілки `ref`, чия назва файла відповідає регулярці `маска`."""
    вих = []
    for ш in _git("ls-tree", "-r", "--name-only", ref, "--", "../аудит").splitlines():
        if "/VIDPOVIDI/" in ш and re.search(маска, ш.rsplit("/", 1)[-1]):
            г = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)$",
                         _git("show", "%s:%s" % (ref, ш)), re.S)
            вих += [(ш, г.group(1), г.group(2))] if г else []
    return вих
