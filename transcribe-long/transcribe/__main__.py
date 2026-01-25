"""Main CLI entry point for transcribe-long."""

import argparse
from pathlib import Path

from thds.core import source
from thds.mops import pure

from transcribe.config import load_config
from transcribe.split import split_audio_on_silences
from transcribe.stitch_transcripts import stitch_transcripts as stitch_transcripts
from transcribe.transcribe_chunks import transcribe_chunks
from transcribe.workdir import derive_workdir, workdir

pure.magic.blob_root(Path(__file__).parent.parent)

split = pure.magic()(split_audio_on_silences)
transcribe = pure.magic()(transcribe_chunks)
stitch = pure.magic()(stitch_transcripts)


def main(input_file: Path) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    workdir.set_global(derive_workdir(input_file, "transcribe"))
    workdir().mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    # Run pipeline steps (decorator handles caching)
    chunks = split(source.from_file(input_file), every=config.split_every_s)
    chunk_transcripts = transcribe(chunks, config=config)
    final = stitch(chunk_transcripts, config=config)

    print(f"\nDone. Output in: {workdir()}")
    print(f"  transcript.txt: {final}")


def cli() -> None:
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Transcribe large audio files by splitting, transcribing chunks, and stitching.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    args = parser.parse_args()
    main(input_file=args.input)


if __name__ == "__main__":
    cli()
