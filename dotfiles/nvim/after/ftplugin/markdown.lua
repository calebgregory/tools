-- nvim's own runtime ftplugin/markdown.vim sets tabstop/softtabstop/shiftwidth
-- to 4, which overrides the 2 that config.options sets globally.  This file
-- lives under after/ so it runs once that has had its say.
vim.bo.tabstop, vim.bo.softtabstop, vim.bo.shiftwidth = 2, 2, 2

-- config.keymaps binds <F12> to vim.lsp.buf.definition; no server attaches to
-- markdown, and the thing under the cursor here that has a definition is a
-- link, so the key follows it instead.
vim.keymap.set("n", "<F12>", require("markdown_links").follow,
  { buffer = true, desc = "Follow the link under the cursor" })

-- Link destinations are the only thing worth completing in markdown, so this
-- 'complete' drops every source config.complete sets and keeps one: "F", the
-- 'completefunc' below, which answers with paths inside a destination and with
-- nothing anywhere else.  The word scans that are useful in code are a
-- distraction in prose, and the "o" has nothing behind it here anyway - no
-- language server attaches to markdown.
vim.bo.completefunc = "v:lua.require'markdown_links'.complete"
vim.bo.complete = "F"

-- A checkbox is a list item, so both bullet and ordered forms count, and only
-- those: matching a bare "[x]" anywhere would rewrite footnote and link
-- references in prose.
local CHECKBOX_PATTERNS = {
  "^(%s*[-*+]%s+%[)([^%]])(%].*)$",
  "^(%s*%d+[.)]%s+%[)([^%]])(%].*)$",
}

local EMPTY = " "

local function is_done(state)
  return state:lower() == "x"
end

-- [>] reads as in progress too.  We never write it - <A-s> writes [/] - but a
-- box typed by hand as [>] should answer to the same key.
local function is_in_progress(state)
  return state == "/" or state == ">"
end

local function rewritten(line, mark, holds)
  for _, pattern in ipairs(CHECKBOX_PATTERNS) do
    local before, state, after = line:match(pattern)
    if before then
      return before .. (holds(state) and EMPTY or mark) .. after
    end
  end
  return nil
end

-- Both keys have the same shape: put the box in the key's own state, or empty
-- it when it is already in that state.  So <A-d> finishes a box from any state
-- and empties a finished one, and <A-s> does the same around in progress.
local function map_checkbox(key, mark, holds, desc)
  vim.keymap.set("n", key, function()
    local line = rewritten(vim.api.nvim_get_current_line(), mark, holds)
    if line then vim.api.nvim_set_current_line(line) end
  end, { buffer = true, desc = desc })
end

map_checkbox("<A-d>", "x", is_done,        "Checkbox on this line: done")
map_checkbox("<A-s>", "/", is_in_progress, "Checkbox on this line: in progress")
