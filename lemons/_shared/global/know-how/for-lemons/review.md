# Review

## Send fixes back to the reviewer before handing the work over

When a reviewer (a person, or another agent you asked) finds problems and you fix them, send the fixes
back to the same reviewer before you tell the user the work is ready. A fix is new code that nobody has
reviewed yet, and the reviewer already knows what it asked for, so it is the cheapest check of whether
the fix holds. Repeat until the reviewer's verdict is "ready", and only then hand the work to the user,
with the reviewer's verdict.

## Point a reviewer at the base commit, not at `git diff`

Caleb stages hunks as he reads them, so a plain `git diff` shows only what he hasn't read yet, and a
reviewer given it misses the rest. When you ask for a review of uncommitted work, name the commit the
work starts from and ask for `git diff <base>` plus untracked files, and ask the reviewer not to touch
the index, which is his record of what he has read.
