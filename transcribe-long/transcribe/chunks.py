#!/usr/bin/env -S uv run python
import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from litellm import transcription

from transcribe.config import TranscribeConfig, load_config


@dataclass(frozen=True)
class Job:
    index: int
    chunk_path: Path
    out_json: Path


@dataclass
class ChunkTranscript:
    index: int
    text: str
    chunk_filename: str


def _extract_text(resp: object) -> str:
    """Extract text from a litellm transcription response."""
    if hasattr(resp, "text") and isinstance(resp.text, str):
        return resp.text
    if hasattr(resp, "model_dump"):
        data = resp.model_dump()
        if isinstance(data, dict) and "text" in data:
            return str(data["text"])
    return ""


def _extract_index_from_filename(filename: str) -> int:
    """Extract chunk index from filename like 'chunk_001.m4a' -> 1."""
    match = re.search(r"chunk_(\d+)", filename)
    return int(match.group(1)) if match else 0


def transcribe_one(job: Job, model: str) -> None:
    job.out_json.parent.mkdir(parents=True, exist_ok=True)

    with job.chunk_path.open("rb") as f:
        file_param = (job.chunk_path.name, f, "audio/mp4")
        resp = transcription(model=model, file=file_param)

    transcript = ChunkTranscript(
        index=job.index,
        text=_extract_text(resp),
        chunk_filename=job.chunk_path.name,
    )
    job.out_json.write_text(json.dumps(asdict(transcript), ensure_ascii=False, indent=2), encoding="utf-8")


def main(
    workdir: Path,
    config: TranscribeConfig | None = None,
) -> None:
    if config is None:
        config = load_config(workdir=workdir)
    chunks_dir = workdir / "chunks"
    out_dir = workdir / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = sorted(chunks_dir.glob("chunk_*.m4a"))
    if not chunks:
        raise SystemExit(f"No chunks found in {chunks_dir}")

    jobs = [
        Job(
            index=_extract_index_from_filename(p.name),
            chunk_path=p,
            out_json=out_dir / (p.stem + ".json"),
        )
        for p in chunks
    ]

    failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=config.transcription_jobs) as ex:
        futs = {ex.submit(transcribe_one, j, config.transcription_model): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                fut.result()
                print(f"ok  {j.chunk_path.name}")
            except Exception as e:
                failures.append((j.chunk_path, str(e)))
                print(f"ERR {j.chunk_path.name}: {e}")

    if failures:
        print("\nSome chunks failed:")
        for p, msg in failures:
            print(f"  {p.name}: {msg}")
        raise SystemExit(2)

    print(f"\nWrote transcripts to: {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", help="Work directory created by audio:split")
    ap.add_argument("--model", help="Transcription model (overrides config)")
    ap.add_argument("--jobs", type=int, help="Number of parallel jobs (overrides config)")
    args = ap.parse_args()

    config = load_config(workdir=Path(args.workdir))
    if args.model:
        config.transcription_model = args.model
    if args.jobs:
        config.transcription_jobs = args.jobs

    main(workdir=Path(args.workdir), config=config)
