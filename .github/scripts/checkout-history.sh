#!/usr/bin/env bash
# Повна історія потрібна історичним базам проб і звіту правил.
# Явні refspec обмежують fetch головою, базою й main навіть за широкого remote.origin.fetch.
set -euo pipefail

base_ref=${BASE_REF:-refs/heads/main}
if [[ "$base_ref" =~ ^0+$ ]]; then
  base_ref=refs/heads/main
fi
head_sha=${GITHUB_SHA:-$(git rev-parse HEAD)}

# Checkout не лишає токена в .git/config; заголовок діє лише в цьому процесі.
if [ -n "${GITHUB_TOKEN:-}" ]; then
  auth=$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 | tr -d '\n')
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="http.${GITHUB_SERVER_URL:-https://github.com}/.extraheader"
  export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $auth"
fi

depth=()
if [ "$(git rev-parse --is-shallow-repository)" = true ]; then
  depth+=(--unshallow)
fi
git fetch --no-tags --no-recurse-submodules "${depth[@]}" origin \
  "$head_sha" "$base_ref" +refs/heads/main:refs/remotes/origin/main
if [ "$base_ref" = refs/heads/main ]; then
  base_ref=refs/remotes/origin/main
fi
git cat-file -e "${head_sha}^{commit}"
git cat-file -e "${base_ref}^{commit}"
git merge-base "$head_sha" "$base_ref"
