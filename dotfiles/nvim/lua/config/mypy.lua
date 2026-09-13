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
-- the process still in flight per buffer, so a superseded one can be stopped
local mypy_job = {}

local enabled = true

local function run_mypy(buf)
  if not enabled then return end

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

  -- save again while mypy is still working and its answer is already stale.
  -- Stopping it frees the CPU instead of leaving mypy to finish a reply we
  -- would only throw away; the token still guards the callback, because a
  -- killed process calls back too.
  local in_flight = mypy_job[buf]
  if in_flight then in_flight:kill("sigterm") end

  local token = (mypy_run[buf] or 0) + 1
  mypy_run[buf] = token

  mypy_job[buf] = vim.system({ mypy, "--output=json", "--no-error-summary", path },
    { cwd = root, text = true },
    vim.schedule_wrap(function(res)
      if mypy_run[buf] ~= token or not vim.api.nvim_buf_is_valid(buf) then return end
      mypy_job[buf] = nil
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

-- An augroup so that re-sourcing the config replaces these autocmds rather
-- than adding a second copy of each.
--
-- BufWritePost, not Pre: mypy reads the file off disk, so it has to be there.
-- BufReadPost as well, so that opening a file tells you what mypy makes of it
-- without your having to save first.
vim.api.nvim_create_autocmd({ "BufReadPost", "BufWritePost" }, {
  group = vim.api.nvim_create_augroup("mypy", { clear = true }),
  pattern = { "*.py", "*.pyi" },
  callback = function(args) run_mypy(args.buf) end,
})

vim.api.nvim_create_user_command("Mypy", function()
  run_mypy(vim.api.nvim_get_current_buf())
end, { desc = "Re-run mypy on this buffer, without waiting for a save" })

vim.api.nvim_create_user_command("MypyToggle", function()
  enabled = not enabled
  if enabled then
    run_mypy(vim.api.nvim_get_current_buf())
  else
    -- every buffer, not just this one: the switch is global, and leaving old
    -- errors sitting in the buffers you are not looking at would be a lie
    vim.diagnostic.reset(mypy_ns)
  end
  vim.notify(("mypy diagnostics %s"):format(enabled and "on" or "off"))
end, { desc = "Turn mypy diagnostics on or off" })
