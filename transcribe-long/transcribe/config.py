#!/usr/bin/env -S uv run python
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAME = "transcribe.toml"


@dataclass
class TranscribeConfig:
    transcription_model: str = "gpt-4o-transcribe"
    diarization_model: str = "gpt-4o-transcribe-diarize"
    reformat_model: str = "gpt-4o"
    split_audio_approx_every_s: int = 20 * 60  # 20 minutes

    @classmethod
    def from_dict(cls, data: dict) -> "TranscribeConfig":
        """Create config from a dictionary, ignoring unknown keys."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


def find_config_file(input_path: Path | None = None) -> Path | None:
    """
    Find a config file in order of precedence:
    1. Peer to input file (e.g., /path/to/audio.m4a -> /path/to/transcribe.toml)
    2. In current working directory

    Returns None if no config file is found.
    """
    candidates = [input_path.parent / CONFIG_FILENAME if input_path else None, Path.cwd() / CONFIG_FILENAME]

    for candidate in filter(None, candidates):
        if candidate.is_file():
            return candidate

    return None


def load_config(input_path: Path | None = None, config_path: Path | None = None) -> TranscribeConfig:
    """
    Load config from TOML file, with environment variable overrides.

    Priority (highest to lowest):
    1. Environment variables (TRANSCRIBE_MODEL, TRANSCRIBE_JOBS, REFORMAT_MODEL)
    2. Explicit config_path argument
    3. Auto-detected config file (peer to input, workdir, or cwd)
    4. Default values
    """
    config = TranscribeConfig()

    # Try to load from file
    if config_path is None:
        config_path = find_config_file(input_path)

    if config_path is not None and config_path.is_file():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        config = TranscribeConfig.from_dict(data)

    return config
