---
name: tidy
description: Audit and reorganize todo files — scan for issues, normalize dates, reorder by urgency. Use for periodic cleanup and triage.
argument-hint: [all | home | wedding | <path>]
disable-model-invocation: true
---

# Tidy

Audit todo files for issues, normalize dates, reorder by urgency, and propose fixes.

## Scope

- `/tidy` — defaults to `todo/todo.md`
- `/tidy all` — all todo files across the vault (enables cross-file duplicate detection)
- `/tidy home` — `home/todo.md`
- `/tidy wedding` — all `projects/andrew-and-kayla-wedding/**/todo.md`
- `/tidy <path>` — specific file

When scanning, skip `.obsidian/`, `.git/`, `node_modules/`, `.venv/`, `_archive/`.

## Steps

1. Run `~/tools/relative_dates.py` to get date boundaries
2. Read target file(s)
3. **Scan for issues** (see Checks below)
4. **Normalize dates** — convert any relative dates to `YYYY-MM-DD` using keys from `relative_dates.py`
5. **Check section routing** — flag tasks in the wrong section for their due date (e.g., due tomorrow but in long-term)
6. **Reorder by urgency** within each section (see Urgency Order below)
7. **Present findings + proposed reorg**, ask for confirmation
8. **Apply changes** on confirmation

## Checks

1. **Overdue dates** with severity tiers:
   - ⚠️ Overdue < 1 month
   - 🔴 Overdue 1-6 months
   - 💀 Overdue > 6 months
2. **Missing area tags** — tasks with no `{area:...}` and not in an obviously-named section
3. **Vague tasks** — too vague to act on without decomposition
4. **Stale `{waiting:...}`** — flag so user can check if blocker resolved
5. **Empty sections** — note but don't remove (may be placeholders)
6. **Cross-file duplicates** — same or very similar task in multiple files (only when scope is `all`)

## Urgency Order

Within each section, most urgent first:

1. **Overdue** (most overdue first)
2. **Due today**
3. **Due tomorrow**
4. **Due this workweek** (ascending)
5. **Due this weekend** (ascending)
6. **Due later** (ascending)
7. **No due date**

Parent inherits urgency of its most-urgent subtask.

## Output Format

```
## Tidy Report

### Issues Found

**Overdue**
- 💀 "charity research" {due:2023-03-19} — `todo/todo.md` (~3 years overdue)
- ⚠️ ...

**Missing area tag**
- "gather stray tennis balls" — suggest `{area:home}`?

**Needs decomposition**
- "clean out email" — vague, could use concrete steps

**Stale waiting**
- "task" {waiting:reason} — check if resolved

**Cross-file duplicates** (all mode only)
- "task A" in `todo/todo.md` ↔ "task B" in `home/todo.md`

### Date Normalizations
- "end of week" → 2026-02-05
- ...

### Section Routing
- "call dentist" {due:2026-02-07} in long-term → should be short-term

### Proposed Reorder
[show before/after for sections that change]

---
Apply changes? (yes / no / pick specific items)
```

## Rules

- Present findings before applying any changes
- Don't be pedantic — only flag things genuinely useful to fix
- Preserve all links, tags, and notes
- Completed `[x]` tasks: leave in place (archiving is separate)
- Apply fixes in a single edit pass after confirmation
