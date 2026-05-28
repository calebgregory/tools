# Minimal Color Theme

A personal fork of [Rubber](https://github.com/apust/vscode-rubber-theme) using
the [Gruvbox Dark](https://lospec.com/palette-list/gruvbox-dark) palette
(Medium contrast: `#282828` background, `#ebdbb2` foreground).

Rubber follows the "less is more" approach to syntax highlighting described in
Nikita Prokopov's
[Syntax highlighting is a mess](https://tonsky.me/blog/syntax-highlighting/) —
highlight a few load-bearing tokens (strings, constants, top-level defs,
comments) and leave the rest at the base color, so the eye actually catches
what matters. This fork keeps Rubber's restraint and only swaps in
Gruvbox-family hues.

## Install

```sh
./install.sh
```

Symlinks this directory into `~/.vscode/extensions/`. Then reload VS Code
(`Cmd+Shift+P` → `Developer: Reload Window`) and pick **Minimal** from the
theme picker.
