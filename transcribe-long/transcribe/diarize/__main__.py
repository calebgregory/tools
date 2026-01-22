#!/usr/bin/env -S uv run python
"""CLI entry point for GPT-4o based transcribe-diarize."""

import argparse
from pathlib import Path

from thds.core import source
from thds.mops import pure

from transcribe.config import load_config
from transcribe.gpt_diarize.stitch import stitch_diarized_chunks
from transcribe.gpt_diarize.transcribe import transcribe_chunks_diarized
from transcribe.split import split_audio_on_silences
from transcribe.workdir import derive_workdir, workdir

pure.magic.blob_root(Path(__file__).parent.parent.parent)

split = pure.magic()(split_audio_on_silences)
transcribe_diarized = pure.magic()(transcribe_chunks_diarized)
stitch = pure.magic()(stitch_diarized_chunks)


def main(input_file: Path) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    workdir.set_global(derive_workdir(input_file, kind="transcribe-gpt-diarize"))
    workdir().mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    # Split audio into chunks on silences
    print("Splitting audio on silences...")
    chunks = split(source.from_file(input_file), every=300.0, window=60.0)  # 5min chunks, 60s window
    print(f"Split into {len(chunks)} chunks")

    # Transcribe chunks with GPT-4o diarization (per-chunk speaker labels)
    print("Transcribing with diarization...")
    transcripts = transcribe_diarized(chunks, config)

    # Stitch with LLM (merge split sentences, add punctuation)
    print("Stitching transcript...")
    output = stitch(transcripts, config)

    print(f"\nDone. Output: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="transcribe-diarize-gpt",
        description="Transcribe audio with GPT-4o speaker diarization.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    args = parser.parse_args()

    main(input_file=args.input)
