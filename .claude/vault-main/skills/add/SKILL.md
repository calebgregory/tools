---
name: add
description: Add a task to the todo list. Use when the user wants to capture a new task or reminder.
argument-hint: <task description> {area:home|art|work|community|admin} {due:...} {project:...}
disable-model-invocation: true
---

# Add Task

Add a task to the appropriate `todo.md` file in the vault.

## Routing

- If the task is about contacting/catching up with someone → `todo/contact.md`
- If `{project:...}` is specified, or the task clearly belongs to a known project, add it to that project's `todo.md`:
  - `{project:andrew-and-kayla-wedding}` → `projects/andrew-and-kayla-wedding/planning/todo.md` (default; use `meetings/todo.md` or `ideation/todo.md` if the task is clearly a meeting or research item)
  - `{project:dance}` or AJA-related → `projects/dance/todo.md`
  - `{project:woodworking}` or `{project:yoga-wall}` → `projects/woodworking/yoga_wall/todo.md`
- If the task is a home improvement item tied to a specific room → `home/todo.md`
- Otherwise, add to `todo/todo.md`

## Steps

1. Parse the argument: extract the task description and any metadata tags (`{area:...}`, `{due:...}`, `{waiting:...}`, `{project:...}`)
2. Determine the target file (see Routing above)
3. Determine the correct section within the file:
   - For `todo/todo.md`: if `{due:...}` is near-term or "this week" → **short term**; "this month" → **mid term**; "someday" or no due → **long term**
   - For `todo/todo.md` short term: pick subsection if applicable (random, buy, call, make, fix, listen, labor)
   - For project files: append to the end or the most appropriate section
4. Read the target file
5. Add the line `- [ ] <task description> <tags>` in the appropriate section
6. Write the file
7. Confirm with the single line you added, which file, and where

## Examples

`/add buy pegboard for garage {area:home} {due:this month}` →
- Adds to `todo/todo.md` under **mid term**

`/add call barnes exterminators {due:this week}` →
- Adds to `todo/todo.md` under **short term > call**

`/add schedule final rehearsal with Andrew {project:andrew-and-kayla-wedding}` →
- Adds to `projects/andrew-and-kayla-wedding/planning/todo.md`

`/add research konnakol teachers {area:art}` →
- Adds to `todo/todo.md` under **long term**

If no `$ARGUMENTS` are provided, ask what task to add.
