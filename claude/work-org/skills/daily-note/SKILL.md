---
name: daily-note
description: Transcribe and summarize voice memos from today.md into a composite daily note.
argument-hint: [date]
---

# Daily Note

End-of-day workflow: archive completed tasks, transcribe voice memos, and generate a composite summary. Designed for incremental use throughout the day.

## Arguments

- No argument: process today
- `yesterday`: process yesterday
- `YYYY-MM-DD`: process a specific date

## Source Files

- `todo/todo.md` — completed tasks to archive
- `todo/today.md` — Obsidian audio embeds: `![[path/to/audio.m4a]]`

## Destination

`daily/{YYYY}/{YYYY-MM-DD}.md` — composite note with summary, completed tasks, and transcripts

## Temp Directory

`.out/{YYYY-MM-DD}/` — transcripts cached here, named by mtime

## Steps

### 1. Archive completed tasks

1. Read `todo/todo.md` and find all `[x]` tasks
2. If any completed tasks exist:
   - Gather context (git commits, PR status) — see Context Enrichment below
   - Append to `## Completed` section in the daily note
   - Remove archived tasks from todo.md
3. If no completed tasks, skip to transcription

### 2. Transcribe voice memos

1. Parse `todo/today.md` for `![[...m4a]]` or `![[...mp3]]` links
2. For each audio file:
   - Get file mtime (use `stat -f %m` on macOS)
   - Check if transcript exists in `.out/{date}/{mtime}_{basename}.txt`
   - If not, transcribe: `transcribe <audio-path> -o <temp-transcript-path>`
3. Concatenate transcripts (sorted by mtime) with `## HH:MM` headers
4. Append to `# Transcripts` section (avoid duplicating existing transcripts)

### 3. Generate summary

1. Read the full daily note (completed tasks + transcripts)
2. Generate/update:
   - **Summary**: 2-3 sentences, first-person, what I worked on and key outcomes
   - **Outline**: Things worked on, tasks for the future, insights

## Daily Note Structure

```markdown
# Daily Note — YYYY-MM-DD

## Summary

{composite summary}

## Outline

**Work completed:**
- bullet points

**Follow-ups:**
- [ ] task

**Notes:**
- insights

## Completed

### project name

- [x] task description [thread](url)
  - context note
  - commit: `abc123`

---

# Transcripts

## HH:MM

{transcript text}
```

## Context Enrichment (for completed tasks)

**Git commits**: `git -C <monorepo> log --oneline --since="today" --author="<user>"` — match to tasks by keyword/branch

**PR links**: If task has GitHub PR URL, note if merged

**Project context**: Read `current-project.md` for grouping

## Incremental Behavior

When run multiple times:
- Only archive newly-completed tasks (check what's already in Completed section)
- Only transcribe new audio files (check by mtime)
- Re-generate summary incorporating all content

## Rules

- First-person perspective (user is the speaker in transcripts)
- Don't over-enrich completed tasks — add context useful for weekly updates
- Preserve existing content when updating
- If no completed tasks AND no audio embeds, report that and exit
