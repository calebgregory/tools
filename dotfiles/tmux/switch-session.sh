#!/bin/sh
# Switch this client to the session numbered $1 in the status bar's session list.
# The number is the session's @index option, written by tmux-session-index
# (~/tools/main); looking it up there, rather than counting list-sessions
# output again, guarantees the key picks the session whose number is on screen.
set -eu

target=$(tmux list-sessions -f "#{==:#{@index},$1}" -F '#{session_id}')
if [ -n "$target" ]; then
    tmux switch-client -t "$target"
fi
