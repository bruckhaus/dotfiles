#!/bin/zsh

here=${0:a:h}
files=('.bash_profile' '.bashrc' '.emacs' '.gitconfig' '.zshrc' '.config/wezterm' '.config/starship.toml')

for i in $files; do
  ln -s "${here}"/"${i}" "${HOME}"
done

