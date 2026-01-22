#!/usr/bin/env -S uv run python
import json
import typing as ty
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from litellm import transcription
from thds.core.source import Source

from transcribe.config import TranscribeConfig
from transcribe.split import Chunk
from transcribe.workdir import workdir


@dataclass(frozen=True)
class _Job:
    index: int
    chunk_path: Path
    out_json: Path


@dataclass
class ChunkTranscript:
    index: int
    text: str
    chunk_file: Source


class _TranscriptionError(Exception):
    def __init__(self, file: Path, exception: Exception):
        self.file = file
        self.exception = exception


def _extract_text(resp: object) -> str:
    """Extract text from a litellm transcription response."""
    if hasattr(resp, "text") and isinstance(resp.text, str):
        return resp.text
    if hasattr(resp, "model_dump"):
        data = resp.model_dump()
        if isinstance(data, dict) and "text" in data:
            return str(data["text"])
    return ""


def _transcribe_one(job: _Job, model: str) -> ChunkTranscript:
    job.out_json.parent.mkdir(parents=True, exist_ok=True)

    with job.chunk_path.open("rb") as f:
        file_param = (job.chunk_path.name, f, "audio/mp4")
        resp = transcription(model=model, file=file_param)

    transcript = ChunkTranscript(
        index=job.index,
        text=_extract_text(resp),
        chunk_file=Source.from_file(job.chunk_path),
    )

    # maybe useful
    job.out_json.write_text(json.dumps(asdict(transcript), ensure_ascii=False, indent=2), encoding="utf-8")

    return transcript


def transcribe_chunks(chunks: ty.Iterable[Chunk], config: TranscribeConfig) -> list[ChunkTranscript]:
    out_dir = workdir() / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = sorted(chunks, key=lambda c: c.index)

    jobs = [
        _Job(index=c.index, chunk_path=c.file.path(), out_json=out_dir / (c.file.path().stem + ".json"))
        for c in chunks
    ]

    print(f"transcribing {len(chunks)} chunks...")
    successes: list[ChunkTranscript] = []
    failures: list[_TranscriptionError] = []
    with ThreadPoolExecutor(max_workers=config.transcription_jobs) as ex:
        futs = {ex.submit(_transcribe_one, j, config.transcription_model): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                successes.append(fut.result())
                print(f"ok  {j.chunk_path.name}")
            except Exception as e:
                failures.append(_TranscriptionError(j.chunk_path, e))

    if failures:
        raise ExceptionGroup("Transcribing some chunks failed", failures)

    return successes
