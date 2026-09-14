#!/bin/sh
# Point the tmux status bar at the macOS light/dark setting.
#
# macOS reports the appearance through one global default, and only when it is
# Dark: in Light mode the key does not exist and `defaults` exits 1.  nvim reads
# the same default (nvim/lua/config/appearance.lua) and wezterm reads the same
# setting through its own API (.wezterm.lua), so the three agree without having
# to talk to each other.
#
# tmux 3.5 added `client-light-theme` and `client-dark-theme` hooks, which would
# be the right way to do this, but they fire only when the terminal announces
# its theme and wezterm does not: `#{client_theme}` is empty for every client.
#
# We also park the answer in @appearance, which the window title script reads as
# its last argument -- it runs once per window per status refresh, far too often
# to ask macOS itself.

set -eu

COLORS="$HOME/tools/main/src/tools/tmux/colors.json"

if [ "$(defaults read -g AppleInterfaceStyle 2>/dev/null)" = "Dark" ]; then
    appearance=dark
else
    appearance=light
fi

# client-focus-in fires on every pane switch.  Everything above this line is one
# `defaults` read; everything below spawns python and redraws the bar, so do it
# only when the answer actually changed.
if [ "$(tmux show-option -gqv @appearance)" = "$appearance" ]; then
    exit 0
fi

# The bar colors live beside the window-title palette rather than here, because
# wezterm's tab bar reads the same file and has to land on the same gray.
read -r bar_bg bar_fg current_bg <<EOF
$(python3 -c '
import json, sys
from pathlib import Path
chrome = json.loads(Path(sys.argv[1]).read_text())["chrome"]
print(*(chrome[k][sys.argv[2]] for k in ("bar_bg", "bar_fg", "current_bg")))
' "$COLORS" "$appearance")
EOF

tmux set -g @appearance "$appearance"
tmux set -g status-style "bg=$bar_bg,fg=$bar_fg"
tmux set -gw window-status-style "bg=$bar_bg"
tmux set -gw window-status-current-style "bg=$current_bg"
