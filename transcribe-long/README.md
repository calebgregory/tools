# transcribe-long

Transcribe large audio files using OpenAI's transcription API by splitting on silence, transcribing chunks in parallel, and stitching the results back together.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- [mise](https://mise.jdx.dev/)
- ffmpeg
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

## Usage

```bash
# 1. Detect silence in audio file
mise run audio:split:detect-silence -- input.m4a workdir/

# 2. Split on silence (creates ~20min chunks)
mise run audio:split:split-on-silence -- input.m4a workdir/

# 3. Transcribe chunks in parallel
mise run audio:transcribe -- workdir/

# 4. Stitch transcripts and reformat
mise run audio:stitch -- workdir/
```

Or run all steps:

```bash
mise run audio:all -- input.m4a workdir/
```

## Output

After running, `workdir/` contains:

- `chunks/` - Split audio files
- `transcripts/` - Individual chunk transcripts (JSON)
- `transcript.raw.txt` - Stitched transcript (unformatted)
- `transcript.txt` - Final transcript (reformatted with proper paragraphs)
- `transcript.jsonl` - All chunks as JSON lines

## Configuration

Create `transcribe.toml` next to your input file or in the working directory:

```toml
transcription_model = "gpt-4o-transcribe"
transcription_jobs = 2
reformat_model = "gpt-4o"
```

Environment variables override config file values:

- `TRANSCRIBE_MODEL` - Model for transcription
- `TRANSCRIBE_JOBS` - Number of parallel transcription jobs
- `REFORMAT_MODEL` - Model for post-processing reformatting

## CLI Options

```bash
# Skip the LLM reformat step
mise run audio:stitch -- workdir/ --skip-reformat

# Override models via CLI
uv run transcribe/chunks.py workdir/ --model gpt-4o-transcribe --jobs 4
uv run transcribe/stitch_transcripts.py workdir/ --reformat-model gpt-4o-mini
```
