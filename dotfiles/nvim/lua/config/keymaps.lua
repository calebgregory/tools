local map = vim.keymap.set

-- descriptions are not decoration: they show up in `:nmap`, in `:verbose nmap
-- <key>`, and in the <leader>? picker in config.find
map("i", "jj", "<Esc>",                    { desc = "Escape to normal mode" })
map("i", "<C-c>", "<CR><Esc>O",            { desc = "Open a line above" })
map("n", "<C-u>", "viwUw",                 { desc = "Upcase word under cursor" })

-- move lines, as the VS Code C-j / C-k bindings did.  On Alt rather than Ctrl
-- so that <C-k> is free to be a chord prefix (see the copy-path mappings
-- below) without a timeoutlen pause on every line move.  WezTerm sends the
-- left Option key as Meta by default; the right one composes characters.
map("n", "<M-j>", "<cmd>m .+1<CR>==",      { desc = "Move line down" })
map("n", "<M-k>", "<cmd>m .-2<CR>==",      { desc = "Move line up" })
map("v", "<M-j>", ":m '>+1<CR>gv=gv",      { desc = "Move selection down" })
map("v", "<M-k>", ":m '<-2<CR>gv=gv",      { desc = "Move selection up" })

-- VS Code muscle memory
map("n", "<F12>", vim.lsp.buf.definition,      { desc = "Go to definition" })
map("n", "<S-F12>", vim.lsp.buf.references,    { desc = "References (this project only)" })
map("n", "K", vim.lsp.buf.hover,               { desc = "Hover docs" })
map("n", "<leader>rn", vim.lsp.buf.rename,     { desc = "Rename symbol" })
map("n", "<F2>", vim.lsp.buf.rename,     { desc = "Rename symbol" })
map("n", "<leader>ca", vim.lsp.buf.code_action,{ desc = "Code action" })
map("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, { desc = "Previous diagnostic" })
map("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end,  { desc = "Next diagnostic" })
map("n", "<leader>d", vim.diagnostic.open_float,                    { desc = "Show diagnostic" })

-- file nav
vim.keymap.set('n', '<leader>bb', '<C-^>', { desc = 'Switch to alternate file' })

-- copy the current buffer's path, on the same <C-k> ; chord as the VS Code
-- copyRelativeFilePath binding
local function yank_path(modifier)
  return function()
    local path = vim.fn.expand("%" .. modifier)
    vim.fn.setreg("+", path)
    vim.notify("Copied: " .. path)
  end
end
map("n", "<C-k>;", yank_path(":."), { desc = "Copy relative path of current file" })
map("n", "<C-k>'", yank_path(":p"), { desc = "Copy absolute path of current file" })
