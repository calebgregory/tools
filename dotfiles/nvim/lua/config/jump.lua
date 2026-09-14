-- Labels are drawn as extmarks, so nothing is ever written to the buffer.
-- That is the whole reason this is here instead of easymotion, which swaps
-- the label characters into the text and confuses anything watching the
-- buffer (linters, diagnostics, git signs).
--
-- Two defaults are turned on below that ship off:
--
--   modes.search.enabled puts labels on every match of a regular `/` or `?`
--   search.  `<C-s>` while the search prompt is open toggles it back off for
--   that one search.
--
--   modes.char.jump_labels labels the other f/t targets as soon as you press
--   f/t, so you jump to the third one by its label instead of pressing `;`
--   twice.
--
-- The labels stay live for a moment after an f/t jump, which is what
-- label.exclude is for: a key in that string is never handed out as a label,
-- so it keeps its normal meaning when pressed right after the motion.  flash
-- ships "hjkliardc"; p and P are added because `fx` then `p` to paste at the
-- char you just jumped to is a sequence worth protecting.  The list is
-- case-sensitive and flash labels with both cases, so P needs its own entry -
-- excluding p alone would leave P live.
require("flash").setup({
  modes = {
    search = { enabled = true },
    char = {
      jump_labels = true,
      label = { exclude = "hjkliardcpP" },
    },
  },
})

local map = vim.keymap.set
local flash = function(fn) return function() require("flash")[fn]() end end

-- `s` and `S` take the keys over from the built-in substitute; `cl` and `cc`
-- are the same two commands and still work.
map({ "n", "x", "o" }, "s", flash("jump"),             { desc = "Flash jump" })
-- normal and operator-pending only: visual `S` belongs to nvim-surround
map({ "n", "o" },      "S", flash("treesitter"),       { desc = "Flash treesitter select" })
-- `dr<label>` deletes a textobject in another part of the screen, then puts
-- the cursor back where it started
map("o",               "r", flash("remote"),           { desc = "Flash remote (operate elsewhere)" })
map({ "o", "x" },      "R", flash("treesitter_search"),{ desc = "Flash treesitter search" })
map("c",            "<C-s>", flash("toggle"),          { desc = "Toggle flash labels while searching" })
