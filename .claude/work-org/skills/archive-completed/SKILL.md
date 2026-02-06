---
name: archive-completed
description: Move completed tasks from todo.md to the daily note (standalone — usually handled by /daily-note).
---

# Archive Completed Tasks

Move completed `[x]` tasks from todo.md to today's daily note.

**Note:** This is now handled automatically by `/daily-note`. Use this skill standalone only for mid-day archiving when you don't want to run the full daily-note workflow.

## Destination

`daily/{YYYY}/{YYYY-MM-DD}.md`

## Steps

1. Get today's date via `~/tools/relative_dates.py`
2. Read `todo/todo.md`, find all `[x]` tasks
3. Gather context (git commits, PR status, project grouping)
4. Append to `## Completed` section in daily note
5. Remove archived tasks from todo.md

## Context Enrichment

- **Git commits**: `git -C <monorepo> log --oneline --since="today" --author="<user>"`
- **PR links**: Note if merged
- **Project**: Read `current-project.md` for grouping

## Rules

- Only archive `[x]` tasks
- If parent is `[x]` but has `[ ]` subtasks, archive parent, keep subtasks in todo.md
- Don't duplicate — check what's already in Completed section
