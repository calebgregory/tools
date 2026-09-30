#!/usr/bin/env bash
# Keeps the `custom:system` Claude Code theme on the ANSI preset that matches the macOS
# appearance (dark-ansi or light-ansi). Claude Code reloads ~/.claude/themes/ live, so
# running sessions switch as soon as the file changes.
#
# Run from the SessionStart hook. Only one poller runs machine-wide (a mkdir lock), and it
# exits when no `claude` process remains, so it only runs while a session is open.
set -u

lock_dir="${TMPDIR:-/tmp}/claude-theme-follow-system.lock"
log_file="${TMPDIR:-/tmp}/claude-theme-follow-system.log"
theme_file="$HOME/.claude/themes/system.json"
poll_seconds=3

# The hook waits on its command's output, so detach and return immediately.
if [[ "${1:-}" != "--poll" ]]; then
  nohup "$0" --poll >>"$log_file" 2>&1 </dev/null &
  exit 0
fi

log() { echo "$(date '+%F %T') [$$] $*"; }

take_lock() {
  if mkdir "$lock_dir" 2>/dev/null; then
    echo $$ >"$lock_dir/pid"
    return 0
  fi
  local holder
  holder=$(cat "$lock_dir/pid" 2>/dev/null)
  if [[ -n "$holder" ]] && kill -0 "$holder" 2>/dev/null; then
    return 1
  fi
  # An empty pid file is normal for a moment right after another poller's mkdir; only
  # treat it as stale once the lock is old.
  if [[ -z "$holder" ]] && [[ -z "$(find "$lock_dir" -maxdepth 0 -mmin +1)" ]]; then
    return 1
  fi
  log "removing stale lock held by pid '${holder}'"
  rm -rf "$lock_dir"
  mkdir "$lock_dir" 2>/dev/null && echo $$ >"$lock_dir/pid"
}

system_base() {
  if defaults read -g AppleInterfaceStyle 2>/dev/null | grep -q Dark; then
    echo dark-ansi
  else
    echo light-ansi
  fi
}

take_lock || exit 0
trap 'rm -rf "$lock_dir"' EXIT
log "started"

current=""
while pgrep -x claude >/dev/null; do
  base=$(system_base)
  if [[ "$base" != "$current" ]]; then
    mkdir -p "$(dirname "$theme_file")"
    # Write elsewhere and rename so Claude Code never reads a half-written file.
    printf '{\n  "name": "Follow system (ANSI)",\n  "base": "%s"\n}\n' "$base" >"$lock_dir/system.json"
    mv "$lock_dir/system.json" "$theme_file"
    log "overwrote $theme_file with base $base (was '${current}')"
    current=$base
  fi
  sleep "$poll_seconds"
done

log "no claude sessions left; exiting"
