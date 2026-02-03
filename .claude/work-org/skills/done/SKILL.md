---
name: done
description: Mark a work task as completed. Use when the user says they finished something.
argument-hint: <partial task description to match>
disable-model-invocation: true
---

# Mark Task Done

Mark a task as completed in the work todo file.

## Steps

1. Read the todo file (see Environment in CLAUDE.md)
2. Fuzzy-match `$ARGUMENTS` against open tasks (`- [ ]` lines)
3. If exactly one match: mark it `[x]` and confirm
4. If multiple matches: show them numbered and ask which one
5. If no match: say so and suggest similar open tasks
6. Write the updated file

## Matching Rules

- Match is case-insensitive and partial
- `/done fincher` should match `- [ ] review Fincher's PR ...`
- `/done support` should match `- [ ] enter support via Fincher's message ...`
- Match against the task description, not the links or tags

## Rules

- Don't delete the task — change `[ ]` to `[x]`
- Preserve all links, tags, and subtasks on the line
- If the task has subtasks, only mark the specific line matched (not the whole tree)
- Confirm with the completed line

If no `$ARGUMENTS` are provided, ask what was completed.
