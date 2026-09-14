-- vim.pack ships with nvim 0.12, so there is no bootstrap block here.
-- `:lua vim.pack.update()` to update.
--
-- This runs before every other config module, because vim.pack.add puts the
-- plugins on the runtimepath and the modules that follow require them.
vim.pack.add({
  { src = "https://github.com/ibhagwan/fzf-lua" },
  { src = "https://github.com/nvim-treesitter/nvim-treesitter", version = "main" },
  { src = "https://github.com/esmuellert/codediff.nvim" },
  { src = "https://github.com/lewis6991/gitsigns.nvim" },
  { src = "https://github.com/nvim-tree/nvim-tree.lua" },
  { src = "https://github.com/kylechui/nvim-surround", version = vim.version.range("^3.0.0") },
  { src = "https://github.com/folke/flash.nvim" },
})
