---
name: session-recap
description: End-of-session recap for re-entry after days away. Shows what changed, what's due soon, and where to pick up.
---

# Session Recap

Generate a recap of recent vault activity and upcoming deadlines for easy re-entry.

## Git note

The vault root is NOT a git repo. Some subdirectories have their own `.git/` (e.g., individual projects). Do not run `git` commands from the vault root — they will error. Instead:
- Use `find` or `Glob` to locate `.git/` directories within the vault
- Run git commands only from within directories that have a `.git/`
- If no git repos are found, skip all git steps and rely on todo file scanning only

## Steps

1. Find git repos in the vault: look for `.git/` directories (skip `.obsidian/`, `node_modules/`, `.venv/`, `_archive/`)
2. For each git repo found, run `git -C <repo-path> log --oneline --since="3 days ago"` and `git -C <repo-path> diff --name-only HEAD~10 2>/dev/null` to find recent changes
3. Scan all `todo.md` files (skip `.obsidian/`, `.git/`, `node_modules/`, `.venv/`, `_archive/`) for:
   - Items with `{due:...}` dates within the next 7 days
   - Items tagged `{due:this week}`
   - Items recently marked `[x]` (cross-reference with git diffs if available)
4. Group activity by type:
   - **Tasks completed** — recently checked off
   - **Files changed** — notes, todo edits, new files
   - **Coming up** — items due within 7 days
5. Present the recap before writing
6. Ask the user (via AskUserQuestion): "Anything to note before I save this recap?"
7. Write to `todo/most-recent-recap.md` (overwrite previous recap) — only after user confirms

## Output format

```
# Session Recap — [date range]

## What happened
- [1-line summary per activity, grouped by type]
- See `path/to/file.md`

## Due this week
- [ ] [item] (due [date]) — from [file]

## Where to pick up
[2-3 sentences: what's most urgent, what's next natural step, any decisions pending]
```

## Rules

- Keep it to ~20 lines max — this is a quick re-entry tool, not a full review
- Only mention files that actually changed — don't list the whole vault
- If no git repos are found in the vault, just do the todo scan portion
- Never run git commands from the vault root — it is not a git repo
- Overwrite `todo/most-recent-recap.md` each time (only the latest recap matters)
- Ask before writing the file
