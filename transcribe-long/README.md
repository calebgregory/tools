# transcribe-long

Transcribe large audio files using OpenAI's transcription API by splitting on silence, transcribing chunks in parallel, and stitching the results back together.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- ffmpeg
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
transcribe input.mp4
```

The pipeline is idempotent and memoizing - re-running the same command will skip already-completed steps.

## Output

After running, the working directory contains:

- `audio.m4a` - Extracted audio track
- `chunks/` - Split audio files
- `transcripts/` - Individual chunk transcripts (JSON)
- `transcript.raw.txt` - Stitched transcript (unformatted)
- `transcript.txt` - Final transcript (reformatted with proper paragraphs)

## Configuration

Create `transcribe.toml` next to your input file:

```toml
transcription_model = "gpt-4o-transcribe"
reformat_model = "gpt-4o"
```

## Speaker Diarization

For multi-speaker audio, see [transcribe/diarize/README.md](transcribe/diarize/README.md) for speaker identification support.
