---
name: swift-scribe-transcription-fallback
description: swift-scribe is the local (Apple Speech) fallback when the `transcribe` CLI fails on OpenAI credits
metadata:
  type: reference
---

`swift-scribe <audio-file> -o out.txt` (on PATH, `~/.local/bin`) transcribes locally with Apple Speech. Use it when `transcribe` fails with an OpenAI 429 `credit_balance_exhausted` error. Its output is rougher (choppy punctuation, more misheard terms), so apply [[transcription-corrections]] more aggressively.

**How to apply:** In `/daily-note`, when `transcribe` errors out, retry with `swift-scribe` to the same `.out/{date}/{mtime}_{basename}.txt` path instead of stopping.
