#!/bin/sh
# Print how far review of the working tree has gotten, in changed lines:
#
#     <unstaged> / <uncommitted> (<percent staged>)
#
# A changed line is an added or a deleted line, so a modified line counts twice.
# Untracked files count as unstaged, every line added.  Binary files and
# submodules do not count.  Prints nothing outside a repo or when the tree is
# clean.

set -eu

cd "$1" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# numstat reports binary files as "-	-	path".
sum_numstat() {
    awk '$1 != "-" { n += $1 + $2 } END { print n + 0 }'
}

staged=$(git diff --cached --numstat --ignore-submodules | sum_numstat)
unstaged=$(git diff --numstat --ignore-submodules | sum_numstat)
# grep -I counts 0 lines in a binary file.  /dev/null keeps the filename prefix
# on single-file output and gives grep an argument when there are no files.
untracked=$(
    git ls-files -z --others --exclude-standard \
        | xargs -0 grep -cI '' /dev/null \
        | awk -F: '{ n += $NF } END { print n + 0 }'
)

not_staged=$((unstaged + untracked))
not_committed=$((staged + not_staged))
[ "$not_committed" -eq 0 ] && exit 0

# tmux interprets #[...] style sequences in #() output.  The colors match the
# modified and staged styles in .gitmux.conf.
not='#[fg=yellow,bold,italics]'
tot='#[fg=default,bold]'
pct='#[fg=green,bold]'
clear='#[fg=default,nobold,noitalics]'
printf '%s | %s%d%s of %s%d%s (%s%d%%%s)' \
    "$clear" \
    "$not" "$not_staged" "$clear" \
    "$tot" "$not_committed" "$clear" \
    "$pct" "$((staged * 100 / not_committed))" "$clear"
