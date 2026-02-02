---
name: breakdown
description: Break a vague or large task into concrete next actions. Use when a task needs decomposition into smaller steps.
argument-hint: <partial task description to match>
disable-model-invocation: true
---

# Break Down Task

Decompose a task into concrete, actionable subtasks.

## Steps

1. Read `todo/todo.md`
2. Fuzzy-match `$ARGUMENTS` against open tasks
3. If multiple matches, ask which one
4. Propose 2-5 concrete next actions as subtasks (indented under the parent)
5. Each subtask should be a single, completable action — not another vague item
6. Show the proposed breakdown and ask for confirmation
7. On confirmation, replace the original task line with the parent + indented subtasks in the file

## Example

Before:
```
- [ ] reverse osmosis filter
```

After:
```
- [ ] reverse osmosis filter {area:home}
  - [ ] research RO filter options and price range
  - [ ] measure under-sink space
  - [ ] order filter
  - [ ] install filter (or schedule installation)
```

## Rules

- Keep the parent task line — subtasks are indented under it
- Preserve any existing tags on the parent
- Each subtask should start with a verb
- Don't over-decompose — 2-5 steps is the sweet spot

If no `$ARGUMENTS` are provided, ask which task to break down.
