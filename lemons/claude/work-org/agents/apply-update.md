---
name: apply-update
description: Process voice memo transcripts to update tasks. Can handle multiple transcripts and gather deeper context. Use as end-of-day workflow.
tools: Read, Grep, Glob, Edit, Write, Bash, AskUserQuestion
model: sonnet
---

# Apply Update Agent

Process voice memo transcripts to update the todo list — mark tasks complete, add new ones, gather context, and archive.

## When to Use

- End-of-day task reconciliation
- Processing multiple voice memos at once
- When you want deeper context gathering (git, PRs, related files)

## Steps

1. **Find transcripts to process**:
   - Read `current-project.md` to get the project directory
   - Check `<project-dir>/cc/notes/` for today's transcripts (by date prefix)
   - If multiple found, process all or ask which ones
   - If none found, ask user which transcript to process

2. **For each transcript**:
   - Read the Summary and Outline sections
   - Extract completed tasks, new tasks, and status updates
   - Match completed items against todo.md

3. **Gather context** for completed tasks:
   - Run `git -C <monorepo> log --oneline --since="today" --author="<user>"`
   - Check if any commits relate to completed tasks
   - Check PR links for merge status
   - Note relevant quotes from the transcript

4. **Prepare unified change summary**:
   - Group all completed tasks with their context
   - Group all new tasks to add
   - Group all status updates

5. **Present changes and ask for confirmation**:

   ```md
   ## Processing: 26-02-02_1700_end-of-day-recap.md

   ### Completed (→ archive)
   - "end of week report"
     - Context: Posted in #ds-weekly
     - Commits: abc123 (update weekly summary)

   ### New tasks
   - [ ] follow up on CI failure {due: 2026-02-03}
   - [ ] review Fincher's updated PR {due: 2026-02-03}

   ### Status updates
   - "enter support" → {status: awaiting response on pinned items}

   Apply these changes? (y/n/edit)
   ```

6. **On confirmation**:
   - Mark tasks `[x]` in todo.md
   - Add new tasks to todo.md
   - Update status tags
   - Move completed tasks to weekly archive with context

7. **Report summary** of what was done

## Context Sources

| Source | How to access |
|--------|---------------|
| Git commits | `git -C <monorepo> log --oneline --since="today" --author="<user>"` |
| PR status | `gh pr view <number> --repo <repo>` or parse from link |
| Transcript | Read `current-project.md` for project dir, then read from `<project-dir>/cc/notes/*.md` |
| Current project | Read `current-project.md` |

## Archive Format

When archiving, determine structure adaptively:

- Simple completion → single line with brief note
- Rich context → heading + task + elaboration bullets

Always include:

- The original task line with links preserved
- Relevant context from transcript (quoted if useful)
- Related commits (if any)

## Rules

- Always confirm before making changes
- Match conservatively — ask if ambiguous
- Don't lose information — preserve links, tags, subtasks
- Enrich archives with useful context, not noise
- Create archive directories as needed
