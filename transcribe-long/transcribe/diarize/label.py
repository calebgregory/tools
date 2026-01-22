#!/usr/bin/env -S uv run python
"""Replace CHUNK_N_X speaker labels with human-readable names."""

import argparse
import re
import tomllib
from pathlib import Path


def _load_label_mappings(labels_path: Path) -> dict[str, str]:
    """Load label mappings from TOML file.

    TOML format:
        Caleb = ["CHUNK_0_A", "CHUNK_1_B"]
        Austin = ["CHUNK_0_B", "CHUNK_1_A"]

    Returns dict mapping CHUNK_N_X -> name.
    """
    with open(labels_path, "rb") as f:
        data = tomllib.load(f)

    mappings: dict[str, str] = {}
    for name, labels in data.items():
        if isinstance(labels, list):
            for label in labels:
                mappings[label] = name
        else:
            # Single label as string
            mappings[labels] = name

    return mappings


def _replace_labels(transcript: str, label_onto_name: dict[str, str]) -> str:
    """Replace CHUNK_N_X labels with mapped names."""

    # Pattern matches CHUNK_N_X at the start of lines (speaker labels)
    # e.g., "CHUNK_0_A:" or "CHUNK_1_B:"
    def replace_match(match: re.Match[str]) -> str:
        label = match.group(1)
        name = label_onto_name.get(label, label)  # Keep original if not mapped
        return f"{name}:"

    # Replace labels at start of lines
    result = re.sub(r"^(CHUNK_\d+_[A-Z]+):", replace_match, transcript, flags=re.MULTILINE)

    return result


def main(transcript_path: Path, labels_path: Path) -> None:
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    # Load inputs
    transcript = transcript_path.read_text(encoding="utf-8")
    label_onto_name = _load_label_mappings(labels_path)

    print(f"Loaded {len(label_onto_name)} label mappings:")
    for label, name in sorted(label_onto_name.items()):
        print(f"  {label} -> {name}")

    # Replace labels
    result = _replace_labels(transcript, label_onto_name)

    # Write to new file
    output_path = transcript_path.with_suffix(".labeled.txt")
    output_path.write_text(result, encoding="utf-8")
    print(f"\nWrote: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="transcript-update-labels",
        description="Replace CHUNK_N_X speaker labels with human-readable names.",
    )
    parser.add_argument("transcript", help="Path to transcript.txt", type=Path)
    parser.add_argument("labels", help="Path to labels.toml", type=Path)
    args = parser.parse_args()

    main(transcript_path=args.transcript, labels_path=args.labels)
