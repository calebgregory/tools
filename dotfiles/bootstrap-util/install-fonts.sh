#!/bin/bash

for ttf in ~/tools/dotfiles/assets/fonts/*; do
  file_name="$(basename "${ttf}")"
  target="$HOME/Library/Fonts/${file_name}"

  if [ ! -f "${target}" ]; then
    cp "${ttf}" "${target}"
    echo "✔ ${file_name} installed"
  else
    echo "x ${file_name} already installed"
  fi
done

echo "done"
