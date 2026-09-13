local o = vim.opt
o.number, o.relativenumber = true, true
o.clipboard = "unnamed"
o.signcolumn = "yes"
o.cursorline = true
o.wrap = true
o.linebreak = true
o.textwidth = 105
o.undofile = true
o.splitright, o.splitbelow = true, true
o.ignorecase, o.smartcase = true, true
o.scrolloff = 4
o.updatetime = 250
o.mouse = "a"
o.termguicolors = true

-- 2 spaces by default, 4 in python - matches editor.tabSize plus the
-- "[python]" override in the VS Code settings
o.expandtab = true
o.shiftwidth, o.tabstop, o.softtabstop = 2, 2, 2

-- show tabs loudly, as .vimrc.after did with listchars=tab:T> in red
o.list = true
o.listchars = { tab = "T>", trail = "·", nbsp = "␣" }

-- files.insertFinalNewline.  This is already nvim's default; it is spelled out
-- so that a file saved here ends in a newline whatever a future plugin decides.
o.fixeol = true

vim.cmd.colorscheme("minimal")
