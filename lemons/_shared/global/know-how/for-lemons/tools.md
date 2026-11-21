# Tools

Quirks of the tools a lemon works with, and how to check what they tell you.

## Check that a search can match before trusting an empty result

An empty search result proves nothing until you know the pattern can match. `git grep -E` uses POSIX
extended regular expressions, which have no `\b`, so a pattern containing it silently matches nothing and
a search for leftover names reports none. Spell the boundary out (`name([^a-z_]|$)`), or use `git grep -P`
where PCRE is available. Before relying on "no matches", run the pattern once against a line you know is
there.

The same holds for a replacement. macOS's BSD `sed` has no `\b` either, so `sed 's/\bNAME\b/_NAME/g'`
silently changes nothing. Do word-boundary replacements with Python's `re`, and grep for the new name
afterwards.

## Write escape sequences with a shell heredoc, not Claude Code's Write tool

Claude Code's Write tool turns `\uXXXX` escapes in the content it writes into the characters
themselves, so `"\u2028"` in Python source becomes a literal line separator and `` `\u003e` `` in a
doc becomes `` `>` ``. When a file must contain a backslash escape, write it with a quoted shell
heredoc (`cat > file <<'EOF'`), whose content reaches the file byte for byte, or build the character
in code (`chr(0x2028)`). Afterwards, check the file with `grep` for the escape you meant to write.

## Expand `~` yourself in an `env` argument

In `env PATH=~/bin:$PATH cmd`, the `PATH=...` is an argument to `env`, not a shell assignment, so the
shell leaves `~` as it is and `cmd` searches a directory literally named `~`. A lookup then falls
through to whatever is next on `PATH`, silently: a test meant to run a worktree's `lemonaid` ran the
installed one. Write `$HOME` instead of `~` there.

## End a headless nvim script on every path

`nvim --headless -u script.lua` runs the script and then waits for input. If the script raises before
its final `qa!`, nvim sits there until an outer timeout kills it, and the run looks like a hang with
no output. Run the script's body under `xpcall`, then write the results and quit whether or not it
succeeded. Write each check to a file as it runs too, so a run that does hang shows how far it got.

## Compare nvim buffer names, not the paths you opened

On macOS, `/tmp` is a symlink to `/private/tmp`, and nvim names a buffer by the resolved path. A
buffer opened as `/tmp/x/code.py` is named `/private/tmp/x/code.py`. Code that keys anything by a
buffer's name (`nvim_buf_get_name`) won't match the path a test built from `/tmp`. Take the name from
the buffer.
