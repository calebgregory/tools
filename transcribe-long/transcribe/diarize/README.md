# transcribe-diarize

Speaker diarization support for transcribe-long. Identifies who is speaking and labels the transcript accordingly.

## Installation

```bash
# Install with diarization support
uv pip install -e ".[diarize]"
```

This installs [pyannote.audio](https://github.com/pyannote/pyannote-audio) which requires PyTorch.

## Setup

1. Accept the pyannote model license at https://huggingface.co/pyannote/speaker-diarization-3.1
2. Set your HuggingFace token:

```bash
export HF_TOKEN=your_huggingface_token
```

## Usage

```bash
transcribe-diarize input.mp4
```

Options:

```bash
transcribe-diarize input.mp4 --workdir ./my-workdir
```

## Output

```
SPEAKER_00: Hello, how are you today?

SPEAKER_01: I'm doing well, thanks for asking. How about yourself?

SPEAKER_00: Pretty good. I wanted to talk about the project.
```

## How it works

1. **Diarize** - pyannote.audio analyzes the full audio to identify speaker segments
2. **Split** - Audio is split on silence into chunks (same as regular transcribe)
3. **Transcribe** - Each chunk is transcribed with word-level timestamps
4. **Stitch** - Words are aligned to speaker segments using timestamps

This approach solves the problem of speaker labels being inconsistent across chunks - diarization runs on the full audio first, giving consistent global speaker IDs.

## Configuration

Uses the same `transcribe.toml` config as the main transcribe command. See the main README for details.
