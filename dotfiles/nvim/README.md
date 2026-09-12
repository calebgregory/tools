# nvim

Config for working in `ds-monorepo`, where VS Code's multi-root workspace takes
20+ minutes to become usable. Symlinked to `~/.config/nvim` by
[symlink-dotfiles.sh](../bootstrap/symlink-dotfiles.sh).

## Finding your own keybindings

Three ways, no cheatsheet needed:

- `<leader>?` — fuzzy-search every mapping, with descriptions. Enter jumps to
  where it is defined.
- `:nmap`, `:imap`, `:vmap` — the built-in listing. `:nmap <leader>R` shows one.
- `:verbose nmap <leader>R` — adds the file and line that set it.

Leader is `<Space>`.

## Keybindings

### Code navigation

| Key | Does |
|---|---|
| `F12` | Go to definition. Crosses editable deps into `libs/*/src`. |
| `Shift+F12` | References — **current project only**, see below. |
| `K` | Hover docs |
| `<leader>R` | References across the whole repo, via ripgrep |
| `<leader>rn` | Rename symbol |
| `<leader>ca` | Code action |
| `[d` / `]d` | Previous / next diagnostic |
| `<leader>e` | Show diagnostic under cursor |

`Shift+F12` answers only for the project you are in. basedpyright is rooted at
the nearest `pyproject.toml`, which is what keeps startup near one second
instead of twenty minutes — it never loads the other ~99 projects, so it cannot
see references in them. `<leader>R` is the cross-project half: ripgrep for the
word under cursor, run from the git root.

### Finding files and text

| Key | Does |
|---|---|
| `Ctrl+p` / `<leader>ff` | Files in the current project |
| `<leader>fF` | Files across the repo |
| `<leader>fg` | Grep the current project |
| `<leader>fG` | Grep the whole repo |
| `<leader>fb` | Buffers |
| `<leader>fs` | Symbols in this file |
| `<leader>?` | Search keybindings |

### Source control

`<leader>gs` opens [codediff.nvim](https://github.com/esmuellert/codediff.nvim),
the VS Code Source Control view: a file panel listing changed files with status
(`M` / `A` / `D` / `??`) and a `Staged Changes` section, a side-by-side diff
whose **right pane is the editable working tree**, and staging from the panel.
It reuses VS Code's own diff algorithm, compiled to a native library — on first
run it downloads that library from the plugin's GitHub releases.

| Key | Does |
|---|---|
| `<leader>gs` | Open the source control view |
| `<leader>gh` | History for the current file |
| `<leader>gm` | Review this branch against `main` |
| `<leader>gp` | Review a pull request |

It is one command with subcommands, and `:CodeDiff <Tab>` completes git revs and
ranges as well — `:CodeDiff HEAD~3`, `:CodeDiff origin/main...`, `:CodeDiff merge`
for conflicts, `:CodeDiff dir` for a directory.

Inside the view, these are buffer-local:

| Key | Does |
|---|---|
| `<CR>` | Open the file under the cursor in the diff |
| `-` | Stage / unstage that file |
| `S` / `U` | Stage all / unstage all |
| `X` | **Discard** that file's changes — no undo |
| `]f` / `[f` | Next / previous file |
| `]c` / `[c` | Next / previous change within the diff |
| `do` / `dp` | Pull a change from / push one to the other pane |
| `K` | Show the full path |
| `R` | Refresh |
| `<leader>b` | Hide or show the panel |
| `<leader>e` | Jump back to the panel (shadows "show diagnostic" here) |

### Git in a normal buffer

[gitsigns](https://github.com/lewis6991/gitsigns.nvim) covers the same
operations at hunk granularity while you are editing, without opening the review
view. These attach only in a tracked file.

| Key | Does |
|---|---|
| `]h` / `[h` | Next / previous hunk |
| `<leader>hs` | Stage hunk |
| `<leader>hr` | Reset hunk |
| `<leader>hp` | Preview hunk |
| `<leader>hb` | Blame line |
| `<leader>hd` | Diff this file |

### File tree

[nvim-tree](https://github.com/nvim-tree/nvim-tree.lua), the direct NERDTree
successor. It shows git status per file and follows the buffer you are editing.
`.venv`, `.git` and `__pycache__` are filtered out — unfiltered, a tree rooted at
ds-monorepo lists the 83,499 files under the venvs instead of the 9,584 that are
checked in.

| Key | Does |
|---|---|
| `Ctrl+n` | Toggle the tree |
| `<leader>n` | Reveal the current file in the tree |

### Editing

Carried over from `.vimrc.after` and the VS Code vim settings.

| Key | Mode | Does |
|---|---|---|
| `jj` | insert | Escape |
| `Ctrl+c` | insert | Open a line above |
| `Ctrl+u` | normal | Upcase word under cursor |
| `Ctrl+j` / `Ctrl+k` | normal, visual | Move line or selection down / up |
| `Ctrl+w` `h/j/k/l` | normal | Focus window left/down/up/right (native) |

### Built in, worth knowing

Neovim 0.12 ships these; nothing here configures them.

| Key | Does |
|---|---|
| `]q` / `[q` | Next / previous quickfix entry |
| `]Q` / `[Q` | Last / first quickfix entry |
| `]b` / `[b` | Next / previous buffer |
| `]l` / `[l` | Next / previous location-list entry |
| `]a` / `[a` | Next / previous file in the arglist |
| `]D` / `[D` | Last / first diagnostic in the buffer |
| `]` / `[` | Add an empty line below / above |
| `]n` / `[n` | Next / previous treesitter node (visual mode) |
| `Ctrl+w` `d` | Show diagnostics under the cursor |

## Commands

| Command | Does |
|---|---|
| `:LspRoots` | Which servers are running and where each is rooted |
| `:TSInstallAll` | Install the treesitter parsers this config expects |
| `:lua vim.pack.update()` | Update plugins |
| `:ColorIdentifiersToggle` | Turn per-name identifier colors on or off |

## On save

Python goes through `ruff format` plus its fix-all code action, which is what
`editor.formatOnSave` and `source.fixAll` did in VS Code. Every other filetype
gets trailing whitespace trimmed.

## What's installed, and by whom

`mise` handles anything with a prebuilt binary in its registry — `neovim`,
`ruff`, `ty`, and `tree-sitter` (which nvim-treesitter shells out to when
compiling parsers). See [mise.toml](../mise.toml).

`uv` handles `basedpyright`, which mise has no registry entry for. See
[uv-tools.txt](../bootstrap/uv-tools.txt).

Plugins come from `vim.pack`, built into nvim 0.12, pinned in
[nvim-pack-lock.json](./nvim-pack-lock.json). There are two: `fzf-lua` for
finding things and `nvim-treesitter` for parsers.

## Color identifiers

Every occurrence of `patient_id` gets one color, every occurrence of `claim_id`
another, so you follow a value by hue instead of by reading — the same thing the
VS Code and Emacs `color-identifiers` modes do.

This is [our own module](./lua/color_identifiers.lua) rather than a plugin.
[markid](https://github.com/david-kunz/markid) is the neovim plugin for it, but
it is an nvim-treesitter *module*, and the module system no longer exists on
nvim-treesitter's main branch. None of its five forks fixed that.

Only variables get an identity color. Function names, method names, class names,
constructors, decorators, builtin types and `self` are all left alone — a name
that denotes a function is not a value you track through a function body. The
classification comes from the language's own treesitter highlights query, so
there is no table of node types to maintain.

It pairs with the theme by design. `colors/minimal.lua` leaves `@variable` at the
base foreground because coloring by *kind* is noise; this colors by *identity*,
which is the part worth seeing.

## The theme

[colors/minimal.lua](./colors/minimal.lua) ports
[the VS Code Minimal theme](../../vscode/minimal-color-theme). The palette is
Gruvbox Dark, but the palette is not the point — it colors a short list
(comments, strings, escape sequences, numeric and character constants,
definition names, control-flow keywords, punctuation, errors) and leaves
everything else at the base foreground.

Definitions and references are deliberately different. `def build` and
`class UaInput` are yellow because they define something; `x: Path`, `int`,
`str` and `PipelineKwargs(...)` are gray, because a reference to a type is
scaffolding, not the subject of the line. Python's treesitter query captures both
as `@type`, so [after/queries/python/highlights.scm](./after/queries/python/highlights.scm)
re-captures the definition site as `@type.definition` to tell them apart. Installing a stock gruvbox would restore
the colors and lose the restraint, so most of that file links captures back to
`Normal` on purpose.
