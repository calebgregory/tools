local map = vim.keymap.set

require("nvim-tree").setup({
  view = { width = 36, signcolumn = "auto" },
  renderer = {
    group_empty = true,
    indent_markers = { enable = true },
    icons = { git_placement = "signcolumn" },
  },
  filters = { dotfiles = false, custom = { "^\\.git$", "^\\.venv$", "__pycache__" } },
  git = { enable = true, ignore = false },
  update_focused_file = { enable = true },  -- follow the buffer you are in
})

map("n", "<C-n>",     "<cmd>NvimTreeToggle<CR>",     { desc = "Toggle file tree" })
map("n", "<leader>n", "<cmd>NvimTreeFindFile<CR>",   { desc = "Reveal current file in tree" })
