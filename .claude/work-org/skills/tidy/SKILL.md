---
name: tidy
description: Assess and reorganize the todo list — sort by urgency, suggest groupings, normalize dates.
---

# Tidy Todo List

Analyze the todo list and suggest reorganization based on urgency and conceptual groupings.

## Steps

1. **Read todo.md** (see Environment in CLAUDE.md)
2. **Parse task structure**: identify all tasks, subtasks, due dates, statuses
3. **Assess urgency** for each task (see Urgency Order below)
4. **Identify grouping opportunities**:
   - Related tasks that could share a parent (e.g., multiple PR reviews → "PR reviews" parent)
   - Orphaned subtasks under completed parents → promote to top-level
   - Subtasks that are conceptually independent → suggest flattening
5. **Identify date normalizations** needed (relative → concrete)
6. **Present proposed changes** (see Output Format below)
7. **On confirmation**: apply changes to todo.md
8. **Confirm** what was changed

## Urgency Order

Sort tasks by urgency, most urgent first:

1. **Overdue** — due date has passed
2. **Due today with time** — "by noon" before "end of day"
3. **Due today** — no time qualifier
4. **Due tomorrow with time**
5. **Due tomorrow**
6. **Due this week** — ascending by date
7. **Due later** — ascending by date
8. **No due date** — at the bottom

**Parent inheritance**: A parent task inherits the urgency of its most urgent subtask. If a parent has no due date but a subtask does, the parent is sorted by that subtask's due date. This is not a conflict — it's how grouping works.

## Conceptual Grouping

Look for patterns:
- Multiple "review X PR" tasks → suggest "PR reviews" parent
- Multiple tasks mentioning same project/feature → suggest grouping
- Tasks with `{status: awaiting ...}` → could group under "Blocked / Waiting"

Only suggest groupings that reduce cognitive load. Don't over-organize.

## Date Normalization

Convert relative dates to concrete YYYY-MM-DD:
- "today" → current date
- "tomorrow" → next day
- "end of week" → Friday's date
- "end of month" → last day of month

Preserve time qualifiers: "by noon", "end of day", "at 10:30am"

## Output Format

```
## Proposed changes to todo.md

### Reorder by urgency
Current order → Proposed order:
1. [was #3] read and respond to Joe's PR... {due: today end of day}
2. [was #1] pick up support... {due: today by noon}
3. [was #2] support tasks
   ...

### Date normalizations
- "end of day today" → "2026-02-02 end of day"
- "end of week" → "2026-02-06"
- "end of month" → "2026-02-28"

### Grouping suggestions
- (none, or describe proposed grouping)

---
Apply changes? (yes / no / edit specific items)
```

## Rules

- Always show proposed changes before applying
- Don't reorder arbitrarily — only when urgency or grouping justifies it
- Preserve all links, tags, and notes
- Maintain proper indentation (tabs for subtasks)
- If no changes needed, say so and exit
- Completed `[x]` tasks: leave in place (archiving is separate)
