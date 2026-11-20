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
