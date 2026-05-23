#!/bin/bash

### symlink dotfiles (whitelist-style, to prevent accidents)

cd "$HOME" || exit 1

rm ~/.zshrc # has to be removed for symlink

files_to_symlink=(
  .default-python-packages
  .emacs.d
  .git-credentials
  .gitconfig
  .gitignore_global
  .gitmux.conf
  .gvimrc.after
  .tmux.conf
  .vimrc.after
  .zshrc
  .wezterm.lua
)
for file in "${files_to_symlink[@]}"; do
  ln -s ~/tools/dotfiles/"${file}" ~
done

ln -s ~/tools/dotfiles/mise.toml ~/.config/mise/config.toml

mkdir -p ~/.config/lemonaid/
ln -s ~/tools/dotfiles/lemonaid.toml ~/.config/lemonaid/config.toml

mkdir -p ~/.config/yazi/
ln -s ~/tools/dotfiles/yazi.toml ~/.config/yazi/yazi.toml

for file in keybindings.json settings.json; do
  ln -s ~/tools/dotfiles/vscode/"$file" ~/"Library/Application Support/Code/User/$file"
done
