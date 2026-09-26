-- Ctrl+n works like VS Code's Cmd+D: the first press puts a second cursor on
-- the next match of the word (or visual selection) under the cursor, and each
-- press after that adds one more.  Then edit as usual and every cursor follows.
--
-- The mappings inside the keymap layer only exist while there is more than one
-- cursor, which is what lets them take keys that mean something else the rest
-- of the time: <C-x> is decrement and <Esc> does nothing in normal mode.
local mc = require("multicursor-nvim")
mc.setup()

local map = vim.keymap.set

map({ "n", "x" }, "<C-n>",     function() mc.matchAddCursor(1) end, { desc = "Add cursor at next match" })
map({ "n", "x" }, "<leader>A", mc.matchAllAddCursors,               { desc = "Add cursor at every match" })

mc.addKeymapLayer(function(layer_map)
  layer_map({ "n", "x" }, "<C-x>", function() mc.matchSkipCursor(1) end, { desc = "Skip this match" })
  layer_map("n", "<Esc>", mc.clearCursors, { desc = "Back to one cursor" })
end)
