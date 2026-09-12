-- ── Plugins ───────────────────────────────────────────────────────────
-- vim.pack ships with nvim 0.12, so there is no bootstrap block here.
-- `:lua vim.pack.update()` to update.
vim.pack.add({
  { src = "https://github.com/ibhagwan/fzf-lua" },
  { src = "https://github.com/nvim-treesitter/nvim-treesitter", version = "main" },
  { src = "https://github.com/esmuellert/codediff.nvim" },
  { src = "https://github.com/lewis6991/gitsigns.nvim" },
  { src = "https://github.com/nvim-tree/nvim-tree.lua" },
})

vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- ── Options ───────────────────────────────────────────────────────────
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

-- 2 spaces by default, 4 in python - matches editor.tabSize plus the
-- "[python]" override in the VS Code settings
o.expandtab = true
o.shiftwidth, o.tabstop, o.softtabstop = 2, 2, 2

-- show tabs loudly, as .vimrc.after did with listchars=tab:T> in red
o.list = true
o.listchars = { tab = "T>", trail = "·", nbsp = "␣" }

vim.cmd.colorscheme("minimal")

-- ── Keymaps ───────────────────────────────────────────────────────────
local map = vim.keymap.set

-- descriptions are not decoration: they show up in `:nmap`, in `:verbose nmap
-- <key>`, and in the <leader>? picker below
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
map("n", "<leader>ca", vim.lsp.buf.code_action,{ desc = "Code action" })
map("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end, { desc = "Previous diagnostic" })
map("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end,  { desc = "Next diagnostic" })
map("n", "<leader>e", vim.diagnostic.open_float,                    { desc = "Show diagnostic" })

-- ── Finding things ────────────────────────────────────────────────────
-- The monorepo has ~100 projects and the LSP is rooted at ONE of them, so
-- Shift+F12 only ever answers for the current project.  The repo-wide
-- searches below are the cross-project half, and they run from the git root.
local function git_root()
  local root = vim.fs.root(vim.api.nvim_buf_get_name(0), ".git")
  return root or vim.fn.getcwd()
end

local fzf = function(fn, opts)
  return function() require("fzf-lua")[fn](opts and opts() or {}) end
end

map("n", "<C-p>",      fzf("files"),                                  { desc = "Files (project)" })
map("n", "<leader>ff", fzf("files"),                                  { desc = "Files (project)" })
map("n", "<leader>fF", fzf("files", function() return { cwd = git_root() } end),     { desc = "Files (repo)" })
map("n", "<leader>fg", fzf("live_grep"),                              { desc = "Grep (project)" })
map("n", "<leader>fG", fzf("live_grep", function() return { cwd = git_root() } end), { desc = "Grep (repo)" })
map("n", "<leader>fb", fzf("buffers"),                                { desc = "Buffers" })
map("n", "<leader>fs", fzf("lsp_document_symbols"),                   { desc = "Symbols (file)" })
map("n", "<leader>?",  fzf("keymaps"),                                { desc = "Search my keybindings" })
-- the honest Shift+F12 replacement: word under cursor, whole repo
map("n", "<leader>R",  fzf("grep_cword", function() return { cwd = git_root() } end),
  { desc = "References across the repo (ripgrep)" })

-- ── Treesitter ────────────────────────────────────────────────────────
local PARSERS = { "python", "lua", "bash", "json", "yaml", "toml", "markdown",
                  "markdown_inline", "sql", "dockerfile", "diff", "gitcommit" }

vim.api.nvim_create_autocmd("FileType", {
  callback = function(args)
    local lang = vim.treesitter.language.get_lang(args.match)
    if lang and vim.treesitter.language.add(lang) then
      vim.treesitter.start(args.buf, lang)
      vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
    end
  end,
})

vim.api.nvim_create_user_command("TSInstallAll", function()
  require("nvim-treesitter").install(PARSERS)
end, { desc = "Install the parsers this config expects" })

-- ── Source control ───────────────────────────────────────────────────
-- :CodeDiff is the VS Code source-control view: a file panel of changed files
-- with status, a side-by-side diff whose right pane is the editable working
-- tree, and staging from the panel (- toggles a file, S / U stage or unstage
-- everything).
require("gitsigns").setup({
  signs = {
    add = { text = "+" }, change = { text = "~" },
    delete = { text = "_" }, topdelete = { text = "‾" }, changedelete = { text = "~" },
  },
  on_attach = function(buf)
    local gs = require("gitsigns")
    local function m(lhs, rhs, desc)
      map("n", lhs, rhs, { buffer = buf, desc = desc })
    end
    m("]h", function() gs.nav_hunk("next") end, "Next hunk")
    m("[h", function() gs.nav_hunk("prev") end, "Previous hunk")
    m("<leader>hs", gs.stage_hunk,        "Stage hunk")
    m("<leader>hr", gs.reset_hunk,        "Reset hunk")
    m("<leader>hp", gs.preview_hunk,      "Preview hunk")
    m("<leader>hb", gs.blame_line,        "Blame line")
    m("<leader>hd", gs.diffthis,          "Diff this file")
  end,
})

-- one command with subcommands; `:CodeDiff <Tab>` also completes git revs and
-- ranges, so `:CodeDiff main...` reviews just this branch's work
map("n", "<leader>gs", "<cmd>CodeDiff<CR>",         { desc = "Source control (changed files)" })
map("n", "<leader>gh", "<cmd>CodeDiff history<CR>", { desc = "File history" })
map("n", "<leader>gm", "<cmd>CodeDiff main...<CR>", { desc = "Review this branch against main" })
map("n", "<leader>gp", "<cmd>CodeDiff pr<CR>",      { desc = "Review a pull request" })

-- ── File tree ────────────────────────────────────────────────────────
require("nvim-tree").setup({
  view = { width = 36 },
  renderer = { group_empty = true, indent_markers = { enable = true } },
  filters = { dotfiles = false, custom = { "^\\.git$", "^\\.venv$", "__pycache__" } },
  git = { enable = true, ignore = false },
  update_focused_file = { enable = true },  -- follow the buffer you are in
})
map("n", "<C-n>",     "<cmd>NvimTreeToggle<CR>",     { desc = "Toggle file tree" })
map("n", "<leader>n", "<cmd>NvimTreeFindFile<CR>",   { desc = "Reveal current file in tree" })

-- ── Color identifiers ─────────────────────────────────────────────────
require("color_identifiers").setup({ filetypes = { "python", "lua" } })

-- ── LSP ───────────────────────────────────────────────────────────────
-- One server per project root.  root_markers resolves to the NEAREST ancestor
-- holding a pyproject.toml, so apps/unified-asset gets its own server rather
-- than inheriting the repo root and dragging in all ~100 projects.
vim.lsp.config("basedpyright", {
  cmd = { "basedpyright-langserver", "--stdio" },
  filetypes = { "python" },
  root_markers = { "pyproject.toml" },
  settings = {
    basedpyright = {
      analysis = { diagnosticMode = "openFilesOnly", typeCheckingMode = "standard" },
    },
  },
  -- on_init, not before_init: the server pulls settings via
  -- workspace/configuration after it starts and nvim answers from
  -- client.settings, so the venv has to be on the client by then.  Each root
  -- has its own uv venv, and the editable .pth files inside it are how the
  -- server reaches libs/*/src.
  on_init = function(client)
    local venv = client.root_dir .. "/.venv/bin/python"
    if not vim.uv.fs_stat(venv) then
      -- Without it the server still attaches and still answers about this
      -- project's own code, but every third-party and sibling-lib import comes
      -- back unresolved, which looks like a broken config rather than a missing
      -- venv.  Say so instead of failing quietly.
      vim.notify(
        ("basedpyright: no .venv in %s\nimports will not resolve; run `uv run mono venvs install %s`")
          :format(vim.fn.fnamemodify(client.root_dir, ":~"), vim.fn.fnamemodify(client.root_dir, ":.")),
        vim.log.levels.WARN)
      return
    end
    client.settings = vim.tbl_deep_extend("force", client.settings or {}, {
      python = { pythonPath = venv },
    })
  end,
})

vim.lsp.config("ruff", {
  cmd = { "ruff", "server" },
  filetypes = { "python" },
  root_markers = { "pyproject.toml" },
  on_attach = function(client)
    -- basedpyright owns hover; two servers answering is just noise
    client.server_capabilities.hoverProvider = false
  end,
})

vim.lsp.enable({ "basedpyright", "ruff" })

-- ── On save ───────────────────────────────────────────────────────────
-- ports editor.formatOnSave + codeActionsOnSave source.fixAll, ruff-only
vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = "*.py",
  callback = function(args)
    vim.lsp.buf.format({ bufnr = args.buf, name = "ruff", timeout_ms = 3000 })
  end,
})

-- files.trimTrailingWhitespace, for everything ruff does not own
vim.api.nvim_create_autocmd("BufWritePre", {
  callback = function()
    if vim.bo.filetype == "python" then return end
    local pos = vim.api.nvim_win_get_cursor(0)
    vim.cmd([[keeppatterns %s/\s\+$//e]])
    pcall(vim.api.nvim_win_set_cursor, 0, pos)
  end,
})

-- ── Which server am I talking to? ─────────────────────────────────────
vim.api.nvim_create_user_command("LspRoots", function()
  for _, c in ipairs(vim.lsp.get_clients()) do
    print(string.format("%-14s %s", c.name, vim.fn.fnamemodify(c.root_dir or "-", ":~")))
  end
end, { desc = "List active servers and their roots" })
