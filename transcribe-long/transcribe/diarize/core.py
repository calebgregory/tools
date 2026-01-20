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
        use_auth_token=hf_token,
    )

    # Run diarization
    diarization = pipeline(str(audio_file))

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
