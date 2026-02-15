#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

mkdir dist/

pnpx @vscode/vsce package --skip-license --out dist/md-checkboxes.vsix

code --install-extension dist/md-checkboxes.vsix
