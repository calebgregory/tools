---
name: archive-completed
description: Move completed tasks from todo.md to the weekly archive file, enriched with context from git commits and related notes.
---

# Archive Completed Tasks

Move all completed `[x]` tasks from todo.md to the weekly archive, enriching them with context.

## Archive Location

`todo/_archive/{YYYY}/{MM-DD}.md` — named by the Monday of the current week.

Example: If today is Wednesday 2026-02-05, the file is `todo/_archive/2026/02-03.md` (Monday).

## Steps

1. **Calculate the Monday of this week** for the archive filename
2. **Read todo.md** (see Environment in CLAUDE.md)
3. **Find all completed tasks** (`- [x]` lines), including their subtasks and notes
4. **Gather context for each task**:
   - Check git log (monorepo) for today's commits by the user
   - If task has PR/GitHub links, note the resolution
   - Check if task relates to current project (read `current-project.md`)
   - Look for voice memo transcripts from today in `<project-dir>/cc/notes/` (get project dir from `current-project.md`)
5. **Determine archive structure** for each task:
   - Simple task with minimal context → single `[x]` line with brief note
   - Task with rich context → heading + task + indented elaboration
   - Adapt based on how much context is available
6. **Create or append to the weekly archive file**:
   - If file exists, append under today's date header
   - If file doesn't exist, create with week header and today's date
   - If today's date section exists, append to it
7. **Remove archived tasks from todo.md**
8. **Confirm** what was archived

## Archive File Format

```markdown
# Week of 2026-02-03

## 2026-02-03 Monday

- [x] simple task
  - Brief context note

## 2026-02-04 Tuesday

### larger task with context
- [x] task description [thread](url)
  - What was accomplished
  - Related commits: `abc123` (commit message)
  - Notes from daily memo: "relevant quote"
```

## Context Enrichment

**Git commits**: Run `git -C <monorepo> log --oneline --since="today" --author="<user>"` to find related commits. Match commits to tasks by keyword/branch name.

**PR links**: If task contains a GitHub PR URL, check if it was merged or its current status.

**Voice memos**: Read `current-project.md` to get project directory, then check `<project-dir>/cc/notes/` for today's transcripts. Extract relevant context.

**Project context**: Read `current-project.md` for current Shape-up project info.

## Rules

- Only archive tasks that are marked `[x]` — leave `[ ]` tasks in todo.md
- When a parent task is `[x]` but has `[ ]` subtasks, archive the parent but keep subtasks in todo.md (or ask)
- Preserve all links and tags when archiving
- Don't over-enrich — add context that's genuinely useful for weekly updates
- Create year directories as needed (`_archive/2026/`)
