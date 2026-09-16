-- Find and replace across a search, which is the half config.find does not
-- cover: <leader>R and <leader>fG find the matches, <M-q> inside fzf sends them
-- to the quickfix list, and :Replace rewrites them.
--
-- The quickfix list in the middle is the point.  It is what you can look at
-- before anything is written, and what you can cut down first - a rename that
-- should skip two of its forty matches is an fzf multi-select rather than a
-- cleverer pattern.
--
-- vim.lsp.buf.rename (<leader>rn) is the better tool when it can answer at all.
-- It cannot here: basedpyright is rooted at the nearest pyproject.toml and has
-- never loaded the other ~99 projects, so it renames within one of them.  This
-- is text, and text does not care where a project ends.

local M = {}

-- One (buffer, line) pair however many matches the search put on it: ripgrep
-- reports a line once per match, and the substitution below already takes every
-- match on the line it runs on.
local function _lines_in_quickfix()
  local seen, targets = {}, {}
  for _, entry in ipairs(vim.fn.getqflist()) do
    local key = entry.bufnr .. ":" .. entry.lnum
    if entry.valid == 1 and entry.bufnr > 0 and entry.lnum > 0 and not seen[key] then
      seen[key] = true
      table.insert(targets, { buf = entry.bufnr, lnum = entry.lnum })
    end
  end
  return targets
end

local function _plural(count, singular, plural)
  return ("%d %s"):format(count, count == 1 and singular or plural)
end

local function _match_count(line, pattern)
  local count, from = 0, 0
  while true do
    local start = vim.fn.match(line, pattern, from)
    if start < 0 then return count end
    local stop = vim.fn.matchend(line, pattern, from)
    count = count + 1
    -- a pattern can match the empty string, and then matchend is where match
    -- was; step over it rather than sit there
    from = stop > start and stop or start + 1
  end
end

-- What the replacement would do, worked out but not applied, so that the count
-- you are asked to confirm is the count you get.
local function _plan(targets, pattern, replacement)
  local plan = { edits = {}, matches = 0, files = {}, file_count = 0 }
  for _, target in ipairs(targets) do
    vim.fn.bufload(target.buf)
    local line = vim.api.nvim_buf_get_lines(target.buf, target.lnum - 1, target.lnum, false)[1]
    local found = line and _match_count(line, pattern) or 0
    if found > 0 then
      table.insert(plan.edits, {
        buf = target.buf,
        lnum = target.lnum,
        text = vim.fn.substitute(line, pattern, replacement, "g"),
      })
      plan.matches = plan.matches + found
      if not plan.files[target.buf] then
        plan.files[target.buf] = true
        plan.file_count = plan.file_count + 1
      end
    end
  end
  return plan
end

local function _apply(plan)
  for _, edit in ipairs(plan.edits) do
    vim.api.nvim_buf_set_lines(edit.buf, edit.lnum - 1, edit.lnum, false, { edit.text })
  end
  for buf in pairs(plan.files) do
    -- noautocmd, so that renaming a name in forty files does not also run
    -- format-on-save and mypy over forty files - see config.format and
    -- config.mypy.  The write is the rename and nothing else; the files that
    -- were already unformatted stay that way.
    --
    -- silent, because forty "written" messages is a "Press ENTER" prompt.  The
    -- count below is the report.
    vim.api.nvim_buf_call(buf, function() vim.cmd("silent noautocmd update") end)
  end
end

-- \C because 'ignorecase' is on: without it a rename of "patient" would rewrite
-- "Patient" too, and write the lowercase replacement over it.  \< \> because a
-- name is a word, which is also what ripgrep searched for under <leader>R.
local function _pattern_for(word)
  return word == "" and "" or ([[\C\<%s\>]]):format(vim.fn.escape(word, [==[\/.*$^~[]]==]))
end

function M.over_quickfix()
  local targets = _lines_in_quickfix()
  if #targets == 0 then
    vim.notify("replace: the quickfix list is empty - search with <leader>R or <leader>fG, then <M-q>",
      vim.log.levels.WARN)
    return
  end

  vim.ui.input({ prompt = "Find (vim pattern): ", default = _pattern_for(vim.fn.expand("<cword>")) },
    function(pattern)
      if not pattern or pattern == "" then return end
      vim.ui.input({ prompt = "Replace with: " }, function(replacement)
        if not replacement then return end

        local plan = _plan(targets, pattern, replacement)
        if plan.matches == 0 then
          vim.notify(("replace: %s matches nothing on the %d lines in the quickfix list")
            :format(pattern, #targets), vim.log.levels.WARN)
          return
        end

        local scope = ("%s on %s in %s"):format(
          _plural(plan.matches, "match", "matches"),
          _plural(#plan.edits, "line", "lines"),
          _plural(plan.file_count, "file", "files"))
        if vim.fn.confirm("Replace " .. scope .. "?", "&Replace\n&Cancel", 2) ~= 1 then return end

        _apply(plan)
        vim.notify("replace: " .. scope .. ", written without the save hooks")
      end)
    end)
end

vim.api.nvim_create_user_command("Replace", M.over_quickfix,
  { desc = "Find and replace over the quickfix list" })

vim.keymap.set("n", "<leader>rr", M.over_quickfix,
  { desc = "Replace across the quickfix list" })

return M
