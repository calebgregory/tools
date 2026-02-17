#!/usr/bin/env -S uv run python

import plistlib
import re
import shutil
import sqlite3
from functools import partial
from pathlib import Path


def _backup_abspath_for_file_id(backup_root: Path, file_id: str) -> Path:
    """in iphone backups, a "fileID" is a hashed form of the relpath.  they
    store these files at their hashed filenames in subdirectories, where the
    subdirectory name == first two chars of the hash"""
    subdir = file_id[:2]
    src = backup_root / subdir / file_id
    return src


def _sanitize(name: str) -> str:
    """Remove characters illegal in filenames."""
    return re.sub(r"[^\w\s\-\.,()]", "", name).strip()


def _find_all_voice_memo_files(
    backup_root: Path, manifest_db: sqlite3.Connection
) -> dict[str, Path] | None:
    cur = manifest_db.cursor()

    print("Querying for files in voice memos app…")
    cur.execute(
        """
        SELECT fileID, relativePath
        FROM Files
        WHERE domain = 'AppDomainGroup-group.com.apple.VoiceMemos.shared'
        ORDER BY relativePath;
    """
    )
    rows = cur.fetchall()

    if not rows:
        print("No voice memo .m4a files found!")
        return None

    print(f"Found {len(rows)} voice memos files.")
    return {relpath: _backup_abspath_for_file_id(backup_root, file_id) for file_id, relpath in rows}


def _select_only_resultant_audio_files(all_voice_memo_files: dict[str, Path]) -> dict[str, Path]:
    """the voice memo app stores "waveform" files and "fragment" m4a files; we
    only want the final output."""
    resultant_audio_files = {
        relpath: abspath
        for relpath, abspath in all_voice_memo_files.items()
        if relpath.startswith("Recordings")
        and relpath.endswith(".m4a")
        and "/fragments/" not in relpath
    }
    print(f"Found {len(resultant_audio_files)} resultant audio files.")
    return resultant_audio_files


###
# within the voice memos app, you can name files something informative.  we want
# to retain that information, rather than having hundreds of unnamed files
###


def _build_file_id_onto_title(
    recordings_db: Path | None,
) -> dict[str, str]:
    if not recordings_db:
        return dict()

    with sqlite3.connect(recordings_db) as conn:
        cur = conn.cursor()
        cur.execute("select ZPATH, ZENCRYPTEDTITLE from ZCLOUDRECORDING;")
        rows = cur.fetchall()

        file_id_onto_title = {file_name: title for file_name, title in rows}
        return file_id_onto_title


def _recording_db_path_from_relpath(relpath: str) -> str:
    return Path(relpath).name


def _get_title_from_recordings_db(
    file_id_onto_title: dict[str, str], audio_file_relpath: str
) -> str:
    path = _recording_db_path_from_relpath(audio_file_relpath)
    return file_id_onto_title.get(path) or ""


def _manifest_plist_for_file(
    all_voice_memo_files: dict[str, Path], audio_file_relpath: str
) -> dict | None:
    audio_file_without_m4a = audio_file_relpath.replace(".m4a", "")
    manifest_plist_relpath = f"{audio_file_without_m4a}.composition/manifest.plist"
    if f := all_voice_memo_files.get(manifest_plist_relpath):
        manifest_plist: dict = plistlib.loads(f.read_text())
        return manifest_plist
    return None


def _derive_friendly_name(
    title_in_db: str, manifest_plist: dict | None, audio_file_relpath: str
) -> str:
    original_stem = Path(audio_file_relpath).stem

    if title_in_db:
        return f"{original_stem} {title_in_db}.m4a"

    if manifest_plist:
        title = manifest_plist["RCSavedRecordingTitle"]
        return f"{original_stem} {title}.m4a"

    return Path(audio_file_relpath).name


def main(backup_root: Path, output_dir: Path) -> None:
    manifest = backup_root / "Manifest.db"
    if not manifest.exists():
        raise EnvironmentError(f"Manifest.db not found at {manifest}")

    shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    print("Connecting to Manifest.db…")
    manifest_db = sqlite3.connect(str(manifest))

    all_voice_memo_files = _find_all_voice_memo_files(backup_root, manifest_db)
    if not all_voice_memo_files:
        print("No files found.")
        return

    audio_files = _select_only_resultant_audio_files(all_voice_memo_files)

    recordings_db = all_voice_memo_files.get("Recordings/CloudRecordings.db")
    get_title_from_recordings_db = partial(
        _get_title_from_recordings_db, _build_file_id_onto_title(recordings_db)
    )

    for relpath, src in audio_files.items():
        if not src.exists():
            print(f"WARNING: Missing backup file: {relpath}, {src}")
            continue

        friendly_name = _derive_friendly_name(
            title_in_db=get_title_from_recordings_db(relpath),
            manifest_plist=_manifest_plist_for_file(all_voice_memo_files, relpath),
            audio_file_relpath=relpath,
        )
        shutil.copy2(src, output_dir / friendly_name)

    print("\nDone. Extracted files are in:", output_dir.resolve())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("backup_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    main(args.backup_root, args.output_dir)
