-- ys<motion><char> adds a surround, ds<char> deletes one, cs<old><new>
-- changes one.  `S` in visual mode surrounds the selection, which is the one
-- default worth knowing about: it takes the key over from the built-in
-- linewise change.  `c` still does that.
require("nvim-surround").setup({})
