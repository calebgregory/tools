---
name: cycle-review
description: Transcribe voice memos in an end-of-cycle review file, extract key points, and replace recordings with summaries.
argument-hint: <cycle-number>
---

# Cycle Review

Transcribe audio recordings embedded in an end-of-cycle review file, write transcripts alongside it, and replace the recording embeds with extracted key points linking back to the full transcripts.

## Arguments

- Cycle number (e.g., `13`) — resolves to `end-of-cycle-reviews/cycle-{N}/cycle-{N}.md`

## Source

`end-of-cycle-reviews/cycle-{N}/cycle-{N}.md` — markdown file structured as `# Cycle {N}` → `## Self Review` → `### question headings` with `![[Recording ...]]` embeds under `###` headings. Audio files live in the same directory.

## Steps

### 1. Parse the review file

1. Read the review file
2. For each `![[Recording ....m4a]]` embed, note:
   - The audio filename
   - The `###` heading it falls under (this determines the transcript's descriptive name)

### 2. Transcribe recordings

1. For each recording, derive a kebab-case filename from the section heading (e.g., "What went well?" → `went-well.md`)
2. Transcribe in parallel: `transcribe <audio-path> -o <transcript-path>`
   - Transcripts are written to the same directory as the review file (e.g., `end-of-cycle-reviews/cycle-{N}/went-well.md`)

### 3. Apply transcription corrections

1. Read transcription corrections from memory (`memory/transcription-corrections.md`)
2. Apply known corrections to each transcript file
3. If new likely-misheard terms are found, flag them to the user and update the corrections file upon confirmation

### 4. Replace recordings with summaries

For each section that had a recording:

1. Read the transcript
2. Extract the most important points as a concise numbered list (or single bullet if brief)
3. Replace the `![[Recording ...]]` embed with:
   - A `[transcript](./{name}.md)` link (relative to review file)
   - The extracted key points

Preserve the `##` headings and any non-recording content in the file.

## Output Structure

```markdown
# Cycle {N}

## Self Review

### Question heading

[transcript](./name.md)

1. **Key point** — supporting detail
2. **Key point** — supporting detail
```

## Rules

- First-person perspective — write as the user speaking ("I did X", not "did X")
- Key points should be substantive, not just restating the question
- Use as many points as the content warrants (typically 1-7 per section)
- If a recording is brief or noncommittal, a single bullet is fine (e.g., "- I'm not sure")
- Bold the lead of each point, then add supporting detail after an em dash
