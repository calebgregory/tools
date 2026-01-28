#!/usr/bin/env -S uv run python
import json
import logging
import typing as ty
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from openai import OpenAI
from thds.core.source import Source

from transcribe.config import TranscribeConfig
from transcribe.split import Chunk
from transcribe.workdir import workdir

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Job:
    index: int
    chunk_path: Path
    out_json: Path


@dataclass(frozen=True)
class ChunkTranscript:
    index: int
    text: str
    chunk_file: Source


class _TranscriptionError(Exception):
    def __init__(self, file: Path, exception: Exception):
        self.file = file
        # Store as string to ensure picklability (raw exceptions may contain unpicklable state)
        self.exception = f"{type(exception).__name__}: {exception}"


def _transcribe_one(job: _Job, model: str) -> ChunkTranscript:
    job.out_json.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    with job.chunk_path.open("rb") as f:
        resp = client.audio.transcriptions.create(model=model, file=f)

    transcript = ChunkTranscript(
        index=job.index,
        text=resp.text,
        chunk_file=Source.from_file(job.chunk_path),
    )

    # maybe useful
    job.out_json.write_text(
        json.dumps(asdict(transcript), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

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
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(_transcribe_one, j, config.transcription_model): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                successes.append(fut.result())
                print(f"ok  {j.chunk_path.name}")
            except Exception as e:
                logger.error(f"Error raised for job {j.index}", exc_info=e)
                failures.append(_TranscriptionError(j.chunk_path, e))

    if failures:
        raise ExceptionGroup("Transcribing some chunks failed", failures)

    return successes
