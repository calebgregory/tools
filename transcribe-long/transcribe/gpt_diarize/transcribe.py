"""Transcription with GPT-4o diarization model."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from openai import OpenAI

from transcribe.config import TranscribeConfig
from transcribe.gpt_diarize.types import DiarizedChunkTranscript, DiarizedSegment
from transcribe.split import Chunk
from transcribe.workdir import workdir


def _rename_speaker(original: str, chunk_index: int) -> str:
    """Rename speaker from A/B/C to CHUNK_{index}_A/B/C."""
    # OpenAI returns speakers as "A", "B", "C", etc.
    return f"CHUNK_{chunk_index}_{original}"


def _transcribe_chunk_diarized(chunk: Chunk, model: str, out_dir: Path) -> DiarizedChunkTranscript:
    """Transcribe a single chunk with GPT-4o diarization."""
    client = OpenAI()

    with open(chunk.file, "rb") as f:
        # Using OpenAI client directly instead of litellm because of
        # https://github.com/BerriAI/litellm/issues/18125
        # litellm doesn't properly pass chunking_strategy which is required for diarization
        response = client.audio.transcriptions.create(
            model=model,
            file=f,
            response_format="diarized_json",
            chunking_strategy="auto",  # Required for audio > 30s
        )

    # Parse response - diarized_json returns segments with speaker labels
    segments: list[DiarizedSegment] = []

    # The diarized_json response has 'segments' with speaker info
    for seg in response.segments:
        segments.append(
            DiarizedSegment(
                speaker=_rename_speaker(seg.speaker, chunk.index),
                text=seg.text.strip(),
                start=seg.start,
                end=seg.end,
            )
        )

    transcript = DiarizedChunkTranscript(
        index=chunk.index,
        chunk_file=chunk.file,
        segments=segments,
    )

    # Save to file for debugging/caching
    out_json = out_dir / f"chunk_{chunk.index:03d}_diarized.json"
    out_json.write_text(
        json.dumps(asdict(transcript), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    return transcript


class _TranscriptionError(Exception):
    def __init__(self, file: str, exception: Exception):
        self.file = file
        self.exception = exception


def transcribe_chunks_diarized(
    chunks: list[Chunk], config: TranscribeConfig
) -> list[DiarizedChunkTranscript]:
    """Transcribe chunks with GPT-4o diarization model."""
    out_dir = workdir() / "diarized_transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = sorted(chunks, key=lambda c: c.index)
    model = config.diarization_model

    print(f"Transcribing {len(chunks)} chunks with diarization using {model}...")
    successes: list[DiarizedChunkTranscript] = []
    failures: list[_TranscriptionError] = []

    with ThreadPoolExecutor(max_workers=config.transcription_jobs) as ex:
        futs = {ex.submit(_transcribe_chunk_diarized, c, model, out_dir): c for c in chunks}
        for fut in as_completed(futs):
            chunk = futs[fut]
            chunk_name = chunk.file.path().name
            try:
                successes.append(fut.result())
                print(f"ok  {chunk_name}")
            except Exception as e:
                failures.append(_TranscriptionError(chunk_name, e))
                print(f"ERR {chunk_name}: {e}")

    if failures:
        raise ExceptionGroup("Transcribing some chunks failed", [f.exception for f in failures])

    return sorted(successes, key=lambda t: t.index)
