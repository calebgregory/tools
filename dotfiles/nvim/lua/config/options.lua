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

-- 2 spaces, matching editor.tabSize in the VS Code settings.  This is only the
-- global default: nvim ships ftplugins that set their own width per filetype,
-- and those run after this file, so the width a buffer actually gets is
-- whichever ftplugin spoke last.  That is where python's 4 comes from - the
-- "[python]" override in the VS Code settings needs nothing here.  To keep a
-- filetype on 2, override it back in after/ftplugin/<ft>.lua, as markdown does.
o.expandtab = true
o.shiftwidth, o.tabstop, o.softtabstop = 2, 2, 2

-- show tabs loudly, as .vimrc.after did with listchars=tab:T> in red
o.list = true
o.listchars = { tab = "T>", trail = "·", nbsp = "␣" }

-- files.insertFinalNewline.  This is already nvim's default; it is spelled out
-- so that a file saved here ends in a newline whatever a future plugin decides.
o.fixeol = true

