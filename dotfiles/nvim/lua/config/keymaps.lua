local map = vim.keymap.set

-- descriptions are not decoration: they show up in `:nmap`, in `:verbose nmap
-- <key>`, and in the <leader>? picker in config.find
map("i", "jj", "<Esc>",                    { desc = "Escape to normal mode" })
map("i", "<C-c>", "<CR><Esc>O",            { desc = "Open a line above" })
map("n", "<C-u>", "viwUw",                 { desc = "Upcase word under cursor" })

-- move lines, as the VS Code C-j / C-k bindings did
map("n", "<C-j>", "<cmd>m .+1<CR>==",      { desc = "Move line down" })
map("n", "<C-k>", "<cmd>m .-2<CR>==",      { desc = "Move line up" })
map("v", "<C-j>", ":m '>+1<CR>gv=gv",      { desc = "Move selection down" })
map("v", "<C-k>", ":m '<-2<CR>gv=gv",      { desc = "Move selection up" })

-- VS Code muscle memory
map("n", "<F12>", vim.lsp.buf.definition,      { desc = "Go to definition" })
map("n", "<S-F12>", vim.lsp.buf.references,    { desc = "References (this project only)" })
map("n", "K", vim.lsp.buf.hover,               { desc = "Hover docs" })
map("n", "<leader>rn", vim.lsp.buf.rename,     { desc = "Rename symbol" })
map("n", "<F2>", vim.lsp.buf.rename,     { desc = "Rename symbol" })
map("n", "<leader>ca", vim.lsp.buf.code_action,{ desc = "Code action" })
map("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, { desc = "Previous diagnostic" })
map("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end,  { desc = "Next diagnostic" })
map("n", "<leader>e", vim.diagnostic.open_float,                    { desc = "Show diagnostic" })
