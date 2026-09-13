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

vim.api.nvim_create_user_command("LspRoots", function()
  for _, c in ipairs(vim.lsp.get_clients()) do
    print(string.format("%-14s %s", c.name, vim.fn.fnamemodify(c.root_dir or "-", ":~")))
  end
end, { desc = "List active servers and their roots" })
