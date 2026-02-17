#!/bin/bash

folder="$1"
if [ -z "${folder}" ]; then
  echo "must provide folder name"
  exit 1
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/.secret"

html_export_path="$HOME/Documents/iphone-message-backups/$1/export-html"
txt_export_path="$HOME/Documents/iphone-message-backups/$1/export-txt"

imessage-exporter \
    --format html \
    --db-path "$DEVICE_BACKUP_ROOT" \
    --export-path "$html_export_path" \
    --copy-method full

imessage-exporter \
    --format txt \
    --db-path "$DEVICE_BACKUP_ROOT" \
    --export-path "$txt_export_path" \

uv run "$SCRIPT_DIR/rename-files-using-address-book.py" \
  "$DEVICE_BACKUP_ROOT" \
  "$html_export_path" \
  --ext html \
  --apply

uv run "$SCRIPT_DIR/rename-files-using-address-book.py" \
  "$DEVICE_BACKUP_ROOT" \
  "$txt_export_path" \
  --ext txt \
  --apply
