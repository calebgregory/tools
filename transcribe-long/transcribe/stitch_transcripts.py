#!/usr/bin/env -S uv run python
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from litellm import completion

from transcribe.chunks import ChunkTranscript
from transcribe.config import TranscribeConfig, load_config

REFORMAT_SYSTEM_PROMPT = """\
You are a transcript editor. The user will provide a transcript that has been \
stitched together from multiple audio fragments. Because of this fragmentation, \
some sentences may have incorrect capitalization or punctuation at the boundaries \
where fragments were joined.

Your task:
1. Correct any capitalization errors (e.g., lowercase letter at the start of a sentence)
2. Correct any punctuation errors (e.g., missing periods, incorrect comma placement at boundaries)
3. Add paragraph breaks where natural topic or speaker changes occur

CRITICAL RULES:
- You may ONLY change whitespace (spaces, newlines) and capitalization/punctuation
- Do NOT change any words, add words, remove words, or rephrase anything
- Do NOT add any commentary, headers, or formatting beyond paragraph breaks
- Return ONLY the corrected transcript text, nothing else
"""


def reformat_transcript(text: str, model: str) -> str:
    """
    Send the stitched transcript to an LLM to fix capitalization/punctuation
    and add paragraph breaks.
    """
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": REFORMAT_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content
    return content.strip() if content else text


def load_transcript(path: Path) -> ChunkTranscript:
    """Load a ChunkTranscript from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return ChunkTranscript(**data)


def main(
    workdir: Path,
    config: TranscribeConfig | None = None,
    skip_reformat: bool = False,
) -> None:
    if config is None:
        config = load_config(workdir=workdir)

    transcripts_dir = workdir / "transcripts"
    files = sorted(transcripts_dir.glob("chunk_*.json"))
    if not files:
        raise SystemExit(f"No transcripts found in {transcripts_dir}")

    transcripts = [load_transcript(f) for f in files]
    transcripts.sort(key=lambda t: t.index)

    out_jsonl = workdir / "transcript.jsonl"
    out_raw = workdir / "transcript.raw.txt"
    out_txt = workdir / "transcript.txt"

    txt_parts: list[str] = []

    with out_jsonl.open("w", encoding="utf-8") as w:
        for t in transcripts:
            w.write(json.dumps(asdict(t), ensure_ascii=False) + "\n")
            if t.text:
                txt_parts.append(t.text.strip())

    print(f"Wrote: {out_jsonl}")

    if not txt_parts:
        print("No text found in transcripts.")
        return

    raw_text = "\n\n".join(txt_parts)
    out_raw.write_text(raw_text + "\n", encoding="utf-8")
    print(f"Wrote: {out_raw}")

    if skip_reformat:
        out_txt.write_text(raw_text + "\n", encoding="utf-8")
        print(f"Wrote: {out_txt} (reformat skipped)")
    else:
        print(f"Reformatting with {config.reformat_model}...")
        reformatted = reformat_transcript(raw_text, config.reformat_model)
        out_txt.write_text(reformatted + "\n", encoding="utf-8")
        print(f"Wrote: {out_txt}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--skip-reformat", action="store_true", help="Skip the LLM reformat step")
    ap.add_argument("--reformat-model", help="Model to use for reformatting (overrides config)")
    args = ap.parse_args()

    config = load_config(workdir=Path(args.workdir))
    if args.reformat_model:
        config.reformat_model = args.reformat_model

    main(
        workdir=Path(args.workdir),
        config=config,
        skip_reformat=args.skip_reformat,
    )
