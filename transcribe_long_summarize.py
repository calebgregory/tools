#!/usr/bin/env python3
"""Pipeline that transcribes audio using transcribe-long (because chunking is
necessary to get a good transcript), then summarizes transcript with
confident-confidant."""

import argparse
import shutil
import typing as ty
from pathlib import Path

from cc import summarize_transcript

from transcribe import transcribe_audio_file


class Output(ty.NamedTuple):
    transcript: Path
    summary: Path


def transcribe_and_summarize(input_file: Path) -> Output:
    """Transcribe an audio file and summarize the resulting transcript.

    Args:
        input_file: Path to the audio file to process

    Returns:
        Tuple of (transcript_path, summary_path) - both as peers of the input file
    """
    input_file = input_file.resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Step 1: Transcribe using transcribe-long
    print(f"Transcribing: {input_file}")
    transcript_path = transcribe_audio_file(input_file)

    # Step 2: Copy transcript to be a peer of input file
    transcript_output_path = input_file.parent / f"{input_file.stem}.transcript.md"
    shutil.copy2(transcript_path, transcript_output_path)
    print(f"Transcript copied to: {transcript_output_path}")

    # Step 3 & 4: Summarize using confident-confidant, writing directly to peer of input file
    summary_output_path = input_file.parent / f"{input_file.stem}.transcript-summarized.md"
    print(f"Summarizing: {transcript_output_path}")
    summarize_transcript(transcript_output_path, output_path=summary_output_path)
    print(f"Summary written to: {summary_output_path}")

    return Output(transcript_output_path, summary_output_path)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe audio files and summarize the transcript.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    args = parser.parse_args()

    transcript_path, summary_path = transcribe_and_summarize(args.input)
    print("\nDone!")
    print(f"  Transcript: {transcript_path}")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    cli()
