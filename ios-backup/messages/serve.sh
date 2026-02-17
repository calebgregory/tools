#!/bin/bash

folder="$1"
if [ -z "${folder}" ]; then
  echo "must provide folder name"
  exit 1
fi

pushd "$HOME/Documents/iphone-message-backups/$1/export-html" || exit
trap "popd" EXIT
python -m http.server 8000