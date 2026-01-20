"""Stitch transcripts with speaker labels from diarization."""

from pathlib import Path

from transcribe.diarize.types import SpeakerSegment, TimedTranscript


def _find_speaker_at_time(segments: list[SpeakerSegment], time: float) -> str | None:
    """Find which speaker is active at a given timestamp."""
    for seg in segments:
        if seg.start <= time <= seg.end:
            return seg.speaker
    return None


def _assign_speakers_to_words(
    transcript: TimedTranscript,
    segments: list[SpeakerSegment],
) -> list[tuple[str, str | None]]:
    """Assign speaker labels to each word based on timestamp alignment."""
    result: list[tuple[str, str | None]] = []
    for word in transcript.words:
        # Convert chunk-relative timestamp to absolute
        abs_time = transcript.chunk_start_time + word.start
        speaker = _find_speaker_at_time(segments, abs_time)
        result.append((word.word, speaker))
    return result


def stitch_with_speakers(
    transcripts: list[TimedTranscript],
    segments: list[SpeakerSegment],
    workdir: Path,
) -> Path:
    """
    Stitch transcripts together with speaker labels.

    Groups consecutive words by speaker and formats output as:
    SPEAKER_00: Hello, how are you?
    SPEAKER_01: I'm doing well, thanks.
    """
    transcripts = sorted(transcripts, key=lambda t: t.index)

    lines: list[str] = []
    current_speaker: str | None = None
    current_words: list[str] = []

    def flush():
        nonlocal current_speaker, current_words
        if current_words:
            speaker_label = current_speaker or "UNKNOWN"
            text = " ".join(current_words)
            lines.append(f"{speaker_label}: {text}")
            current_words = []

    for transcript in transcripts:
        words_with_speakers = _assign_speakers_to_words(transcript, segments)
        for word, speaker in words_with_speakers:
            if speaker != current_speaker:
                flush()
                current_speaker = speaker
            current_words.append(word)

    flush()  # Don't forget the last segment

    out_txt = workdir / "transcript.txt"
    out_txt.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote: {out_txt}")

    return out_txt
