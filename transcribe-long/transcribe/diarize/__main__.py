#!/usr/bin/env -S uv run python
"""CLI entry point for transcribe-diarize."""

import argparse
from pathlib import Path

from thds.mops import pure

from transcribe.config import load_config
from transcribe.diarize.core import diarize_audio
from transcribe.diarize.refine import refine_transcript
from transcribe.diarize.stitch import stitch_with_speakers
from transcribe.diarize.transcribe import transcribe_chunks_with_timestamps
from transcribe.split import extract_audio, split_audio_on_silences
from transcribe.workdir import derive_workdir

pure.magic.blob_root(Path(__file__).parent.parent.parent)

split = pure.magic()(split_audio_on_silences)
diarize = pure.magic()(diarize_audio)
transcribe = pure.magic()(transcribe_chunks_with_timestamps)
stitch = pure.magic()(stitch_with_speakers)
refine = pure.magic()(refine_transcript)


def main(input_file: Path, workdir: Path | None = None) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not workdir:
        workdir = derive_workdir(input_file, ".transcribe-diarize")

    workdir.mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    audio_file = extract_audio(input_file, workdir)

    # Run diarization on full audio (can run in parallel with split)
    print("Running speaker diarization...")
    segments = diarize(audio_file)
    print(f"Found {len(set(s.speaker for s in segments))} speakers")

    # Split audio into chunks
    chunks = split(input_file, workdir)

    # Transcribe with timestamps
    transcripts = transcribe(chunks, workdir, config=config)

    # Stitch with speaker labels
    raw_transcript = stitch(transcripts, segments, workdir)

    # Refine with LLM (assign unknown speakers, add punctuation)
    print("Refining transcript with LLM...")
    refined = refine(raw_transcript, workdir, model=config.reformat_model)

    print(f"\nDone. Output in: {workdir}")
    print(f"  transcript.txt (raw): {raw_transcript}")
    print(f"  transcript.refined.txt: {refined}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="transcribe-diarize",
        description="Transcribe audio with speaker diarization.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    parser.add_argument(
        "--workdir",
        "-w",
        help="Working directory (default: .transcribe-diarize/<input_stem>/<sha256>)",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    main(input_file=args.input, workdir=args.workdir)
