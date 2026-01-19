#!/usr/bin/env -S uv run python
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from litellm import transcription  # per LiteLLM docs :contentReference[oaicite:3]{index=3}


@dataclass(frozen=True)
class Job:
    chunk_path: Path
    out_json: Path


def _to_jsonable(resp: Any) -> Any:
    # LiteLLM responses vary by version/provider; handle common shapes.
    if hasattr(resp, "model_dump"):
        return resp.model_dump()
    if hasattr(resp, "dict"):
        return resp.dict()
    if isinstance(resp, (dict, list, str, int, float, bool)) or resp is None:
        return resp
    # last resort:
    return {"repr": repr(resp)}


def transcribe_one(job: Job, model: str) -> None:
    job.out_json.parent.mkdir(parents=True, exist_ok=True)

    with job.chunk_path.open("rb") as f:
        # If your LiteLLM install supports filename+content_type tuples, this is the safest:
        file_param = (job.chunk_path.name, f, "audio/mp4")
        resp = transcription(model=model, file=file_param)

    job.out_json.write_text(json.dumps(_to_jsonable(resp), ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", help="Work directory created by audio:split")
    ap.add_argument("--model", default=os.environ.get("TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize"))
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("TRANSCRIBE_JOBS", "2")))
    args = ap.parse_args()

    workdir = Path(args.workdir)
    chunks_dir = workdir / "chunks"
    out_dir = workdir / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = sorted(chunks_dir.glob("chunk_*.m4a"))
    if not chunks:
        raise SystemExit(f"No chunks found in {chunks_dir}")

    jobs = [Job(chunk_path=p, out_json=out_dir / (p.stem + ".json")) for p in chunks]

    failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(transcribe_one, j, args.model): j for j in jobs}
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
    main()
