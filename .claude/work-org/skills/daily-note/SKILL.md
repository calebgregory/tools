---
name: daily-note
description: Transcribe and summarize voice memos from today.md into a composite daily note.
argument-hint: [date]
---

# Daily Note

Transcribe voice memos embedded in `todo/today.md`, accumulate transcripts, and generate a composite summary. Designed for incremental use throughout the day.

## Arguments

- No argument: process today's memos
- `yesterday`: process yesterday's memos
- `YYYY-MM-DD`: process a specific date

## Source

`todo/today.md` — contains Obsidian audio embeds: `![[path/to/audio.m4a]]`

## Destination

`daily/{YYYY}/{YYYY-MM-DD}.md` — composite note with summary + raw transcripts

## Temp Directory

`.out/{YYYY-MM-DD}/` — transcripts cached here, named by mtime

## Steps

1. **Parse source file** for `![[...m4a]]` or `![[...mp3]]` links
   - Extract audio file paths (resolve relative to vault root if needed)

2. **For each audio file**:
   - Get file mtime (use `stat -f %m` on macOS)
   - Check if transcript exists in `.out/{date}/{mtime}_{basename}.txt`
   - If not, transcribe: `transcribe <audio-path> -o <temp-transcript-path>`

3. **Concatenate transcripts** (sorted by mtime):
   - Format each with a header showing the time: `## HH:MM` (derived from mtime)
   - Preserve the raw transcript text

4. **Generate summary**:
   - Use all transcripts as context
   - First-person perspective (user is the speaker)
   - Format as: Summary (2-3 sentences) + Outline (things worked on, tasks, insights)
   - If destination file already exists, read it to understand what's already summarized

5. **Write destination file**:
   ```
   # Daily Note — YYYY-MM-DD

   ## Summary

   {composite summary}

   ## Outline

   {merged outline: things worked on, tasks, insights}

   ---

   # Transcripts

   ## HH:MM

   {transcript 1}

   ## HH:MM

   {transcript 2}
   ```

## Incremental Behavior

When run multiple times in a day:
- Only transcribe new audio files (check by mtime in temp dir)
- Append new transcripts to existing ones
- Re-generate summary incorporating all content
- New information should update/extend the summary, not replace unrelated parts

## Summary Format

Use the same style as confident-confidant:

- **Summary**: 2-3 sentences, first-person, what I worked on and key outcomes
- **Outline**:
  - Things I worked on (bullet points)
  - Tasks for the future (`- [ ] task`)
  - Insights or points to ponder

## Notes

- mtime is Unix timestamp; convert to readable time for headers
- Audio files are typically in `todo/cc/audio/` or relative paths from today.md
- If no audio embeds found, report that and exit
