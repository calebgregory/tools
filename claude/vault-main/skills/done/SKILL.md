---
name: done
description: Mark a task as completed. Use when the user says they finished something.
argument-hint: <partial task description to match>
disable-model-invocation: true
---

# Mark Task Done

Mark a task as completed in `todo/todo.md`.

## Steps

1. Read `todo/todo.md`
2. Fuzzy-match `$ARGUMENTS` against open tasks (`- [ ]` lines)
3. If exactly one match: mark it `[x]` and confirm
4. If multiple matches: show them numbered and ask which one
5. If no match: say so and suggest similar tasks
6. Write the updated file

## Rules

- Match is case-insensitive and partial — `/done towel` should match `- [ ] towel rack`
- Don't delete the task. Change `[ ]` to `[x]`.
- Confirm with the completed line

If no `$ARGUMENTS` are provided, ask what was completed.
