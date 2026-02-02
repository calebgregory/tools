---
name: sweep
description: Scan the todo list for issues — missing tags, stale dates, duplicates, tasks that need attention. Use for periodic cleanup and triage.
disable-model-invocation: true
---

# Sweep Tasks

Scan `todo/todo.md` for issues and suggest fixes.

## Check for

1. **Missing area**: tasks with no `{area:...}` tag and not in an obviously-named section
2. **Stale dates**: `{due:...}` dates more than 2 months past
3. **No timeframe**: tasks with no due tag and no clear time horizon from their section
4. **Duplicates**: tasks that look like the same thing worded differently
5. **Empty sections**: sections with no tasks (these are fine to keep as placeholders, just note them)
6. **Vague tasks**: tasks that are too vague to act on without a breakdown

## Output format

```
## Sweep Results

### Missing area tag
- "gather stray tennis balls" — suggest `{area:home}`?

### Stale dates
- "charity research" — `{due:2023-03-19}` is ~3 years old

### Needs breakdown
- "clean out email" — vague, could use concrete steps

### Duplicates
- (none found)

Fix these? (y/n, or pick specific items)
```

## Rules

- Present findings, then ask before making changes
- Apply fixes in a single edit pass after confirmation
- Don't be pedantic — only flag things that are genuinely useful to fix
