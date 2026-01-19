#!/usr/bin/env -S uv run python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def extract_text(obj: Any) -> str | None:
    # Try common fields; diarization may be nested differently by provider/version.
    if isinstance(obj, dict):
        for key in ("text", "transcript"):
            if key in obj and isinstance(obj[key], str):
                return obj[key]
        # Sometimes responses look like { "segments": [ ... ] }
        if "segments" in obj and isinstance(obj["segments"], list):
            parts = []
            for seg in obj["segments"]:
                if isinstance(seg, dict) and isinstance(seg.get("text"), str):
                    parts.append(seg["text"].strip())
            if parts:
                return "\n".join(parts)
    return None


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    transcripts_dir = workdir / "transcripts"
    files = sorted(transcripts_dir.glob("chunk_*.json"))
    if not files:
        raise SystemExit(f"No transcripts found in {transcripts_dir}")

    out_jsonl = workdir / "transcript.jsonl"
    out_txt = workdir / "transcript.txt"

    txt_parts: list[str] = []

    with out_jsonl.open("w", encoding="utf-8") as w:
        for f in files:
            obj = json.loads(f.read_text(encoding="utf-8"))
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")

            t = extract_text(obj)
            if t:
                txt_parts.append(t.strip())

    if txt_parts:
        out_txt.write_text("\n\n".join(txt_parts) + "\n", encoding="utf-8")
        print(f"Wrote: {out_txt}")
    else:
        print("No obvious text field found to write transcript.txt (JSONL still written).")

    print(f"Wrote: {out_jsonl}")


if __name__ == "__main__":
    main()
