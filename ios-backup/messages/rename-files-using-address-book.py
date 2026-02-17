#!/usr/bin/env -S uv run python
import os
import sqlite3
from pathlib import Path


def _hashed_path(backup_root: Path, file_id: str) -> Path:
    """Map a fileID (40-char SHA1) to its on-disk path in the backup."""
    p = backup_root / file_id[:2] / file_id
    if p.exists():
        return p
    # Some backups don't use subfolders
    p2 = backup_root / file_id
    if p2.exists():
        return p2
    raise FileNotFoundError(f"Cannot find file for {file_id}")


def _find_addressbook_db(backup_root: Path) -> Path:
    """Locate AddressBook.sqlitedb in a Finder/iTunes backup."""
    manifest = backup_root / "Manifest.db"
    conn = sqlite3.connect(manifest)
    row = conn.execute(
        """
        SELECT fileID, relativePath
        FROM Files
        WHERE relativePath LIKE '%AddressBook.sqlitedb'
    """
    ).fetchone()
    conn.close()
    if not row:
        raise FileNotFoundError("AddressBook.sqlitedb not found in Manifest.db")
    file_id, relpath = row
    db_path = _hashed_path(backup_root, file_id)
    print(f"Found AddressBook: {relpath} (fileID={file_id}) -> {db_path}")
    return db_path


def _build_contact_mapping(addressbook_db: Path) -> dict[str, str]:
    """Return mapping from phone/email to display name."""
    conn = sqlite3.connect(addressbook_db)
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT ABMultiValue.value,
               COALESCE(ABPerson.First, '') as first,
               COALESCE(ABPerson.Last, '') as last,
               COALESCE(ABPerson.Organization, '') as org
        FROM ABPerson
        JOIN ABMultiValue ON ABPerson.ROWID = ABMultiValue.record_id;
    """
    ).fetchall()
    conn.close()

    contact_id_onto_display_name: dict[str, str] = {}
    for value, first, last, org in rows:
        display = " ".join(p for p in (first, last) if p).strip()
        if not display and org:
            display = org
        elif display and org:
            display += f" ({org})"
        if not display:
            display = value
        contact_id_onto_display_name[value] = display
    return contact_id_onto_display_name


def _rename_exports(
    export_dir: Path, contact_id_onto_display_name: dict[str, str], ext: str, dry_run: bool = True
) -> None:
    """Rename exported HTML files using contact names when available."""
    for html_file in export_dir.glob(f"*.{ext}"):
        ids = [p.strip() for p in html_file.stem.split(",")]  # e.g. "+1555..., +1444..."
        new_parts = [
            (f"{name}_{p}" if (name := contact_id_onto_display_name.get(p)) else p) for p in ids
        ]
        new_base = ", ".join(new_parts)
        new_file = html_file.with_name(new_base + f".{ext}")

        if new_file == html_file:
            continue
        print(f"Renaming: {html_file.name} -> {new_file.name}")
        if not dry_run:
            os.rename(html_file, new_file)


def main(backup_root: Path, export_dir: Path, ext: str, apply: bool = False) -> None:
    addressbook_db = _find_addressbook_db(backup_root)
    mapping = _build_contact_mapping(addressbook_db)
    _rename_exports(export_dir, mapping, ext, dry_run=not apply)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename imessage-exporter HTML files with contact names"
    )
    parser.add_argument(
        "backup_root", type=Path, help="Path to device backup root (contains Manifest.db)"
    )
    parser.add_argument("export_dir", type=Path, help="Directory containing exported HTML files")
    parser.add_argument("--ext", default="html", choices=("html", "txt"))
    parser.add_argument(
        "--apply", action="store_true", help="Actually rename files (default is dry run)"
    )
    args = parser.parse_args()
    main(args.backup_root, args.export_dir, args.ext, args.apply)
