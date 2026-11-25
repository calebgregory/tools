# Shared instructions

## git workflow: do not stage or commit

Do not stage (`git add`) or commit your own changes. The user reviews changes one commit at a time
after the agent has made them, and stages hunks as they read them — the staging area is how they track
what has already been reviewed. Staging or committing on the agent’s side destroys that record.

Leave all changes unstaged in the working tree. The user will say when they are done reviewing and
ready to commit. If there is an exception to this workflow, the user will say so explicitly.

## code review: write a review guide, then answer my comments

After you finish a round of changes for me to review, including a round of fixes, follow lemonaid's
`review-guide` skill: it writes a guide that orders the changes for reading, opens it in my editor,
watches it and the files you changed, answers my comments in their threads, and keeps comments out of
commits. My preferences for guides are in its overlay. Tell me which files you watch, then end the
turn. Keep watching until I say the review is done or until the code is committed.

If the skill isn't installed, watch each file you changed instead, so that my comments wake you:

- with a brief: `lemonaid brief doc add --self <path> "review" --watch "All edits"` for each file.
  That only records the subscription; check with `lemonaid watch --self --status` that something
  delivers it, and start a watcher if none runs, as the `brief` skill says.
- without one: start a waiter for each file as the `watch-doc` skill says for your harness.

Whether or not the skill is installed, I comment with lemonaid's review comments, threads kept in the
file. Read them with `lemonaid comments list <path> --unanswered --self` and answer each in its thread
with `lemonaid comments reply`; `lemonaid comments --help` has the rest.

## turn my corrections into principles or know-how

Each correction I make, in review comments or in chat, is a chance to teach the next session too. When a
correction sounds general rather than a one-off, propose an entry for it (the `extract-principle` skill
describes how; `/extract-principle` in Claude, `$extract-principle` in Codex). Write it only after I
confirm. Put it in one of three places:

- `~/tools/principles/`: a rule for writing code, tests and prose that holds anywhere, and facts about
  public tools and libraries (pyarrow, attrs, k8s). This directory is in a public GitHub repo; don't
  write anything business-sensitive there.
- `~/tools/lemons/_shared/global/know-how/for-lemons/`: how a lemon should work. Its workflow (reviews,
  hand-offs), the quirks of its own tools, and my setup (lemonaid, nvim, tmux). This directory is public
  too. List a new file in `~/tools/lemons/_shared/global/index.md`.
- `~/tools/lemons/_shared/global/know-how/private.md`: a fact about my work systems. The `ds-monorepo`
  libraries and conventions (`thds.*`, mops, ADLS), our infrastructure, and services such as Databricks.
  This file is gitignored, because work-internal names and IDs must not go on the internet.

Many corrections are both: a general rule shown with a monorepo API. Split them. The rule goes in
principles, and the API goes in `know-how/private.md`.

Don't save these corrections to a project's memory directory. Project memory is visible only in that one
project, and I want every future session to get the correction.

## make provenance clear

When you create a PR, prefix the PR description with "🍋 ({model}): " so people know it's generated text.
Do the same for PR comments or Slack messages.  If you are working from a `lemonaid brief`, name yourself
as part of model, e.g., `"🍋 (SleepRib, opus 5.5)"`.

Two exceptions - don't add a `Co-Authored-By` trailer, or any other agent attribution, to my commit
messages.  If you are responding to my comments in a document using `lemonaid comments`, you don't need to
name yourself; the display of the comment already tells me who you are.
