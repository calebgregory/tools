"""Main CLI entry point for transcribe-long."""

import argparse
from pathlib import Path

from thds.core import source
from thds.mops import pure

from transcribe.config import load_config
from transcribe.llm.stitch_transcripts import stitch_transcripts
from transcribe.llm.transcribe_chunks import transcribe_chunks
from transcribe.split import split_audio_on_silences
from transcribe.workdir import derive_workdir, workdir

pure.magic.blob_root(Path(__file__).parent.parent)
pure.magic.pipeline_id("transcribe")

_split_audio_on_silences = pure.magic()(split_audio_on_silences)
_transcribe_chunks = pure.magic()(transcribe_chunks)
_stitch_transcripts = pure.magic()(stitch_transcripts)


def transcribe_audio_file(input_file: Path) -> Path:
    """Transcribe an audio file, returning the path to the final transcript.

    Args:
        input_file: Path to the audio file to transcribe

    Returns:
        Path to the generated transcript file
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    workdir.set_global(derive_workdir(input_file, "transcribe"))
    workdir().mkdir(parents=True, exist_ok=True)

    config = load_config(input_path=input_file)

    # Run pipeline steps (decorator handles caching)
    chunks = _split_audio_on_silences(source.from_file(input_file), every=config.split_audio_approx_every_s)
    chunk_transcripts = _transcribe_chunks(chunks, config=config)
    final = _stitch_transcripts(chunk_transcripts, config=config)

    print(f"\nDone. Output in: {workdir()}")
    print(f"  transcript.txt: {final}")

    return final.path()


def cli() -> None:
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Transcribe large audio files by splitting, transcribing chunks, and stitching.",
    )
    parser.add_argument("input", help="Input audio/video file", type=Path)
    args = parser.parse_args()
    transcribe_audio_file(input_file=args.input)


if __name__ == "__main__":
    cli()
