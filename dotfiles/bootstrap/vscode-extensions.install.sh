#!/bin/bash

while read -r line; do
  code --install-extension "$line"
done < ~/tools/dotfiles/bootstrap/vscode-extensions.txt

