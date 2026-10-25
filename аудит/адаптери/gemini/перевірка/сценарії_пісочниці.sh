#!/usr/bin/env bash
# Стенд пісочниці Codex (М.9-Г): справжній `codex` (змінна CODEX; перевірено 0.164.0, бекенд Linux) з дослівним профілем
# `$script:CodexConfig` із gemini_run.ps1. Логіка мірила поза Windows: команда сеансу не виходить у мережу, не читає
# токена Codex і входу agy, не пише `.git/config` і хуків (їх виконала б обгортка); коміт і гілка в робочій теці — є.
# Бекенд Windows (`elevated`) міряє проба ноутбука `m9v/3_пісочниця.ps1`. Вихід 1, якщо хоч один випадок не збігся.
set -u
H=$(cd "$(dirname "$0")" && pwd); SRC=$(cd "$H/.." && pwd); CX="${CODEX:-codex}"; bad=0
W="${TMPDIR:-/tmp}/gemini-obhortka/m9g-pisochnytsia"; rm -rf "$W"; mkdir -p "$W/home/.codex" "$W/home/.gemini" "$W/tmp"
python3 - "$SRC/gemini_run.ps1" > "$W/home/.codex/config.toml" <<'EOF'
import re, sys
s = open(sys.argv[1], encoding='utf-8-sig').read()
print(re.search(r"\$script:CodexConfig = @'\n(.*?)\n'@", s, re.S).group(1))
EOF
echo '{"tokens":{"refresh_token":"ФАЛЬШИВИЙ-ТОКЕН"}}' > "$W/home/.codex/auth.json"; echo 'ФАЛЬШИВИЙ-ВХІД' > "$W/home/.gemini/oauth"
git init -q "$W/repo"; echo a > "$W/repo/a.txt"; git -C "$W/repo" add a.txt
git -C "$W/repo" -c user.name=t -c user.email=t@x -c commit.gpgsign=false commit -q -m init
run() { (cd "$W/repo" && HOME="$W/home" CODEX_HOME="$W/home/.codex" TMPDIR="$W/tmp" "$CX" sandbox -P m9g -- sh -c "$1") 2>&1 | grep -v '^WARNING'; }
chk() { local got; got=$(run "$3"); if [[ "$got" == *"$2"* ]]; then echo "ok   $1"; else echo "FAIL $1: чекав «$2», є «$got»"; bad=1; fi; }
chk net-proxy   NET_DENIED  'curl -sS -m 5 https://example.com -o /dev/null && echo NET_OPEN || echo NET_DENIED'
chk net-direct  NET_DENIED  'env -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u http_proxy -u ALL_PROXY curl -sS -m 5 https://1.1.1.1 -o /dev/null && echo NET_OPEN || echo NET_DENIED'
chk codex-token AUTH_DENIED 'cat ~/.codex/auth.json && echo AUTH_READ || echo AUTH_DENIED'
chk agy-login   GEM_DENIED  'cat ~/.gemini/oauth && echo GEM_READ || echo GEM_DENIED'
chk codex-cfg   CFG_RO      'echo x >> ~/.codex/config.toml && echo CFG_W || echo CFG_RO'
chk git-config  GITCFG_RO   'git config core.fsmonitor "echo pwn" 2>/dev/null && echo GITCFG_W || echo GITCFG_RO'
chk git-hooks   HOOK_RO     'touch .git/hooks/pre-commit 2>/dev/null && echo HOOK_W || echo HOOK_RO'
chk commit      COMMIT_OK   'echo b > b.txt && git add b.txt && git -c user.name=g -c user.email=g@x -c commit.gpgsign=false commit -q -m b && git checkout -q -b gemini/x && echo COMMIT_OK'
chk tmp         TMP_OK      'mktemp >/dev/null && echo TMP_OK'
[[ -z "$(git -C "$W/repo" config --get core.fsmonitor)" && "$(git -C "$W/repo" log --format=%s -1 gemini/x 2>/dev/null)" == b ]] \
  && echo "ok   repo-after" || { echo "FAIL repo-after"; bad=1; }
exit $bad
