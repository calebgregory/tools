"""Data types for diarization pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeakerSegment:
    """A segment of audio attributed to a speaker."""

    speaker: str  # e.g., "SPEAKER_00", "SPEAKER_01"
    start: float  # seconds
    end: float  # seconds


@dataclass(frozen=True)
class WordTimestamp:
    """A word with its timing relative to the chunk."""

    word: str
    start: float  # seconds, relative to chunk start
    end: float


@dataclass
class TimedTranscript:
    """Transcript with word-level timestamps."""

    index: int
    chunk_filename: str
    chunk_start_time: float  # absolute start time in original audio
    words: list[WordTimestamp]

    @property
    def text(self) -> str:
        return " ".join(w.word for w in self.words)
