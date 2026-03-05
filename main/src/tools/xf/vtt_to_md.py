"""Reformat a WebVTT transcript into readable markdown.

Parses speaker-tagged VTT segments, sorts by timestamp, merges consecutive
same-speaker blocks, and writes `{speaker}: {text}` markdown.

See `fmt_vtt_to_md` for programmatic use, or run as CLI:

    uv run python -m thds.support.reformat_vtt input.vtt output.md
"""

import argparse
import re
import typing as ty
from pathlib import Path


class _Segment(ty.NamedTuple):
    start: str
    end: str
    speaker: str
    text: str


_VOICE_RE = re.compile(r"<v\s+(?P<speaker>[^>]+)>(?P<text>.*?)</v>", re.DOTALL)
_TIMESTAMP_RE = re.compile(r"(?P<start>\d{2}:\d{2}:\d{2}\.\d+)\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2}\.\d+)")


def _parse_segments(vtt_content: str) -> list[_Segment]:
    segments = [
        _Segment(
            ts_match["start"],
            ts_match["end"],
            voice_match["speaker"],
            voice_match["text"].replace("\n", " ").strip(),
        )
        for block in vtt_content.split("\n\n")
        if (ts_match := _TIMESTAMP_RE.search(block)) and (voice_match := _VOICE_RE.search(block))
    ]
    return sorted(segments, key=lambda s: s.start)


def _merge_consecutive(segments: ty.Sequence[_Segment]) -> list[tuple[str, str]]:
    if not segments:
        return []
    merged: list[tuple[str, str]] = []
    current_speaker = segments[0].speaker
    current_texts = [segments[0].text]
    for seg in segments[1:]:
        if seg.speaker == current_speaker:
            current_texts.append(seg.text)
        else:
            merged.append((current_speaker, " ".join(current_texts)))
            current_speaker = seg.speaker
            current_texts = [seg.text]
    merged.append((current_speaker, " ".join(current_texts)))
    return merged


def fmt_vtt_to_md(input_vtt: Path, output_md: Path) -> Path:
    segments = _parse_segments(input_vtt.read_text())
    merged = _merge_consecutive(segments)
    lines = [f"**{speaker}**: {text}\n" for speaker, text in merged]
    output_md.write_text("\n".join(lines))
    return output_md


def cli() -> None:
    parser = argparse.ArgumentParser(description="Reformat VTT transcript to markdown")
    parser.add_argument("input_vtt", type=Path)
    parser.add_argument("output_md", type=Path)
    args = parser.parse_args()
    result = fmt_vtt_to_md(args.input_vtt, args.output_md)
    print(f"wrote {result}")


if __name__ == "__main__":
    cli()
