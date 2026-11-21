# Caleb's nvim

- Caleb runs nvim in a pane of the same tmux session as the lemon. Every nvim listens on a socket at
  `$TMPDIR/nvim.caleb.gregory/*/nvim.<pid>.0`, where `<pid>` is the `nvim --embed` child of the
  pane's `nvim` process. To open a file there, find the pane (`tmux list-panes -s -F '#{pane_pid}
  #{pane_current_command}'`) and follow its process down to the embed child: the pane's process is
  usually his shell, with `nvim` as its child and the embed process below that (`pgrep -P <pid>`
  at each step). Then call nvim with a Lua expression rather than keystrokes, which would type into
  whatever mode he is in:
  `nvim --server <sock> --remote-expr "luaeval('vim.cmd(\"vsplit \" .. vim.fn.fnameescape(_A))', '<path>')"`.
  Open it in a split: a plain `:edit` replaces his current buffer, and the next file he opens replaces
  it again. Tell him which tmux window it is in, since his client may be looking at another.

## A selection's range: check it against a yank

`getregionpos()` and `getregion()` report a visual selection without a final line break that a yank
of the same selection keeps. With `'selection'` inclusive, a selection that ends past its line's last
character (`$`, or an empty line) includes that line's break. With exclusive, a selection that ends
on column 1 of a later line includes the previous line's break, and a single position on an empty
line selects that line's break. With `old`, whether a yank keeps the break depends on where the
selection starts. Code that turns a selection into a range should compare its text with what `y`
takes, across these modes and around empty lines. lemonaid's nvim client does this in
`lua/lma/selection.lua`, and its test compares against yanks.
