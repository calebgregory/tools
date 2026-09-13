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
