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

## How the config is laid out

[init.lua](./init.lua) does nothing but set the leader key and require the
modules under [lua/config](./lua/config), each of which runs for its side
effects and returns nothing. Two steps in that order break the config if you
move them, and the entry point says why: `config.pack` runs first because
`vim.pack.add` is what
puts the plugins on the runtimepath, and the leader is set before
`config.keymaps` because a `<leader>` mapping resolves the leader when it is
defined, not when it is pressed.

The modules divide by what they are responsible for:

- [pack](./lua/config/pack.lua) — the plugin list
- [options](./lua/config/options.lua) — editor options
- [appearance](./lua/config/appearance.lua) — the colorscheme, and following macOS light/dark
- [keymaps](./lua/config/keymaps.lua) — editing and LSP mappings
- [find](./lua/config/find.lua) — the fzf-lua pickers, project and repo wide
- [treesitter](./lua/config/treesitter.lua) — parsers, installed on demand
- [git](./lua/config/git.lua) — gitsigns and the `:CodeDiff` source-control view
- [filetree](./lua/config/filetree.lua) — nvim-tree
- [surround](./lua/config/surround.lua) — nvim-surround
- [jump](./lua/config/jump.lua) — flash.nvim, the jump labels
- [lsp](./lua/config/lsp.lua) — basedpyright and ruff, one server per project root
- [mypy](./lua/config/mypy.lua) — type diagnostics, run on save
- [format](./lua/config/format.lua) — what happens when you write a file

[lua/color_identifiers.lua](./lua/color_identifiers.lua) sits outside that
directory on purpose. It is a plugin we happen to keep in this repo, with a
`setup()` you call, rather than configuration that runs on load.

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

#### Reviewing a PR commit by commit

The GitHub PR extension in VS Code shows a PR as one flattened diff. codediff
lets you pick the commit, or the range of commits, you actually want to look at.
Nothing here needs the branch checked out: `pr` fetches into private refs and
leaves the working tree alone.

```vim
" the whole PR, base..head, as one diff
:CodeDiff pr 512
:CodeDiff pr 512 --base release/3.x

" the PR's commits as a list, each expandable into the files it touched;
" <CR> on a file diffs that commit against its parent
:CodeDiff history origin/main..HEAD
:CodeDiff history origin/main..HEAD --reverse   " oldest first

" one commit against its parent, in the explorer view
:CodeDiff abc123~1 abc123

" a span of commits, e.g. everything pushed since you last reviewed
:CodeDiff <last-reviewed-sha> HEAD

" drop the fetched PR refs when you are done
:CodeDiff pr clean 512
:CodeDiff pr clean --all
```

The `history` form wants the PR's commits locally. Either check the branch out,
or run `:CodeDiff pr 512` first and point history at the ref it fetched:

```vim
:CodeDiff history origin/main..refs/codediff/pull-requests/origin/512/head
```

Explorer keys above apply; in the history panel `<CR>` also expands a commit,
`i` switches the file list between flat and tree, and `R` re-fetches.

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

### Jumping

[flash.nvim](https://github.com/folke/flash.nvim) labels the places you can
jump to and you press a label to go there. It replaces easymotion, which draws
its labels by writing them into the buffer and undoing the edit afterwards —
linters and diagnostics see those edits. flash draws labels as extmarks, so
the buffer text never changes.

| Key | Mode | Does |
|---|---|---|
| `s` | normal, visual, operator | Type any characters, then press a label to jump |
| `S` | normal, operator | Select the treesitter node at a label |
| `r` | operator | Operate on a textobject elsewhere, cursor comes back — `dr<label>` |
| `R` | operator, visual | Treesitter search |
| `/` `?` | normal | Labels on every search match |
| `Ctrl+s` | search prompt | Turn the search labels off for this one search |
| `f` `t` `F` `T` | normal, visual, operator | Labels on the other targets, so you skip counting and `;` |

At a `/` prompt you press the label itself rather than Enter first, and flash
only hands out characters that cannot continue your pattern, so typing more of
the pattern and picking a label never conflict. Enter jumps to the first match
the way a normal search does.

`s` and `S` used to be the built-in substitute. `cl` and `cc` are the same two
commands. `S` stays out of visual mode, where nvim-surround wants it.

After an `f` or `t`, the labels stay up for a moment, so a key that is a label
would shadow whatever it normally does. The keys held back from the label pool
are `hjkliardc`, which flash chooses, plus `p` and `P`, so that `fx` then `p`
still pastes. The pool is case-sensitive: `I`, `A`, `R`, `D` and `C` are still
labels, and if one of them gets in the way, add it to `label.exclude` in
[jump](./lua/config/jump.lua).

The labels are bold text in `orange_hi`, the one color nothing else in the
theme uses. It is set in [the theme](./colors/minimal.lua) rather than in the
flash config, because
flash registers its highlight groups with `default = true` and leaves alone any
group the colorscheme already defines. The backdrop that dims everything else
is set there too: flash links it to `Comment` by default, and `Comment` in this
theme is red, so the whole buffer turned red while you picked a label.

### Surrounds

[nvim-surround](https://github.com/kylechui/nvim-surround). The character you
type picks the pair: `"` `'` `` ` ``, `(` `[` `{` `<`, a tag with `t`, or any
other single character surrounds with itself. An opening bracket adds inner
spaces and a closing one does not, so `ysiw(` gives `( word )` and `ysiw)`
gives `(word)`.

| Key | Mode | Does |
|---|---|---|
| `ys<motion><char>` | normal | Surround the motion — `ysiw"` quotes a word |
| `yss<char>` | normal | Surround the whole line |
| `ds<char>` | normal | Delete the surrounding pair |
| `cs<old><new>` | normal | Change one pair into another |
| `S<char>` | visual | Surround the selection |
| `yS` / `ySS` / `gS` | normal, visual | Same, with the pair on its own lines |
| `Ctrl+g` `s` | insert | Surround the cursor position |

`S` in visual mode used to be the built-in linewise change. `c` does that, so
`Vc` is the replacement for `VS`.

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
| `:Mypy` | Re-run mypy on this buffer, without waiting for a save |
| `:MypyToggle` | Turn mypy diagnostics on or off |

## On save

Python goes through ruff's organize-imports and fix-all code actions and then
`ruff format`, in that order. The formatter runs last because the two code
actions rewrite code and the formatter is what tidies up after them. This is
`editor.formatOnSave` and `source.fixAll` from VS Code, plus import sorting,
which `ruff format` does not do on its own — sorting is isort's job, and ruff
exposes it as a code action instead.

Every other filetype gets trailing whitespace trimmed. Every file ends in a
newline, which is nvim's own default ('fixeol') rather than anything this
config arranges.

## Type checking

mypy reports the type errors, basedpyright does the navigation. basedpyright
runs with `typeCheckingMode` set to `off`, so it still answers hover,
go-to-definition, references and rename but stays quiet about types. mypy is
what CI enforces, and two checkers disagreeing in the sign column about the
same line, in different words, costs more than the second opinion is worth.

mypy is not a language server, so it does not arrive through `vim.lsp`. We run
it on save and push what it says into `vim.diagnostic`. It has to be the
project's own `.venv/bin/mypy` rather than one on `PATH` — each root installs
its own, and the versions differ between them, so a single global binary would
report against the wrong config and the wrong dependencies. A project whose
venv has no mypy gets one warning and no mypy diagnostics.

It runs when you open a Python file and again every time you save one, so a
file tells you what mypy makes of it without your having to write it first.
`:MypyToggle` turns it off when it is in the way.

Two things to know about it. mypy's incremental cache is what makes this
usable: the first run in a project takes a few seconds, and later ones are
about a third of a second. And a buffer's mypy diagnostics are only ever what
mypy said about *that file* — if your change breaks a file that imports this
one, you see it when you save that file, not this one. CI is what catches the
rest.

## What's installed, and by whom

`mise` handles anything with a prebuilt binary in its registry — `neovim`,
`ruff`, `ty`, and `tree-sitter` (which nvim-treesitter shells out to when
compiling parsers). See [mise.toml](../mise.toml).

`uv` handles `basedpyright`, which mise has no registry entry for. See
[uv-tools.txt](../bootstrap/uv-tools.txt).

Plugins come from `vim.pack`, built into nvim 0.12, pinned in
[nvim-pack-lock.json](./nvim-pack-lock.json). There are seven: `fzf-lua` for
finding things, `nvim-treesitter` for parsers, `codediff.nvim` and
`gitsigns.nvim` for source control, `nvim-tree.lua` for the file tree,
`nvim-surround` for quotes and brackets, and `flash.nvim` for jumping.

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
Gruvbox medium, but the palette is not the point — it colors a short list
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

### Light and dark

nvim follows the macOS system appearance. [appearance](./lua/config/appearance.lua)
reads it at startup, whenever the window gets the focus back, and every 15
seconds, then sets `'background'` from the answer; the colorscheme reads
`'background'` and picks one of the two palettes in
[lua/minimal/palette.lua](./lua/minimal/palette.lua).

The clock is there because focus is not enough. macOS has no way to tell a
terminal program that the appearance changed, and toggling it from the menu bar
with nvim already in front never focuses or unfocuses anything — so a
focus-driven check leaves the editor in the wrong theme until you tab away and
come back. The tmux status bar has the same problem and solves it the same way,
on the same interval, by running its script from the status redraw.

That palette file is one table of *roles*, each row carrying its dark and light
value together. The roles are named for the job (`fg_bright`, `line_nr`,
`orange_hi`) rather than for the color, because several of them change sides
between the two: light-mode red is `#9d0006`, darker than the code beside it,
where dark-mode red is brighter than it. Keeping both halves on one row is also
what stops the palettes from drifting — you cannot add a color to one without
adding it to the other. The selection and search washes are derived rather than
listed, by mixing a palette color into that palette's background, since a
terminal has no alpha channel.

nvim is one of three things reading that setting, and they agree because they
all ask macOS rather than each other: wezterm picks its scheme from its own
appearance API ([.wezterm.lua](../.wezterm.lua)), and the tmux status bar and
window titles come from [tmux/appearance.sh](../tmux/appearance.sh), which also
parks the answer in the `@appearance` tmux option. The bar colors and the window
title palette both live in
[colors.json](../../main/src/tools/tmux/colors.json), shared by tmux and
wezterm, with a dark and a light value per entry.

Two things outside nvim are worth knowing. tmux has to be told to forward the
focus event (`set -g focus-events on` in [.tmux.conf](../.tmux.conf)) or nvim
never learns you came back at all. And nvim's own guess has to be displaced: it asks
the terminal for its background color at startup (OSC 11) and sets
`'background'` from the reply. Asking macOS is the better question to ask,
because it is the same one wezterm answers when it picks its own scheme and the
same one the tmux status bar reads, so the three cannot disagree — and none of
it rests on an OSC 11 reply surviving the trip out through tmux. Setting
`'background'` in the config is what disables nvim's guess; it drops its own
autocommand at `VimEnter` when it sees the config already set the option.
