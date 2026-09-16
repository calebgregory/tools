-- Every module below runs for its side effects; none of them return anything.
-- Most of the order below just reads in a sensible sequence, but two steps
-- break the config if you move them:
--
--   config.pack goes first, because vim.pack.add is what puts the plugins on
--   the runtimepath, and every module after it requires one.
--
--   mapleader is set here rather than in config.keymaps, because a <leader>
--   mapping resolves the leader at the moment it is defined - setting it
--   afterwards would silently leave every such mapping on the old key.
require("config.pack")

vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("config.options")
require("config.appearance")
require("config.keymaps")
require("config.find")
require("config.replace")
require("config.treesitter")
require("config.git")
require("config.filetree")
require("config.surround")
require("config.jump")
require("config.lsp")
require("config.complete")
require("config.mypy")
require("config.format")

-- the one plugin that lives in this repo rather than coming from vim.pack
require("color_identifiers").setup({ filetypes = { "python", "lua" } })
