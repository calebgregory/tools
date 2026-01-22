"""Speaker diarization using pyannote.audio."""

import os
from pathlib import Path

from pyannote.audio import Pipeline  # type: ignore[import-not-found]

from transcribe.diarize.types import SpeakerSegment


def diarize_audio(audio_file: Path) -> list[SpeakerSegment]:
    """
    Run speaker diarization on audio file using pyannote.audio.

    Requires HF_TOKEN environment variable or ~/.huggingface/token to be set.
    You must accept the model license at https://huggingface.co/pyannote/speaker-diarization-3.1
    """
    hf_token = os.environ.get("HF_TOKEN")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )

    # Run diarization
    result = pipeline(str(audio_file))

    # pyannote-audio v4 returns DiarizeOutput, v3 returned Annotation directly
    if hasattr(result, "speaker_diarization"):
        diarization = result.speaker_diarization
    else:
        diarization = result

    segments: list[SpeakerSegment] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            SpeakerSegment(
                speaker=speaker,
                start=turn.start,
                end=turn.end,
            )
        )

    return segments
