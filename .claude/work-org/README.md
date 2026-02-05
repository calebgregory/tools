# Work Task Manager — Skills & Workflows

## Data Model

```
todo/todo.md       → open tasks (the live list)
todo/today.md      → working file: voice memos, scratch notes
daily/{date}.md    → single source of truth per day
                     (Summary, Outline, Completed, Transcripts)
```

## End-of-Day Workflow

```
                    ┌─────────────────┐
                    │  todo/todo.md   │ (completed tasks)
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────┐    ┌─────────────────┐
│  todo/today.md  │───►│   /daily-note   │
│  (voice memos)  │    │                 │
└─────────────────┘    │ 1. archive [x]  │
                       │ 2. transcribe   │
                       │ 3. summarize    │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ daily/{date}.md │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │/standup tomorrow│
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ todo/tomorrow.md│
                       └─────────────────┘
```

**Steps:**
1. `/daily-note` — archives completed tasks, transcribes voice memos, generates summary
2. `/standup tomorrow` — generates tomorrow's standup from today's daily note + open tasks
3. Edit `todo/tomorrow.md` as needed, then post to DailyBot

## Morning Workflow

```
┌─────────────────┐
│ todo/tomorrow.md│ (prepared night before)
└────────┬────────┘
         │
         ▼
    copy to DailyBot
         │
         ▼
┌─────────────────┐
│  todo/today.md  │ (reset for new day's notes)
└─────────────────┘
```

## Weekly Update Workflow

```
┌─────────────────────────────────────┐
│  daily/2026/2026-02-{02-06}.md     │ (Mon-Fri daily notes)
└────────────────┬────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  /weekly-update │
        └────────┬────────┘
                 │
                 ▼
        formatted update for team channel
```

## Skills Reference

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `/daily-note` | Archive tasks, transcribe memos, summarize | End of day |
| `/standup [tomorrow]` | Generate standup update | End of day (`tomorrow`) or morning (default) |
| `/tidy` | Reorder todo.md by urgency | When list feels disorganized |
| `/weekly-update` | Generate weekly summary | Friday / end of week |
| `/archive-completed` | Archive tasks only (no transcription) | Mid-day cleanup |
| `/apply-update` | Process voice memo to update tasks | Ad-hoc task updates |

See [skills/](./skills/) for full documentation of each skill.

## Task Format

See [CLAUDE.md](../CLAUDE.md) for task format and environment details.
