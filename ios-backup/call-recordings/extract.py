#!/usr/bin/env -S uv run python

import re
import shutil
import sqlite3
import tempfile
import typing as ty
from datetime import datetime, timedelta, timezone
from pathlib import Path

_NOTES_DOMAIN = "AppDomainGroup-group.com.apple.notes"
_CORE_DATA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _backup_abspath_for_file_id(backup_root: Path, file_id: str) -> Path:
    """In iPhone backups, files are stored at {first_two_chars_of_hash}/{hash}."""
    return backup_root / file_id[:2] / file_id


def _sanitize(name: str) -> str:
    return re.sub(r"[^\w\s\-\.,()]", "", name).strip()


def _format_core_data_timestamp(ts: float) -> str:
    dt = _CORE_DATA_EPOCH + timedelta(seconds=ts)
    return dt.astimezone().strftime("%Y-%m-%d %H%M")


class _Recording(ty.NamedTuple):
    media_uuid: str
    note_title: str
    duration: float
    creation_date: float | None
    filename: str


def _find_recordings_in_notestore(notestore_path: Path) -> list[_Recording]:
    """Query NoteStore.sqlite for actual audio attachments (not the 0-duration stubs)."""
    with sqlite3.connect(str(notestore_path)) as conn:
        rows = conn.execute(
            """
            SELECT
                media.ZIDENTIFIER,
                note.ZTITLE1,
                att.ZDURATION,
                att.ZCREATIONDATE,
                media.ZFILENAME
            FROM ZICCLOUDSYNCINGOBJECT att
            JOIN ZICCLOUDSYNCINGOBJECT media ON att.ZMEDIA = media.Z_PK
            JOIN ZICCLOUDSYNCINGOBJECT note ON att.ZNOTE = note.Z_PK
            WHERE att.ZTYPEUTI = 'public.mpeg-4-audio'
              AND att.ZDURATION > 0
              AND media.ZIDENTIFIER IS NOT NULL
            ORDER BY att.ZCREATIONDATE
            """
        ).fetchall()

    return [
        _Recording(media_uuid, note_title, duration, creation_date, filename)
        for media_uuid, note_title, duration, creation_date, filename in rows
    ]


def _resolve_backup_path(media_uuid: str, manifest_db: sqlite3.Connection) -> tuple[str, str] | None:
    """Find the actual audio file in Manifest.db by media UUID."""
    row = manifest_db.execute(
        """
        SELECT fileID, relativePath FROM Files
        WHERE domain = ?
          AND relativePath LIKE ?
          AND relativePath LIKE '%audio.MOV'
        """,
        (_NOTES_DOMAIN, f"%{media_uuid}%"),
    ).fetchone()
    if not row:
        return None
    file_id: str = row[0]
    relpath: str = row[1]
    return file_id, relpath


def _derive_friendly_name(rec: _Recording) -> str:
    parts = []
    if rec.note_title:
        parts.append(_sanitize(rec.note_title))
    if rec.creation_date:
        parts.append(_format_core_data_timestamp(rec.creation_date))
    mins = rec.duration / 60
    parts.append(f"({mins:.0f}min)")
    return " ".join(parts) + ".m4a"


def main(backup_root: Path, output_dir: Path) -> None:
    manifest = backup_root / "Manifest.db"
    if not manifest.exists():
        raise EnvironmentError(f"Manifest.db not found at {manifest}")

    output_dir.mkdir(exist_ok=True, parents=True)

    manifest_db = sqlite3.connect(str(manifest))

    # extract NoteStore.sqlite to a temp file for querying
    row = manifest_db.execute(
        "SELECT fileID FROM Files WHERE domain = ? AND relativePath = 'NoteStore.sqlite'",
        (_NOTES_DOMAIN,),
    ).fetchone()
    if not row:
        print("NoteStore.sqlite not found in backup.")
        return

    notestore_src = _backup_abspath_for_file_id(backup_root, row[0])
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        shutil.copy2(notestore_src, tmp.name)
        recordings = _find_recordings_in_notestore(Path(tmp.name))
        Path(tmp.name).unlink()

    if not recordings:
        print("No call recordings found in NoteStore.")
        return

    print(f"Found {len(recordings)} call recordings.\n")

    for rec in recordings:
        resolved = _resolve_backup_path(rec.media_uuid, manifest_db)
        if not resolved:
            print(f"  MISSING from backup: {rec.note_title} ({rec.duration / 60:.0f}min)")
            continue

        file_id, relpath = resolved
        src = _backup_abspath_for_file_id(backup_root, file_id)
        if not src.exists():
            print(f"  WARNING: file missing on disk: {relpath}")
            continue

        friendly = _derive_friendly_name(rec)
        dest = output_dir / friendly

        if dest.exists():
            stem, suffix = dest.stem, dest.suffix
            i = 2
            while dest.exists():
                dest = output_dir / f"{stem} ({i}){suffix}"
                i += 1

        print(f"  {friendly}")
        shutil.copy2(src, dest)

    print(f"\nDone. Extracted to: {output_dir.resolve()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("backup_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    main(args.backup_root, args.output_dir)
