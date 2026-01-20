#!/usr/bin/env python
"""Main CLI entry point for transcribe-long."""

import argparse
from pathlib import Path

from thds.core import hashing
from thds.mops import pure

from transcribe.config import load_config
from transcribe.split import split_audio_on_silences
from transcribe.stitch_transcripts import stitch_transcripts as stitch_transcripts
from transcribe.transcribe_chunks import transcribe_chunks

pure.magic.blob_root(Path(__file__).parent.parent)

split = pure.magic()(split_audio_on_silences)
transcribe = pure.magic()(transcribe_chunks)
stitch = pure.magic()(stitch_transcripts)


def _workdir(input_file: Path) -> Path:
    dirname = input_file.stem.replace(" ", "-")
    sha256 = str(hashing.file("sha256", input_file), encoding="utf-8")
    workdir = Path(f".transcribe/{dirname}/{sha256}")
    return workdir


def main(input_file: Path, workdir: Path | None = None) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not workdir:
        workdir = _workdir(input_file)

    workdir.mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    # Run pipeline steps (decorator handles caching)
    chunks = split(input_file, workdir)
    chunk_transcripts = transcribe(chunks, workdir, config=config)
    final = stitch(chunk_transcripts, workdir, config=config)

    print(f"\nDone. Output in: {workdir}")
    print(f"  transcript.txt: {final}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Transcribe large audio files by splitting, transcribing chunks, and stitching.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    parser.add_argument(
        "--workdir",
        "-w",
        help="Working directory (default: .transcribe/<input_stem>)",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    main(input_file=args.input, workdir=args.workdir)
