# Diarize Pipeline

Transcribe audio with speaker diarization using GPT-4o, then label speakers with human-readable names.

## Workflow

### 1. Transcribe with diarization

```bash
transcribe-diarize path/to/audio.m4a
```

This outputs to `.out/transcribe-gpt-diarize/<filename>/`:
- `transcript.txt` - formatted transcript with speaker labels like `CHUNK_0_A`, `CHUNK_1_B`
- `speakers.toml` - template file listing all distinct speakers (commented out)

### 2. Review and label speakers

Open `transcript.txt` and identify who each speaker is. Then edit `speakers.toml` to map chunk speakers to names:

```toml
# Before (auto-generated):
# CHUNK_0_A
# CHUNK_0_B
# CHUNK_1_A

# After (you fill in):
Caleb = ["CHUNK_0_A", "CHUNK_1_A"]
Andrew = ["CHUNK_0_B"]
```

Multiple chunk speakers can map to the same person (speakers are identified per-chunk, so the same person may be `CHUNK_0_A` in one chunk and `CHUNK_1_B` in another).

### 3. Apply labels

```bash
transcribe-label transcript.txt speakers.toml
```

This outputs `transcript.labeled.txt` with:
- Speaker labels replaced (`CHUNK_0_A` -> `Caleb`)
- Consecutive same-speaker blocks merged

## Commands

| Command | Description |
|---------|-------------|
| `transcribe-diarize <audio>` | Transcribe with diarization |
| `transcribe-label <transcript> <labels.toml>` | Apply speaker labels |
| `transcribe-label --speakers <transcript>` | List distinct speakers in a transcript |

## Example

```bash
# 1. Transcribe
transcribe-diarize meeting.m4a

# 2. Edit speakers.toml in the output directory
vim .out/transcribe-gpt-diarize/meeting/*/speakers.toml

# 3. Apply labels
transcribe-label \
  .out/transcribe-gpt-diarize/meeting/*/transcript.txt \
  .out/transcribe-gpt-diarize/meeting/*/speakers.toml

# 4. View result
cat .out/transcribe-gpt-diarize/meeting/*/transcript.labeled.txt
```
