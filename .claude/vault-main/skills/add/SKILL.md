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
2. **Normalize the due date**: run `~/tools/relative_dates.py` and convert any relative date to `YYYY-MM-DD`:
   - "this week" / "end of week" → `end_of_workweek` (Thursday)
   - "friday", "saturday", etc. → the matching named day
   - "this month" / "end of month" → `end_of_month`
   - "tomorrow", "monday", etc. → the matching key
   - Already `YYYY-MM-DD` → keep as-is
   - No due date → no `{due:...}` tag
3. Determine the target file (see Routing above)
4. Determine the correct section within `todo/todo.md` using date arithmetic:
   - `due <= end_of_workweek` → **short term**
   - `due <= end_of_month` → **mid term**
   - `due > end_of_month` or no due → **long term**
   - Short term: pick subsection if applicable (random, buy, call, make, fix, listen, labor)
   - For project files: append to the end or the most appropriate section
5. Read the target file
6. Add the line `- [ ] <task description> <tags>` in the appropriate section
7. Write the file
8. Confirm with the single line you added, which file, and where

## Examples

`/add buy pegboard for garage {area:home} {due:end of month}` →
- Normalizes to `{due:2026-02-28}`
- Due is after workweek but within month → adds to `todo/todo.md` under **mid term**

`/add call barnes exterminators {due:tomorrow}` →
- Normalizes to `{due:2026-02-07}`
- Due is within workweek → adds to `todo/todo.md` under **short term > call**

`/add schedule final rehearsal with Andrew {project:andrew-and-kayla-wedding}` →
- Adds to `projects/andrew-and-kayla-wedding/planning/todo.md`

`/add research konnakol teachers {area:art}` →
- No due date → adds to `todo/todo.md` under **long term**

If no `$ARGUMENTS` are provided, ask what task to add.
