#!/usr/bin/env bash
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="$HOME/.vscode/extensions/minimal-color-theme"

if [ -L "$target" ]; then
	current="$(readlink "$target")"
	if [ "$current" = "$src" ]; then
		echo "Already linked: $target -> $src"
		exit 0
	fi
	echo "Replacing existing symlink at $target (was -> $current)"
	rm "$target"
elif [ -e "$target" ]; then
	echo "Refusing to overwrite non-symlink at $target" >&2
	exit 1
fi

ln -s "$src" "$target"
echo "Linked $target -> $src"
echo "Reload VS Code (Cmd+Shift+P -> 'Developer: Reload Window') and pick 'Minimal' from the theme picker."
