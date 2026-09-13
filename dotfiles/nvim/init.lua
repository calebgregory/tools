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

-- files.insertFinalNewline.  This is already nvim's default; it is spelled out
-- so that a file saved here ends in a newline whatever a future plugin decides.
o.fixeol = true

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
  -- typeCheckingMode "off" leaves hover, go-to-definition, references and
  -- rename - which is what basedpyright is here for - and stops it reporting
  -- type errors.  mypy owns those, because mypy is what CI enforces: two
  -- checkers disagreeing in the sign column about the same line, in different
  -- words, costs more than the second opinion is worth.
  settings = {
    basedpyright = {
      analysis = { diagnosticMode = "openFilesOnly", typeCheckingMode = "off" },
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

-- ── mypy ──────────────────────────────────────────────────────────────
-- mypy is what CI enforces, and it is not a language server, so it does not
-- arrive through vim.lsp at all: we run the project's own mypy on save and
-- push what it says into vim.diagnostic ourselves.
--
-- It has to be the project's own mypy rather than one on PATH.  There is no
-- mypy on PATH here by design - each root installs its own into .venv, and
-- versions differ between them (1.19 and 2.0 are both checked out right now),
-- so a single global binary would report against the wrong config and the
-- wrong dependencies.
--
-- --output=json is the parsing contract.  Both versions above support it, it
-- gives 0-based columns already in the shape vim.diagnostic wants, and it
-- sidesteps a regex over a human-readable line that varies by release.
local MYPY_SEVERITY = {
  error = vim.diagnostic.severity.ERROR,
  warning = vim.diagnostic.severity.WARN,
  note = vim.diagnostic.severity.HINT,
}

local mypy_ns = vim.api.nvim_create_namespace("mypy")

-- mypy follows imports, so it reports on the saved file's whole dependency
-- graph.  We keep only the saved file's own errors: a buffer's mypy
-- diagnostics are then exactly what mypy said about it at its last save, and
-- nothing here can leave a stale error in a buffer we never re-check.  The
-- cost is that an error your change caused in a file that imports this one
-- shows up when you save that file, not this one.
local function mypy_diagnostics(stdout, root, path)
  local diags = {}
  for line in vim.gsplit(stdout or "", "\n", { trimempty = true }) do
    local ok, d = pcall(vim.json.decode, line)
    if ok and d.file and vim.fs.normalize(root .. "/" .. d.file) == path then
      table.insert(diags, {
        lnum = d.line - 1,
        col = d.column,
        -- end_line/end_column arrived in mypy 2.0; 1.x marks a point instead
        end_lnum = (d.end_line or d.line) - 1,
        end_col = d.end_column or d.column,
        severity = MYPY_SEVERITY[d.severity] or vim.diagnostic.severity.ERROR,
        -- a JSON null decodes to vim.NIL, which is a userdata and therefore
        -- truthy; only an absent key arrives as a Lua nil
        message = d.hint ~= vim.NIL and (d.message .. "\n" .. d.hint) or d.message,
        code = d.code,
        source = "mypy",
      })
    end
  end
  return diags
end

-- one warning per root, not one per save
local mypy_missing = {}
-- the most recent run per buffer, so that a save landing while mypy is still
-- thinking about the previous one does not get overwritten by the older answer
local mypy_run = {}

local function run_mypy(buf)
  local path = vim.fs.normalize(vim.api.nvim_buf_get_name(buf))
  local root = vim.fs.root(buf, "pyproject.toml")
  if not root then return end

  local mypy = root .. "/.venv/bin/mypy"
  if not vim.uv.fs_stat(mypy) then
    if not mypy_missing[root] then
      mypy_missing[root] = true
      vim.notify(
        ("mypy: not installed in %s/.venv\nno mypy diagnostics for this project")
          :format(vim.fn.fnamemodify(root, ":~")),
        vim.log.levels.WARN)
    end
    return
  end

  local token = (mypy_run[buf] or 0) + 1
  mypy_run[buf] = token

  vim.system({ mypy, "--output=json", "--no-error-summary", path },
    { cwd = root, text = true },
    vim.schedule_wrap(function(res)
      if mypy_run[buf] ~= token or not vim.api.nvim_buf_is_valid(buf) then return end
      -- 0 is clean and 1 is "found errors"; anything above that is mypy itself
      -- failing, and clearing the buffer would read as the file having become
      -- clean when nobody checked it
      if res.code > 1 then
        vim.notify(("mypy: %s"):format(vim.trim(res.stderr or "")), vim.log.levels.WARN)
        return
      end
      vim.diagnostic.set(mypy_ns, buf, mypy_diagnostics(res.stdout, root, path))
    end))
end

-- BufWritePost, not Pre: mypy reads the file off disk, so it has to be there
vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = "*.py",
  callback = function(args) run_mypy(args.buf) end,
})

vim.api.nvim_create_user_command("Mypy", function()
  run_mypy(vim.api.nvim_get_current_buf())
end, { desc = "Re-run mypy on this buffer, without waiting for a save" })

-- ── On save ───────────────────────────────────────────────────────────
-- ports editor.formatOnSave + codeActionsOnSave source.fixAll, ruff-only, and
-- adds import sorting on top of what the VS Code settings asked for.
--
-- `ruff format` does not touch import order - sorting is isort's job, which
-- ruff exposes as a code action rather than as part of the formatter.  So the
-- two rewriting actions run first and the formatter last, which is also the
-- only order that leaves the buffer formatted: an action that moves or deletes
-- a line can leave blank lines the formatter would otherwise have collapsed.
local RUFF_ON_SAVE = { "source.organizeImports.ruff", "source.fixAll.ruff" }

local function ruff_code_action(buf, kind)
  local client = vim.lsp.get_clients({ bufnr = buf, name = "ruff" })[1]
  if not client then return end

  -- ruff's source actions cover the whole document, so the range is a
  -- formality; build the params by hand rather than reading them off whichever
  -- window happens to be current during BufWritePre
  local zero = { line = 0, character = 0 }
  local res = client:request_sync("textDocument/codeAction", {
    textDocument = vim.lsp.util.make_text_document_params(buf),
    range = { start = zero, ["end"] = zero },
    context = { only = { kind }, diagnostics = {} },
  }, 3000, buf)

  if not res or res.err or not res.result then return end

  for _, action in ipairs(res.result) do
    -- a server is allowed to answer with the title alone and hand over the
    -- edit only when you ask for that action by name
    if not action.edit and client:supports_method("codeAction/resolve") then
      local resolved = client:request_sync("codeAction/resolve", action, 3000, buf)
      action = (resolved and not resolved.err and resolved.result) or action
    end
    if action.edit then
      vim.lsp.util.apply_workspace_edit(action.edit, client.offset_encoding)
    end
  end
end

-- ruff returns its formatting as one edit replacing the whole document, and
-- that text ends in a newline.  Applied over a buffer whose last line had no
-- end-of-line, it leaves an empty last line, and 'fixeol' then writes a
-- newline of its own - so a file that reached us without a final newline gets
-- two on its first save.  ruff never means to end a file on a blank line, so
-- drop them and let 'fixeol' put the single newline back.
local function trim_final_blank_lines(buf)
  local last = vim.api.nvim_buf_line_count(buf)
  while last > 1 and vim.api.nvim_buf_get_lines(buf, last - 1, last, true)[1] == "" do
    last = last - 1
  end
  if last < vim.api.nvim_buf_line_count(buf) then
    vim.api.nvim_buf_set_lines(buf, last, -1, true, {})
  end
end

vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = "*.py",
  callback = function(args)
    for _, kind in ipairs(RUFF_ON_SAVE) do
      ruff_code_action(args.buf, kind)
    end
    -- saving within the moment before ruff attaches is otherwise an error
    -- message about a failed format request
    if next(vim.lsp.get_clients({ bufnr = args.buf, name = "ruff" })) then
      vim.lsp.buf.format({ bufnr = args.buf, name = "ruff", timeout_ms = 3000 })
      trim_final_blank_lines(args.buf)
    end
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
