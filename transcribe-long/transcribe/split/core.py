"""Audio splitting functionality using ffmpeg."""

import re
import subprocess
import typing as ty
from dataclasses import dataclass
from pathlib import Path

from transcribe.split.choose_silence_cuts import Cut, choose_cuts


@dataclass(frozen=True)
class Chunk:
    index: int
    file: Path


def _extract_audio(input_file: Path, workdir: Path) -> Path:
    """Extract audio track from input file to m4a format."""
    audio_file = workdir / "audio.m4a"
    if audio_file.exists():
        return audio_file

    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        f"ffmpeg -hide_banner -loglevel error -i {input_file} -vn -map 0:a:0 -c:a copy {audio_file}".split(),
        check=True,
    )
    return audio_file


def _detect_silence(audio_file: Path, workdir: Path) -> Path:
    """Run ffmpeg silencedetect and write log file."""
    log_file = workdir / "silence.log"

    workdir.mkdir(parents=True, exist_ok=True)

    # ffmpeg writes silencedetect output to stderr
    result = subprocess.run(
        f"ffmpeg -hide_banner -i {audio_file} -vn -af silencedetect=noise=-35dB:d=0.4 -f null -".split(),
        capture_output=True,
        text=True,
    )

    log_file.write_text(result.stderr, encoding="utf-8")
    print(f"Wrote: {log_file}")
    return log_file


def _extract_index_from_filename(filename: str) -> int:
    """Extract chunk index from filename like 'chunk_001.m4a' -> 1."""
    match = re.search(r"chunk_(\d+)", filename)
    return int(match.group(1)) if match else 0


def _fmt_float(x: float, digits: int) -> str:
    return f"{x:.{digits}f}".rstrip("0").rstrip(".")


def _fmt_cuts_for_ffmpeg(cuts: ty.Iterable[Cut]) -> str:
    return ",".join(_fmt_float(cut.chosen, digits=6) for cut in cuts)


def _split_on_silence(audio_file: Path, cuts: ty.Iterable[Cut], workdir: Path) -> list[Chunk]:
    """Split audio file at the specified cut points."""
    chunks_dir = workdir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    cuts_str = _fmt_cuts_for_ffmpeg(cuts)

    subprocess.run(
        f"ffmpeg -hide_banner -loglevel error -i {audio_file} -f segment -segment_times {cuts_str} -reset_timestamps 1 -c copy {chunks_dir}/chunk_%03d.m4a".split(),
        check=True,
    )

    print(f"Chunks in: {chunks_dir}")
    return [Chunk(index=_extract_index_from_filename(f.name), file=f) for f in chunks_dir.glob("*.m4a")]


def split_audio_on_silences(
    input_file: Path, workdir: Path, every: float = 1200.0, window: float = 90.0
) -> list[Chunk]:
    """Run the full split pipeline: extract audio, detect silence, choose cuts, split."""
    audio_file = _extract_audio(input_file, workdir)
    log_file = _detect_silence(audio_file, workdir)
    cuts = choose_cuts(silence_log_path=log_file, every=every, window=window)
    chunks = _split_on_silence(audio_file, cuts, workdir)
    return chunks
