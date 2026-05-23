imap jj <Esc>

" Yank to system clipboard
set clipboard=unnamed

exmap surround_double_quotes surround " "
exmap surround_single_quotes surround ' '
exmap surround_backticks surround ` `
exmap surround_brackets surround ( )
exmap surround_square_brackets surround [ ]
exmap surround_curly_brackets surround { }

nunmap s
nmap siw" :surround_double_quotes<CR>
nmap siw' :surround_single_quotes<CR>
nmap siw` :surround_backticks<CR>
nmap siw( :surround_brackets<CR>
nmap siw) :surround_brackets<CR>
nmap siw[ :surround_square_brackets<CR>
nmap siw] :surround_square_brackets<CR>
nmap siw{ :surround_curly_brackets<CR>
nmap siw} :surround_curly_brackets<CR>

vunmap S
vmap S" :surround_double_quotes<CR>
vmap S' :surround_single_quotes<CR>
vmap S` :surround_backticks<CR>
vmap S( :surround_brackets<CR>
vmap S) :surround_brackets<CR>
vmap S[ :surround_square_brackets<CR>
vmap S] :surround_square_brackets<CR>
vmap S{ :surround_curly_brackets<CR>
vmap S} :surround_curly_brackets<CR>

