# lemonaid

- `~/tools/lemonaid` is the checkout the installed `lemonaid` runs from (an editable `uv tool` install;
  it is also a submodule of `~/tools`). Never switch branches or edit there: develop in a worktree under
  `~/lemonaid-wt/<branch>` (`git worktree add ~/lemonaid-wt/<branch> -b <branch> main` from
  `~/tools/lemonaid`), not inside `~/tools`, where it would show as untracked. lemonaid's `AGENTS.md`
  has the rest of the rules, such as running anything but pytest through `scripts/sandbox`.
- lemonaid's edit hooks record an edit as the lemon's own only when the command line names the file. A
  script that opens the file itself (a heredoc'd `python3 -` that edits a path written inside it) goes
  unrecorded, and the lemon's own doc waiter wakes it on its own change. Pass the path as an argument:
  `python3 - <path> <<'EOF'`.
