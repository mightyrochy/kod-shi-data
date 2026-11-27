#!/usr/bin/env bash
# Доказ повного CI прив'язаний до дерева синтетичного коміту PR, його бази й спроби запуску.
set -euo pipefail

znayty_dokaz() {
  local sha derevo batko holova zapusky zapusk sproba artefakt
  local repo="repos/$GITHUB_REPOSITORY"
  [[ ${BASE_SHA:-} =~ ^[0-9a-f]{40}$ ]] || return 1
  sha=$(git rev-parse HEAD) || return 1
  derevo=$(git rev-parse 'HEAD^{tree}') || return 1
  batko=$(git cat-file commit "$sha" | sed -n '2s/^parent //p') || return 1
  [[ "$batko" = "$BASE_SHA" ]] || return 1

  holova=$(gh api --paginate "$repo/commits/$sha/pulls?per_page=100" |
    jq -r --arg sha "$sha" --arg repo "$GITHUB_REPOSITORY" '
      .[] | select(.merged_at and .merge_commit_sha == $sha and .base.ref == "main"
        and .base.repo.full_name == $repo and .head.repo.full_name == $repo
        and .user.login == "mightyrochy") | .head.sha') || return 1
  [[ "$holova" =~ ^[0-9a-f]{40}$ ]] || return 1

  zapusky=$(gh api "$repo/actions/workflows/zbirka.yml/runs?event=pull_request&head_sha=$holova&per_page=20" |
    jq -r --arg sha "$holova" --arg repo "$GITHUB_REPOSITORY" '
      .workflow_runs[] | select(.head_sha == $sha and .head_repository.full_name == $repo
        and .event == "pull_request" and .status == "completed" and .conclusion == "success")
      | [.id, .run_attempt] | @tsv') || return 1
  [[ -n "$zapusky" ]] || return 1
  while read -r zapusk sproba; do
    artefakt="perevirene-${derevo}-${BASE_SHA}-${sproba}"
    if gh api "$repo/actions/runs/$zapusk/artifacts?name=$artefakt" |
      jq -e --arg imia "$artefakt" '.artifacts | any(.name == $imia and .expired == false)' >/dev/null; then
      printf 'run_id=%s\nartifact=%s\n' "$zapusk" "$artefakt" >> "$GITHUB_OUTPUT"
      printf 'Дерево %s на базі %s пройшло CI в запуску %s, спроба %s.\n' \
        "$derevo" "$BASE_SHA" "$zapusk" "$sproba" >> "$GITHUB_STEP_SUMMARY"
      return 0
    fi
  done <<< "$zapusky"
  return 1
}

zberehty_dokaz() {
  local chastyna derevo teky="$RUNNER_TEMP/dokaz"
  [[ "$BASE_SHA" =~ ^[0-9a-f]{40}$ ]]
  [[ "$BASE_SHA" = "$(git cat-file commit HEAD | sed -n '2s/^parent //p')" ]]
  derevo=$(git rev-parse 'HEAD^{tree}')
  mkdir -p "$teky"
  git rev-parse HEAD > "$teky/sha"
  cp index.html "$teky/"
  cp джерела/аудит/ДОСЯЖНІСТЬ.md "$teky/"
  for chastyna in 0 1; do
    mkdir "$teky/replay-$chastyna"
    cp "$RUNNER_TEMP/perevirene-zapysy/replay-summary-$chastyna-$GITHUB_SHA/replay-summary.json" \
      "$teky/replay-$chastyna/підсумок.json"
  done
  printf 'artifact=perevirene-%s-%s-%s\n' "$derevo" "$BASE_SHA" "$GITHUB_RUN_ATTEMPT" >> "$GITHUB_OUTPUT"
}

zibraty() {
  local teky=$1 sha
  sha=$(git rev-parse HEAD)
  # У перевіреному HTML міняється лише оголошення штампа, синтетичний SHA → фактичний SHA злиття.
  python3 - "$teky" "$sha" <<'PY'
from pathlib import Path
import re
import sys

тека, новий = Path(sys.argv[1]), sys.argv[2]
старий = (тека / 'sha').read_text().strip()
if not re.fullmatch('[0-9a-f]{40}', старий):
    raise SystemExit('У доказі нема SHA перевіреного коміту PR')

показ = (тека / 'index.html').read_bytes()
рід = 'const ЗБІРКА_ПОКАЗУ = "'.encode()
старий_штамп = рід + старий.encode() + b'"'
if показ.count(старий_штамп) != 1:
    raise SystemExit('Штамп показу не відповідає SHA перевіреного коміту PR')
Path('index.html').write_bytes(показ.replace(старий_штамп, рід + новий.encode() + b'"'))
PY
  cp "$teky/ДОСЯЖНІСТЬ.md" джерела/аудит/
}

case "${1:-}" in
  --доказ) zberehty_dokaz ;;
  --зібрати) zibraty "$2" ;;
  '')
    if ! znayty_dokaz; then
      echo 'Нема доказу зеленого CI того самого дерева на базі злиття. Іде повний шлях.' >> "$GITHUB_STEP_SUMMARY"
    fi
    ;;
  *) exit 2 ;;
esac
