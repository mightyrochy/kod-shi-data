#!/usr/bin/env bash
# Стенд рушіїв М.9-В (pwsh 7, git, python3; PWSH — шлях до pwsh): fake_codex.py через сценарії_прогону.sh.
# Кожен випадок: «ім'я | оточення | сценарій | модель | очікуваний фрагмент рядка вихідних». Вихід 1, якщо хоч один не збігся.
set -u
H=$(cd "$(dirname "$0")" && pwd); bad=0
case_() {
  local name=$1 env=$2 sc=$3 model=$4 want=$5 got
  got=$(env $env EXTRA="${EXTRA:-{\}}" "$H/сценарії_прогону.sh" "m9v-$name" "$sc" print "$model" 2>/dev/null | grep -F 'GEMINI ОБГОРТКА')
  if [[ "$got" == *"$want"* ]]; then echo "ok   $name"; else echo "FAIL $name: чекав «$want», є «$got»"; bad=1; fi
}
case_ codex-done       "X=1"             abandon_then_done gpt-6.1-sol-high      'ГОТОВО gemini/М.2-проба-обгортки'
case_ codex-github     "X=1"             github            gpt-6.1-sol           'GITHUB_DIR'
case_ codex-blocked    "X=1"             blocked           gpt-6.1-sol-low       'BLOCKED'
EXTRA='{"CodexExe":"/нема/codex"}' case_ codex-missing "X=1" abandon_then_done gpt-6.1-sol 'ENGINE_MISSING'
EXTRA='{"CodexFallbackModel":"gpt-6.1-sol-high"}' case_ fallback-to-codex "FAKE_USAGE=flash0" abandon_then_done gemini-3.5-flash 'МОДЕЛЬ gpt-6.1-sol-high'
EXTRA='{"CodexFallbackModel":"gpt-6.1-sol-high"}' case_ fallback-not-needed "X=1" abandon_then_done gemini-3.5-flash 'КВОТА GEMINI35FLASH'
case_ no-fallback-zero "FAKE_USAGE=flash0" abandon_then_done gemini-3.5-flash 'QUOTA0_GEMINI35FLASH'
case_ codex-429        "X=1"             quota429          gpt-6.1-sol 'ЗАБЛОКОВАНО gemini/М.2-проба-обгортки QUOTA'
case_ codex-auth       "X=1"             auth              gpt-6.1-sol 'AUTH'
case_ agy-unchanged    "X=1"             abandon_then_done gemini-3.8-flash-high 'КВОТА GEMINI35FLASH 34'
# каскад моделей за пулом (М.9-В, доповнення): код — flash → Codex; проєктування — pro → claude-opus-5-5-high → Codex
case_ cascade-code-stays "X=1"                abandon_then_done gemini-3.5-flash     'МОДЕЛЬ gemini-3.5-flash'
EXTRA='{"CodexFallbackModel":"gpt-6.1-sol-high"}' case_ cascade-design-claude "FAKE_USAGE=proclaude" abandon_then_done gemini-3.1-pro-high 'МОДЕЛЬ claude-opus-5-5-high'
EXTRA='{"CodexFallbackModel":"gpt-6.1-sol-high"}' case_ cascade-design-codex  "FAKE_USAGE=ok"        abandon_then_done gemini-3.1-pro-high 'МОДЕЛЬ gpt-6.1-sol-high'
case_ cascade-design-none "FAKE_USAGE=ok" abandon_then_done gemini-3.1-pro-high 'QUOTA0_GEMINI31PRO'
# /usage: формат табів, версійна брама
case_ usage-tsv    "FAKE_USAGE=tsv"       abandon_then_done gemini-3.5-flash 'КВОТА GEMINI35FLASH 34'
case_ usage-nohdr  "FAKE_USAGE=tsv_nohdr" abandon_then_done gemini-3.5-flash 'ГОТОВО gemini/М.2-проба-обгортки'
case_ usage-old    "FAKE_VERSION=1.1.10"  abandon_then_done gemini-3.5-flash 'ГОТОВО gemini/М.2-проба-обгортки'
case_ usage-oldnoquota "FAKE_VERSION=1.1.10 FAKE_USAGE=flash0" abandon_then_done gemini-3.5-flash 'МОДЕЛЬ gemini-3.5-flash'
if grep -q '"/usage"' "${TMPDIR:-/tmp}/gemini-obhortka/m9v-usage-old/fake/argv.log"; then echo "FAIL usage-old-argv: /usage кликано на 1.1.10"; bad=1; else echo "ok   usage-old-argv"; fi
# пули для диспетчера: pools.json і рядок ПУЛИ
case_ pools-line "FAKE_USAGE=tsv" abandon_then_done gemini-3.5-flash 'ПУЛИ V=1.1.11 G=GEMINI35FLASH:34:137 G=GEMINI31PRO:0:137 G=CLAUDEGPT:0:137 M=gemini-3.8-flash-high,claude-opus-5-5-high'
# аргументи рушіїв: прапори й зусилля дослівно
a=$(cat "${TMPDIR:-/tmp}/gemini-obhortka/m9v-codex-done/fake/codex.argv.log" 2>/dev/null | head -1)
[[ "$a" == *'"-m", "gpt-6.1-sol"'* && "$a" == *'model_reasoning_effort=high'* && "$a" == *'--dangerously-bypass-approvals-and-sandbox'* ]] && echo "ok   codex-argv" || { echo "FAIL codex-argv: $a"; bad=1; }
exit $bad
