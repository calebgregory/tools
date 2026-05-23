source ~/.vimrc.before

execute pathogen#infect()
syntax on
filetype plugin indent on

autocmd vimenter * NERDTree

autocmd Filetype * setlocal tabstop=2

source ~/.vimrc.after
