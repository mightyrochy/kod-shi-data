#!/usr/bin/env bash
# Стенд рушіїв М.9-В (pwsh 7, git, python3; PWSH — шлях до pwsh): fake_gemini.py і fake_codex.py через сценарії_прогону.sh.
# Кожен випадок: «ім'я | оточення | сценарій | модель | очікуваний фрагмент рядка вихідних». Вихід 1, якщо хоч один не збігся.
set -u
H=$(cd "$(dirname "$0")" && pwd); bad=0
case_() {
  local name=$1 env=$2 sc=$3 model=$4 want=$5 got
  got=$(env $env EXTRA="${EXTRA:-{\}}" "$H/сценарії_прогону.sh" "m9v-$name" "$sc" print "$model" 2>/dev/null | grep -F 'GEMINI ОБГОРТКА' | grep -v '^{' | tail -1)
  if [[ "$got" == *"$want"* ]]; then echo "ok   $name"; else echo "FAIL $name: чекав «$want», є «$got»"; bad=1; fi
}
case_ gcli-done        "X=1"             abandon_then_done gcli-gemini-3.5-flash 'ГОТОВО gemini/М.2-проба-обгортки'
case_ gcli-quota-line  "X=1"             abandon_then_done gcli-gemini-3.5-flash 'КВОТА GEMINICLI 71'
case_ gcli-429         "X=1"             quota429          gcli-gemini-3.5-flash 'ЗАБЛОКОВАНО gemini/М.2-проба-обгортки QUOTA'
case_ gcli-zero        "FAKE_STATS=zero" abandon_then_done gcli-gemini-3.5-flash 'QUOTA0_GEMINICLI'
case_ gcli-garbage     "FAKE_STATS=garbage" abandon_then_done gcli-gemini-3.5-flash 'ГОТОВО gemini/М.2-проба-обгортки'
case_ gcli-auth        "X=1"             auth              gcli-gemini-3.5-flash 'ЗАБЛОКОВАНО gemini/М.2-проба-обгортки AUTH'
case_ codex-done       "X=1"             abandon_then_done gpt-6.1-sol-high      'ГОТОВО gemini/М.2-проба-обгортки'
case_ codex-github     "X=1"             github            gpt-6.1-sol           'GITHUB_DIR'
case_ codex-blocked    "X=1"             blocked           gpt-6.1-sol-low       'BLOCKED'
EXTRA='{"CodexExe":"/нема/codex"}' case_ codex-missing "X=1" abandon_then_done gpt-6.1-sol 'ENGINE_MISSING'
EXTRA='{"GeminiFallbackModel":"gemini-3.5-flash"}' case_ fallback-to-gcli "FAKE_USAGE=flash0" abandon_then_done gemini-3.5-flash 'КВОТА GEMINICLI 71'
EXTRA='{"GeminiFallbackModel":"gemini-3.5-flash"}' case_ fallback-both0 "FAKE_USAGE=flash0 FAKE_STATS=zero" abandon_then_done gemini-3.5-flash 'QUOTA0_GEMINI35FLASH'
case_ agy-unchanged    "X=1"             abandon_then_done gemini-3.8-flash-high 'КВОТА GEMINI35FLASH 34'
# аргументи рушіїв: прапори й зусилля дослівно
a=$(cat "${TMPDIR:-/tmp}/gemini-obhortka/m9v-codex-done/fake/codex.argv.log" 2>/dev/null | head -1)
[[ "$a" == *'"-m", "gpt-6.1-sol"'* && "$a" == *'model_reasoning_effort=high'* && "$a" == *'--dangerously-bypass-approvals-and-sandbox'* ]] && echo "ok   codex-argv" || { echo "FAIL codex-argv: $a"; bad=1; }
exit $bad
