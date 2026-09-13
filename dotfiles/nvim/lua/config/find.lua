-- The monorepo has ~100 projects and the LSP is rooted at ONE of them, so
-- Shift+F12 only ever answers for the current project.  The repo-wide
-- searches below are the cross-project half, and they run from the git root.
local map = vim.keymap.set

local function git_root()
  local root = vim.fs.root(vim.api.nvim_buf_get_name(0), ".git")
  return root or vim.fn.getcwd()
end

local fzf = function(fn, opts)
  return function() require("fzf-lua")[fn](opts and opts() or {}) end
end

map("n", "<C-p>",      fzf("files"),                                  { desc = "fzf Files (project)" })
map("n", "<leader>ff", fzf("files"),                                  { desc = "fzf Files (project)" })
map("n", "<leader>fF", fzf("files", function() return { cwd = git_root() } end),     { desc = "fzf Files (repo)" })
map("n", "<leader>fg", fzf("live_grep"),                              { desc = "fzf Grep (project)" })
map("n", "<leader>fG", fzf("live_grep", function() return { cwd = git_root() } end), { desc = "fzf Grep (repo)" })
map("n", "<leader>fb", fzf("buffers"),                                { desc = "Buffers" })
map("n", "<leader>fs", fzf("lsp_document_symbols"),                   { desc = "Symbols (file)" })
map("n", "<leader>?",  fzf("keymaps"),                                { desc = "Search my keybindings" })
-- the honest Shift+F12 replacement: word under cursor, whole repo
map("n", "<leader>R",  fzf("grep_cword", function() return { cwd = git_root() } end),
  { desc = "References across the repo (ripgrep)" })
