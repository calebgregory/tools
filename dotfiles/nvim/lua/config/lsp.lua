-- One server per project root.  root_markers resolves to the NEAREST ancestor
-- holding a pyproject.toml, so apps/unified-asset gets its own server rather
-- than inheriting the repo root and dragging in all ~100 projects.
vim.lsp.config("basedpyright", {
  cmd = { "basedpyright-langserver", "--stdio" },
  filetypes = { "python" },
  root_markers = { "pyproject.toml" },
  -- typeCheckingMode "off" leaves hover, go-to-definition, references and
  -- rename - which is what basedpyright is here for - and stops it reporting
  -- type errors.  pyrefly owns those, because pyrefly is what CI enforces: two
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
    -- A file with no pyproject.toml above it starts the server in single-file
    -- mode with no root, so there is no project venv to look for.
    if not client.root_dir then return end
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

-- The monorepo installs ruff and pyrefly once, in the repo-root venv, while
-- each project underneath gets a venv without them.  Walk from the server's
-- root up to the repo root and take the first venv that has the tool, so the
-- editor runs the version the project pins rather than whatever mise has on
-- PATH.  The two disagree about more than bug fixes: ruff 0.16 put the whole UP
-- set in its default selection, so a newer global ruff rewrites annotations the
-- repo's own ruff says nothing about, and CI and the editor stop agreeing.
local function venv_tool(root_dir, name)
  if not root_dir then return nil end
  local repo_root = vim.fs.root(root_dir, ".git")
  local dir = root_dir
  while dir do
    local bin = dir .. "/.venv/bin/" .. name
    if vim.uv.fs_stat(bin) then return bin end
    if dir == repo_root then return nil end
    -- dirname("/") is "/", which is the only way out of the walk when the file
    -- is not in a git repo at all
    local parent = vim.fs.dirname(dir)
    dir = parent ~= dir and parent or nil
  end
end

-- server name -> root_dir -> the binary that root's server actually started
-- with, so :LspRoots can answer "which ruff is this buffer being linted by"
-- without guessing
local server_bins = { ruff = {}, pyrefly = {} }

vim.lsp.config("ruff", {
  cmd = function(dispatchers, config)
    local ruff = venv_tool(config.root_dir, "ruff") or "ruff"
    -- "-" is the key :LspRoots looks up for a rootless client
    server_bins.ruff[config.root_dir or "-"] = ruff
    return vim.lsp.rpc.start({ ruff, "server" }, dispatchers)
  end,
  filetypes = { "python" },
  root_markers = { "pyproject.toml" },
  on_attach = function(client)
    -- pyrefly owns hover; two servers answering is just noise
    client.server_capabilities.hoverProvider = false
  end,
})

-- Each project's [tool.pyrefly] names its own python-interpreter-path, so
-- pyrefly finds the project venv from its config and needs none of the
-- on_init venv plumbing basedpyright does.
vim.lsp.config("pyrefly", {
  cmd = function(dispatchers, config)
    local pyrefly = venv_tool(config.root_dir, "pyrefly") or "pyrefly"
    server_bins.pyrefly[config.root_dir or "-"] = pyrefly
    return vim.lsp.rpc.start({ pyrefly, "lsp" }, dispatchers)
  end,
  filetypes = { "python" },
  root_markers = { "pyproject.toml" },
})

-- basedpyright stays configured above but off: pyrefly answers hover,
-- definitions, references and rename as well as type errors.  Run
-- :lua vim.lsp.enable("basedpyright") to bring it back alongside.
vim.lsp.enable({ "pyrefly", "ruff" })

vim.api.nvim_create_user_command("LspRoots", function()
  for _, c in ipairs(vim.lsp.get_clients()) do
    local root = c.root_dir or "-"
    local bin = server_bins[c.name] and server_bins[c.name][root] or nil
    print(string.format("%-14s %-56s %s",
      c.name, vim.fn.fnamemodify(root, ":~"), bin and vim.fn.fnamemodify(bin, ":~") or ""))
  end
end, { desc = "List active servers, their roots, and which ruff and pyrefly each one runs" })
