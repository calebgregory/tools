---
name: review
description: Show a status overview of all open tasks across the vault. Use when starting a session, when the user asks what's going on, or wants to see their task list.
---

# Review Tasks

Scan all `todo.md` and `contact.md` files across the vault and present a unified status overview.

## Steps

1. Find all `todo.md` and `contact.md` files under the vault root (skip `.obsidian/`, `.git/`, `node_modules/`, `.venv/`, `_archive/`)
2. Read each file
3. Count open tasks (`- [ ]`) per life area, inferring area from `{area:...}` tags or the project context
4. Identify overdue/due-soon items and stalled tasks
5. Note any pending contacts from `contact.md` files

## Output format

```
## Status

- **Overdue / due soon**: (list specific tasks with past or imminent due dates)
- **home**: N open
- **art**: N open
- **work**: N open
- **community**: N open
- **admin**: N open

### Contacts to reach out to
- (pending contacts from todo/contact.md)

### By project
- andrew-and-kayla-wedding: N open (across planning, meetings, ideation)
- dance (AJA): N open
- woodworking/yoga_wall: N open
- home: N open
- (personal): N open

### Stalled
- (tasks with due dates >2 months past, or that look forgotten)
```

## Rules

- Keep it to ~15 lines max unless there's a lot to flag
- Count tasks by `{area:...}` tag; if no tag, infer from the project/section they're in
- "Stalled" = due date >2 months past, or anything that looks forgotten
- Don't list every task — summarize. Only enumerate specific tasks for overdue/stalled items.
- Today's date is available from the system; use it to evaluate due dates
