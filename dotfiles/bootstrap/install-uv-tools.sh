#!/bin/bash

### install the global uv tools listed in uv-tools.txt
###
### --force makes re-runs idempotent, and resolves executable-name collisions
### in favor of whichever spec is listed last.

manifest=~/tools/dotfiles/bootstrap/uv-tools.txt

while IFS= read -r line; do
  line="${line%%#*}"
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [ -z "${line}" ] && continue

  read -ra spec <<< "${line}"
  for i in "${!spec[@]}"; do
    spec[i]="${spec[i]/#\~/${HOME}}"
  done

  if output=$(uv tool install --force "${spec[@]}" 2>&1); then
    echo "✔ ${spec[*]}"
  else
    echo "x ${spec[*]}"
    echo "${output}" | sed 's/^/    /'
  fi
done < "${manifest}"

echo "done"
