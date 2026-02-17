---
name: review
description: Show a status overview of all open tasks across the vault. Use when starting a session, when the user asks what's going on, or wants to see their task list.
---

# Review Tasks

Scan all `todo.md` and `contact.md` files across the vault and present a unified status overview.

## Steps

1. Run `relative-dates` to get date boundaries
2. Find all `todo.md` and `contact.md` files under the vault root (skip `.obsidian/`, `.git/`, `node_modules/`, `.venv/`, `_archive/`)
3. Read each file
4. Count open tasks (`- [ ]`) per life area, inferring area from `{area:...}` tags or the project context
5. Classify tasks by date:
   - **Overdue** — `{due:YYYY-MM-DD}` before today
   - **Due today**
   - **Due this week** — `[today, end_of_week]`
   - **Due this month** — `[end_of_week+1, end_of_month]`
   - **Later / no date**
6. Note any pending contacts from `contact.md` files

## Urgency Order

When listing tasks, order by urgency:

1. Overdue (most overdue first)
2. Due today
3. Due tomorrow
4. Due this workweek (ascending)
5. Due this weekend (ascending)
6. Due later (ascending)
7. No due date

## Output format

```
## Status

### Overdue
- 💀 "task" {due:2023-03-19} (almost 3 years) — `todo/todo.md`
- 🔴 "task" {due:2025-10-01} (4 months) — `file.md`
- ⚠️ "task" {due:2026-01-20} (2 weeks) — `file.md`

### Due this week
- "task" {due:2026-02-06} (today) — `file.md`
- "task" {due:2026-02-07} (tomorrow) — `file.md`

### Counts by area
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

- Keep it to ~20 lines max unless there's a lot to flag
- Count tasks by `{area:...}` tag; if no tag, infer from the project/section they're in
- "Stalled" = due date >2 months past, or anything that looks forgotten
- Don't list every task — summarize. Only enumerate specific tasks for overdue/due-soon/stalled items.
- Display due dates with parenthetical context: `{due:2026-02-07} (tomorrow)`
