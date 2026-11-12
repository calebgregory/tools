# Shared instructions

## git workflow: do not stage or commit

Do not stage (`git add`) or commit your own changes. The user reviews changes one commit at a time
after the agent has made them, and stages hunks as they read them — the staging area is how they track
what has already been reviewed. Staging or committing on the agent’s side destroys that record.

Leave all changes unstaged in the working tree. The user will say when they are done reviewing and
ready to commit. If there is an exception to this workflow, the user will say so explicitly.

## code review: watch the files you changed for my inline comments

After you write code, I review it in my editor, file by file, and leave comments inline in the files you
changed. Expect this as the normal next step. When you finish a change, watch each file you changed with
lemonaid, so that my comments wake you:

- with a brief: `lemonaid brief doc add --self <path> "review" --watch "All edits"` for each file;
- without one: `lemonaid watch doc --wait <path> --me <name> --once` as a background task.

The `watch-doc` and `brief` skills describe the waiter. Tell me which files you watch, then end the turn.

A comment can be a Relay Comment block or an ordinary code comment addressed to you. Treat any new
comment-shaped text from me as addressed to you. For each one:

- If it asks for a change, make the change. If the change resolves the comment, delete the comment.
- If it asks a question, or the change does not fully resolve it, answer in the chat. Leave my comment in
  place and prepend `🍋👀` to it, so that I can see in the file that you replied.

Keep watching until I say the review is done or until the code is committed.

## turn my corrections into principles or know-how

Each correction I make, in review comments or in chat, is a chance to teach the next session too. When a
correction sounds general rather than a one-off, propose an entry for it (the `extract-principle` skill
describes how; `/extract-principle` in Claude, `$extract-principle` in Codex). Write it only after I
confirm. Put it in one of two places:

- `~/tools/principles/`: a rule that holds anywhere. How to write code, tests and prose, and facts about
  public tools and libraries (pyarrow, attrs, k8s). This directory is in a public GitHub repo; don't
  write anything business-sensitive there.
- `~/tools/lemons/_shared/global/know-how.md`: a fact about my work systems. The `ds-monorepo` libraries
  and conventions (`thds.*`, mops, ADLS), our infrastructure, and services such as Databricks. This file
  is gitignored, because work-internal names and IDs must not go on the internet.

Many corrections are both: a general rule shown with a monorepo API. Split them. The rule goes in
principles, and the API goes in know-how.

Don't save these corrections to a project's memory directory. Project memory is visible only in that one
project, and I want every future session to get the correction.

## make provenance clear

When you create a PR, prefix the PR description with "🍋 ({model}): " so people know it's generated text.
Do the same for comments.  If you are working from a `lemonaid brief`, name yourself as part of model,
e.g., `"🍋 (SleepRib, opus 5.5)"`.

One exception - don't add a `Co-Authored-By` trailer, or any other agent attribution, to my commit
messages.
