# Shared instructions

## principle extraction

When the user corrects your code or gives a stylistic/architectural instruction that
sounds like a general principle (not a one-off), suggest invoking the
`extract-principle` skill (`/extract-principle` in Claude, `$extract-principle` in Codex).

## git workflow: do not stage or commit

Do not stage (`git add`) or commit your own changes. The user reviews changes one commit at a time
after the agent has made them, and stages hunks as they read them — the staging area is how they track
what has already been reviewed. Staging or committing on the agent’s side destroys that record.

Leave all changes unstaged in the working tree. The user will say when they are done reviewing and
ready to commit. If there is an exception to this workflow, the user will say so explicitly.

## make provenance clear

When you create a PR, prefix the PR description with "🍋: " so people know it's generated text. Do the
same for comments.
