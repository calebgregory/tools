#!/bin/bash

folder="$1"
if [ -z "${folder}" ]; then
  echo "must provide folder name"
  exit 1
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/.secret"

uv run "$SCRIPT_DIR/extract.py" "$DEVICE_BACKUP_ROOT" "$1"
