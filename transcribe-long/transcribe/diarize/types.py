"""Data types for GPT-4o diarization pipeline."""

from dataclasses import dataclass

from thds.core.source import Source


@dataclass(frozen=True)
class DiarizedSegment:
    """A segment of speech attributed to a speaker within a chunk."""

    speaker: str  # e.g., "CHUNK_0_A", "CHUNK_1_B"
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class DiarizedChunkTranscript:
    """Transcription result for a single chunk with diarization."""

    index: int
    chunk_file: Source  # Use Source instead of Path/str for memoization
    segments: list[DiarizedSegment]
