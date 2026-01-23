#!/usr/bin/env -S uv run python
"""CLI entry point for GPT-4o based transcribe-diarize."""

import argparse
from pathlib import Path

from thds.core import source
from thds.mops import pure

from transcribe.config import load_config
from transcribe.diarize.format import format_diarized_transcripts
from transcribe.diarize.label import extract_speakers
from transcribe.diarize.transcribe import transcribe_chunks_diarized
from transcribe.split import split_audio_on_silences
from transcribe.workdir import derive_workdir, workdir

pure.magic.blob_root(Path(__file__).parent.parent.parent)

split = pure.magic()(split_audio_on_silences)
transcribe_diarized = pure.magic()(transcribe_chunks_diarized)
format_transcripts = pure.magic()(format_diarized_transcripts)


def main(input_file: Path) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    workdir.set_global(derive_workdir(input_file, kind="transcribe-gpt-diarize"))
    workdir().mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    # Split audio into chunks on silences
    print("Splitting audio on silences...")
    chunks = split(source.from_file(input_file))
    print(f"Split into {len(chunks)} chunks")

    # Transcribe chunks with GPT-4o diarization (per-chunk speaker labels)
    print("Transcribing with diarization...")
    transcripts = transcribe_diarized(chunks, config)

    # Format transcript (merge same-speaker segments, add paragraph breaks)
    print("Formatting transcript...")
    output = format_transcripts(transcripts)

    # Write speakers list for labeling
    speakers = extract_speakers(transcript=output.path().read_text(encoding="utf-8"))
    speakers_toml = workdir() / "speakers.toml"
    speakers_toml.write_text("\n".join(f"# {s}" for s in speakers) + "\n", encoding="utf-8")
    print(f"Wrote: {speakers_toml} ({len(speakers)} speakers)")

    print(f"\nDone. Output: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="transcribe-diarize-gpt",
        description="Transcribe audio with GPT-4o speaker diarization.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    args = parser.parse_args()

    main(input_file=args.input)
