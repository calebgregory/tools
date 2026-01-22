"""Transcription with word-level timestamps for diarization."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from litellm import transcription

from transcribe.config import TranscribeConfig
from transcribe.diarize.types import TimedTranscript, WordTimestamp
from transcribe.split import Chunk


def _extract_words(resp: object) -> list[WordTimestamp]:
    """Extract word timestamps from a litellm transcription response."""
    # litellm returns an object with model_dump() for verbose responses
    if hasattr(resp, "model_dump"):
        data = resp.model_dump()
    elif hasattr(resp, "__dict__"):
        data = resp.__dict__
    else:
        data = {}

    words_data = data.get("words", [])
    return [
        WordTimestamp(
            word=w.get("word", ""),
            start=w.get("start", 0.0),
            end=w.get("end", 0.0),
        )
        for w in words_data
    ]


def _transcribe_chunk_with_timestamps(chunk: Chunk, model: str, out_dir: Path) -> TimedTranscript:
    """Transcribe a single chunk with word-level timestamps."""
    with chunk.file.open("rb") as f:
        file_param = (chunk.file.name, f, "audio/mp4")
        # whisper-1 is required for verbose_json with word-level timestamps
        # gpt-4o-transcribe doesn't support this format
        resp = transcription(
            model="whisper-1",
            file=file_param,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = _extract_words(resp)

    transcript = TimedTranscript(
        index=chunk.index,
        chunk_filename=chunk.file.name,
        chunk_start_time=chunk.start_time,
        words=words,
    )

    # Save to file for debugging/caching
    out_json = out_dir / f"{chunk.file.stem}.json"
    out_json.write_text(
        json.dumps(asdict(transcript), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return transcript


class _TranscriptionError(Exception):
    def __init__(self, file: Path, exception: Exception):
        self.file = file
        self.exception = exception


def transcribe_chunks_with_timestamps(
    chunks: list[Chunk], workdir: Path, config: TranscribeConfig
) -> list[TimedTranscript]:
    """Transcribe chunks with word-level timestamps for speaker alignment."""
    out_dir = workdir / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = sorted(chunks, key=lambda c: c.index)

    print(f"Transcribing {len(chunks)} chunks with timestamps...")
    successes: list[TimedTranscript] = []
    failures: list[_TranscriptionError] = []

    with ThreadPoolExecutor(max_workers=config.transcription_jobs) as ex:
        futs = {
            ex.submit(_transcribe_chunk_with_timestamps, c, config.transcription_model, out_dir): c
            for c in chunks
        }
        for fut in as_completed(futs):
            chunk = futs[fut]
            try:
                successes.append(fut.result())
                print(f"ok  {chunk.file.name}")
            except Exception as e:
                failures.append(_TranscriptionError(chunk.file, e))
                print(f"ERR {chunk.file.name}: {e}")

    if failures:
        raise ExceptionGroup("Transcribing some chunks failed", [f.exception for f in failures])

    return successes
