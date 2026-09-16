-- Follow the markdown link under the cursor: config.keymaps binds <F12> to
-- vim.lsp.buf.definition, and in a markdown buffer the thing under the cursor
-- that has a definition is a link.
--
-- The link comes from the markdown_inline tree rather than from matching the
-- line, so the cursor can sit anywhere in `[text](dest)` - in the label as well
-- as the destination - and a link inside a code span is correctly not one.

local M = {}

-- image is in here so that the key opens the image file when the cursor is on
-- an inline image, which is written the same way but for a leading "!"
local LINK_NODES = { inline_link = true, image = true, uri_autolink = true }

-- What looks like a link inside code is literal text.  Reaching one of these
-- before a link means the tree has settled the question, and the line-reading
-- fallback below - which cannot see code - does not get to reopen it.
local CODE_NODES = { code_span = true, fenced_code_block = true, indented_code_block = true }

-- A destination holding spaces is written <in angle brackets>, and may be
-- followed by a "title" that is not part of the path.
local function _unwrapped(destination)
  if destination:sub(1, 1) == "<" then
    return destination:match("^<(.-)>") or destination
  end
  return destination:match("^%s*(%S+)") or destination
end

local function _settling_ancestor(node)
  while node do
    if LINK_NODES[node:type()] or CODE_NODES[node:type()] then return node end
    node = node:parent()
  end
  return nil
end

-- Returns the destination, and whether the tree settled the question at all -
-- an unparsed buffer and a cursor in plain prose both leave it open.
local function _from_tree()
  local parser = vim.treesitter.get_parser(0, nil, { error = false })
  if not parser then return nil, false end
  -- The injected trees are where the links are: markdown gives a paragraph one
  -- opaque "inline" node, and markdown_inline is what breaks that up.  So parse
  -- the injections, which a buffer that has not been drawn yet has not done,
  -- and ask across them.
  parser:parse(true)

  local link = _settling_ancestor(vim.treesitter.get_node({ ignore_injections = false }))
  if not link then return nil, false end
  if CODE_NODES[link:type()] then return nil, true end

  -- an autolink is <https://...> whole, with no separate destination child
  if link:type() == "uri_autolink" then
    return vim.treesitter.get_node_text(link, 0):sub(2, -2), true
  end
  for child in link:iter_children() do
    if child:type() == "link_destination" then
      return _unwrapped(vim.treesitter.get_node_text(child, 0)), true
    end
  end
  return nil, true
end

-- The index of the "[" that opens the label ending at `close`, or nil when the
-- brackets before it do not balance.
local function _label_start(line, close)
  local depth = 0
  for i = close, 1, -1 do
    local char = line:sub(i, i)
    if char == "]" then
      depth = depth + 1
    elseif char == "[" then
      depth = depth - 1
      if depth == 0 then return i end
    end
  end
  return nil
end

-- tree-sitter-markdown does not always agree with CommonMark: a label holding a
-- matched pair of brackets, [a [b] c](dest), it reads as plain text.  So when
-- the tree has no link, read the line instead - what this finds the tree missed
-- is a link to anyone looking at it, which is the cursor's whole argument.
local function _from_line()
  local line = vim.api.nvim_get_current_line()
  local cursor = vim.api.nvim_win_get_cursor(0)[2] + 1

  local search = 1
  while true do
    local close = line:find("](", search, true)
    if not close then return nil end
    local open, shut = line:find("%b()", close + 1)
    local start = _label_start(line, close)
    if open == close + 1 and start and start <= cursor and cursor <= shut then
      return _unwrapped(line:sub(open + 1, shut - 1))
    end
    search = close + 1
  end
end

local function _decoded(text)
  return (text:gsub("%%(%x%x)", function(hex) return string.char(tonumber(hex, 16)) end))
end

local function _is_url(path)
  return path:match("^%a[%w+.%-]*:") ~= nil
end

-- Relative destinations resolve against the file that holds the link first and
-- the cwd second, and a destination with no extension gets ".md" tried too, the
-- way Obsidian and mkdocs write them.  The first candidate that exists wins;
-- when none does we hand back the first, so the caller opens an empty buffer at
-- the path the link names rather than refusing to move.
local function _resolved_path(path)
  if path:sub(1, 1) == "~" or path:sub(1, 1) == "/" then
    return vim.fs.normalize(path)
  end

  local names = vim.fn.fnamemodify(path, ":e") == "" and { path, path .. ".md" } or { path }
  local candidates = {}
  for _, dir in ipairs({ vim.fn.expand("%:p:h"), vim.uv.cwd() }) do
    for _, name in ipairs(names) do
      table.insert(candidates, vim.fs.normalize(vim.fs.joinpath(dir, name)))
    end
  end

  for _, candidate in ipairs(candidates) do
    if vim.uv.fs_stat(candidate) then return candidate end
  end
  return candidates[1]
end

-- GitHub's anchor rules, which are what a "#some-heading" fragment is written
-- against: lowercase, punctuation dropped, spaces to hyphens.
local function _slug(heading)
  return (heading:lower():gsub("[^%w%s%-]", ""):gsub("%s+", "-"))
end

local function _jump_to_heading(fragment)
  local wanted = _slug(_decoded(fragment))
  for lnum, line in ipairs(vim.api.nvim_buf_get_lines(0, 0, -1, false)) do
    -- the trailing #s are the closed ATX form, "## Heading ##"
    local heading = line:match("^#+%s+(.-)%s*#*%s*$")
    if heading and _slug(heading) == wanted then
      vim.api.nvim_win_set_cursor(0, { lnum, 0 })
      vim.cmd("normal! zz")
      return true
    end
  end
  return false
end

function M.follow()
  local destination, settled = _from_tree()
  if not destination and not settled then destination = _from_line() end
  if not destination or destination == "" then
    vim.notify("markdown: no link under the cursor", vim.log.levels.WARN)
    return
  end

  if _is_url(destination) then
    vim.ui.open(destination)
    return
  end

  -- a "#heading" with nothing before it points into this same file
  local path, fragment = destination:match("^(.-)#(.*)$")
  path = path or destination

  -- set the ' mark first, so <C-o> comes back to the link from wherever it goes
  vim.cmd("normal! m'")

  if path ~= "" then
    local target = _resolved_path(_decoded(path))
    if not vim.uv.fs_stat(target) then
      vim.notify(("markdown: %s does not exist yet; opening an empty buffer for it")
        :format(vim.fn.fnamemodify(target, ":~")), vim.log.levels.WARN)
    end
    vim.cmd.edit(vim.fn.fnameescape(target))
  end

  if fragment and fragment ~= "" and not _jump_to_heading(fragment) then
    vim.notify(("markdown: no heading in this file matches #%s"):format(fragment), vim.log.levels.WARN)
  end
end

-- The 0-based column the destination starts at, when the cursor is inside one.
-- The last "](" before the cursor opens it, and a ")" between that and the
-- cursor means the link is already closed and the cursor is past its end.
local function _destination_start(before_cursor)
  local open = nil
  local search = 1
  while true do
    local bracket = before_cursor:find("](", search, true)
    if not bracket then break end
    open, search = bracket + 2, bracket + 2
  end
  if not open or before_cursor:find(")", open, true) then return nil end
  return open - 1
end

-- Everything beside the partial name, as written: "./sub/b" offers everything
-- in ./sub, spelled with the "./sub/" still on it, because the whole
-- destination is what the popup replaces.
local function _siblings(partial)
  local dir, leaf = partial:match("^(.*/)([^/]*)$")
  dir, leaf = dir or "", leaf or partial

  local root = dir
  if dir == "" then
    root = vim.fn.expand("%:p:h")
  elseif dir:sub(1, 1) ~= "~" and dir:sub(1, 1) ~= "/" then
    root = vim.fs.joinpath(vim.fn.expand("%:p:h"), dir)
  end

  local words = {}
  for name, kind in vim.fs.dir(vim.fs.normalize(root)) do
    -- a dotfile is not what prose links to, until you start typing one
    if leaf:sub(1, 1) == "." or name:sub(1, 1) ~= "." then
      local directory = kind == "directory"
      table.insert(words, {
        word = dir .. name .. (directory and "/" or ""),
        kind = directory and "d" or "f",
      })
    end
  end
  return words
end

-- A 'completefunc' offering the paths a link destination could name, which is
-- what config.complete has to work with in a buffer no language server
-- attaches to.  after/ftplugin/markdown.lua is what puts it in 'complete'.
function M.complete(findstart, base)
  local before_cursor = vim.api.nvim_get_current_line():sub(1, vim.api.nvim_win_get_cursor(0)[2])

  if findstart == 1 then
    -- -3 leaves completion rather than offering this buffer's filenames in the
    -- middle of a sentence
    return _destination_start(before_cursor) or -3
  end

  -- a fragment is a heading in another file, not a path, so stop offering paths
  -- once one has started
  if base:find("#", 1, true) then return { words = {} } end

  local ok, words = pcall(_siblings, base)
  -- refresh, because typing a "/" moves the search into another directory and
  -- the list has to be built again
  return { words = ok and words or {}, refresh = "always" }
end

return M
