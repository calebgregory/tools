-- CriticMarkup in markdown buffers: tracked changes and comments written in the
-- text itself.
--
--   {++added++}  {--deleted--}  {~~old~>new~~}  {==highlighted==}  {>>comment<<}
--
-- Relay, the Obsidian plugin, writes a comment as a block that carries its
-- author: "{{", attributes such as author="Caleb", ">>", the comment, "<<}}".
-- We don't write a whole one out here, because lemonaid's comment watcher would
-- take it for a real comment on this file.
--
-- A comment written directly after a mark belongs to it, as the spec has it,
-- and every comment directly after that one, of either kind, joins the same
-- thread as a reply.
--
-- We draw each mark with extmarks and conceal its delimiters, so the delimiters
-- disappear only where 'conceallevel' allows it - render-markdown raises it
-- while it renders and drops it back when you turn rendering off.  The comment
-- panel lists every comment beside the buffer.  Moving through the panel lights
-- up the text a comment is about.
--
-- We scan the raw text, not the treesitter tree, so markup inside a code span or
-- a fenced block is drawn as markup too.

local M = {}

local ns = vim.api.nvim_create_namespace("critic")
local focus_ns = vim.api.nvim_create_namespace("critic_focus")
local panel_ns = vim.api.nvim_create_namespace("critic_panel")

-- Above treesitter (100) and the extmark default (4096), so our colors win over
-- the markup ones.  GFM reads {~~old~>new~~} as strikethrough, for one.
local PRIORITY = 5000

local PANEL_WIDTH = 50

local RELAY_OPENER = "{{"
local RELAY_CLOSER = "<<}}"

local KIND_BY_MARK = {
  ["+"] = "addition", ["-"] = "deletion", ["~"] = "substitution",
  ["="] = "highlight", [">"] = "comment",
}
local CLOSER_BY_MARK = {
  ["+"] = "++}", ["-"] = "--}", ["~"] = "~~}", ["="] = "==}", [">"] = "<<}",
}
local GROUP_BY_KIND = {
  addition = "CriticAddition", deletion = "CriticDeletion",
  highlight = "CriticHighlight", comment = "CriticComment",
}

-- Defaults only: a colorscheme that sets these groups wins, and colors/minimal.lua
-- does.  Run again on ColorScheme, because :hi clear drops them.
local function define_default_highlights()
  local deleted = vim.api.nvim_get_hl(0, { name = "DiffDelete", link = false })
  deleted.strikethrough = true
  deleted.default = true
  vim.api.nvim_set_hl(0, "CriticDeletion", deleted)
  vim.api.nvim_set_hl(0, "CriticAddition", { link = "DiffAdd", default = true })
  vim.api.nvim_set_hl(0, "CriticHighlight", { link = "Search", default = true })
  vim.api.nvim_set_hl(0, "CriticComment", { link = "Comment", default = true })
  vim.api.nvim_set_hl(0, "CriticAuthor", { link = "Title", default = true })
  vim.api.nvim_set_hl(0, "CriticDelimiter", { link = "NonText", default = true })
  vim.api.nvim_set_hl(0, "CriticFocus", { link = "IncSearch", default = true })
end

define_default_highlights()
vim.api.nvim_create_autocmd("ColorScheme", {
  group = vim.api.nvim_create_augroup("critic_colors", { clear = true }),
  callback = define_default_highlights,
})

-- ── Parsing ──────────────────────────────────────────────────────────
-- Offsets are 0-based bytes into the buffer's lines joined with "\n"; `stop`
-- and `body_stop` are exclusive.  `sep` is where a substitution's "~>" starts.
--
-- A thread is a run of comments with no text between them, and the mark they
-- follow, if any: { anchor = mark or nil, comments = { ... }, start, stop }.
-- Each comment and its anchor point back at it with `.thread`.

-- A CriticMarkup item, or nil when the opener at `s` has no closer.
local function parse_critic(text, s, e, mark)
  local close_s = text:find(CLOSER_BY_MARK[mark], e + 1, true)
  if not close_s then return nil end
  local item = {
    kind = KIND_BY_MARK[mark],
    start = s - 1, stop = close_s + 2,
    body_start = e, body_stop = close_s - 1,
  }
  if item.kind == "substitution" then
    local sep = text:find("~>", e + 1, true)
    if not sep or sep > close_s then return nil end
    item.sep = sep - 1
  end
  return item
end

-- A Relay comment, or nil when the "{{" at `s` does not start one.  The header
-- has to sit on one line with no "}" in it, so a {{ template }} is left alone.
local function parse_relay(text, s)
  local header_start = s + #RELAY_OPENER
  local arrows = text:find(">>", header_start, true)
  if not arrows then return nil end
  local header = text:sub(header_start, arrows - 1)
  if header:find("[\n}]") then return nil end
  local close_s = text:find(RELAY_CLOSER, arrows + 2, true)
  if not close_s then return nil end
  return {
    kind = "comment",
    author = header:match('author="([^"]*)"'),
    start = s - 1, stop = close_s + #RELAY_CLOSER - 1,
    body_start = arrows + 1, body_stop = close_s - 1,
  }
end

local function parse(text)
  local items, threads = {}, {}
  local pos = 1
  while true do
    local s, e, mark = text:find("{([-+~=>])%1", pos)
    local relay_s = text:find(RELAY_OPENER, pos, true)
    local relay_comes_first = relay_s and (not s or relay_s < s)
    if not (s or relay_s) then break end

    local item
    if relay_comes_first then
      item = parse_relay(text, relay_s)
      pos = relay_s + 1
    else
      item = parse_critic(text, s, e, mark)
      pos = e + 1
    end
    if not item then goto continue end

    if item.kind == "comment" then
      local previous = items[#items]
      local follows_previous = previous and previous.stop == item.start
      local thread
      if follows_previous and previous.kind == "comment" then
        thread = previous.thread
      else
        local anchor = follows_previous and previous or nil
        thread = { anchor = anchor, comments = {}, start = (anchor or item).start }
        if anchor then anchor.thread = thread end
        threads[#threads + 1] = thread
      end
      thread.comments[#thread.comments + 1] = item
      thread.stop = item.stop
      item.thread = thread
    end

    items[#items + 1] = item
    pos = item.stop + 1
    ::continue::
  end
  return items, threads
end

-- state_by_buf[buf] = { text, line_starts, items, threads, refresh_tick }
local state_by_buf = {}

local function line_starts_of(lines)
  local starts, offset = {}, 0
  for i, line in ipairs(lines) do
    starts[i] = offset
    offset = offset + #line + 1
  end
  return starts
end

-- 0-based row and byte column of an offset.
local function to_pos(line_starts, offset)
  local lo, hi = 1, #line_starts
  while lo < hi do
    local mid = math.floor((lo + hi + 1) / 2)
    if line_starts[mid] <= offset then lo = mid else hi = mid - 1 end
  end
  return lo - 1, offset - line_starts[lo]
end

local function body_text(st, from, to)
  return st.text:sub(from + 1, to)
end

-- ── Drawing ──────────────────────────────────────────────────────────

local function set_mark(buf, st, from, to, opts)
  local sr, sc = to_pos(st.line_starts, from)
  local er, ec = to_pos(st.line_starts, to)
  opts.end_row, opts.end_col = er, ec
  opts.priority = opts.priority or PRIORITY
  vim.api.nvim_buf_set_extmark(buf, ns, sr, sc, opts)
end

local function draw(buf, st)
  vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)
  local delimiter = { hl_group = "CriticDelimiter", conceal = "" }
  for _, item in ipairs(st.items) do
    set_mark(buf, st, item.start, item.body_start, vim.deepcopy(delimiter))
    set_mark(buf, st, item.body_stop, item.stop, vim.deepcopy(delimiter))
    if item.kind == "substitution" then
      set_mark(buf, st, item.body_start, item.sep, { hl_group = "CriticDeletion" })
      set_mark(buf, st, item.sep, item.sep + 2, { hl_group = "CriticDelimiter", conceal = "→" })
      set_mark(buf, st, item.sep + 2, item.body_stop, { hl_group = "CriticAddition" })
    else
      set_mark(buf, st, item.body_start, item.body_stop, { hl_group = GROUP_BY_KIND[item.kind] })
    end
  end
end

-- ── Comment panel ────────────────────────────────────────────────────
-- One panel at a time.  It follows the markdown buffer you are in, and stays on
-- the last one when you move to a buffer of another type.

local panel = { buf = nil, win = nil, source = nil, thread_by_row = {} }

local function panel_is_open()
  return panel.win ~= nil and vim.api.nvim_win_is_valid(panel.win)
end

local function one_line(s)
  return (s:gsub("%s*\n%s*", " "))
end

-- What the panel shows for the text a thread is about.
local function anchor_text(st, item)
  if item.kind == "substitution" then
    return one_line(body_text(st, item.body_start, item.sep)) .. " → "
      .. one_line(body_text(st, item.sep + 2, item.body_stop))
  end
  local prefix = ({ addition = "+ ", deletion = "- " })[item.kind] or ""
  return prefix .. one_line(body_text(st, item.body_start, item.body_stop))
end

--   L12  the text the thread is about
--     Caleb: the comment
--     Claude: a reply
local function draw_panel()
  local st = state_by_buf[panel.source]
  if not (panel_is_open() and st) then return end

  local lines, hls, thread_by_row = {}, {}, {}
  local function add_line(line, thread)
    lines[#lines + 1] = line
    thread_by_row[#lines] = thread
  end
  local function add_hl(col_start, col_end, group)
    hls[#hls + 1] = { row = #lines - 1, col_start = col_start, col_end = col_end, group = group }
  end

  for _, thread in ipairs(st.threads) do
    local label = ("L%d"):format(to_pos(st.line_starts, thread.start) + 1)
    if thread.anchor then
      add_line(label .. "  " .. anchor_text(st, thread.anchor), thread)
      -- a substitution has two colors in the source; its header takes the highlight's
      add_hl(#label + 2, #lines[#lines], GROUP_BY_KIND[thread.anchor.kind] or "CriticHighlight")
    else
      add_line(label, thread)
    end
    add_hl(0, #label, "LineNr")

    for _, comment in ipairs(thread.comments) do
      local author = comment.author and (comment.author .. ": ") or ""
      local body_lines = vim.split(body_text(st, comment.body_start, comment.body_stop), "\n")
      add_line("  " .. author .. body_lines[1], thread)
      if author ~= "" then add_hl(2, 2 + #author, "CriticAuthor") end
      -- a comment's later lines sit further in than its first, as its wrapped
      -- lines do ('breakindentopt'), so a paragraph never reads as a new comment
      for i = 2, #body_lines do
        add_line(body_lines[i] == "" and "" or ("    " .. body_lines[i]), thread)
      end
    end
    lines[#lines + 1] = ""
  end
  if #lines == 0 then lines = { "No comments in this buffer." } end

  vim.bo[panel.buf].modifiable = true
  vim.api.nvim_buf_set_lines(panel.buf, 0, -1, false, lines)
  vim.bo[panel.buf].modifiable = false
  panel.thread_by_row = thread_by_row

  vim.api.nvim_buf_clear_namespace(panel.buf, panel_ns, 0, -1)
  for _, hl in ipairs(hls) do
    vim.api.nvim_buf_set_extmark(panel.buf, panel_ns, hl.row, hl.col_start,
      { end_col = hl.col_end, hl_group = hl.group })
  end
end

local function source_win()
  local win = vim.fn.bufwinid(panel.source)
  return win ~= -1 and win or nil
end

local function clear_focus()
  if panel.source and vim.api.nvim_buf_is_valid(panel.source) then
    vim.api.nvim_buf_clear_namespace(panel.source, focus_ns, 0, -1)
  end
end

local function thread_under_panel_cursor()
  return panel.thread_by_row[vim.api.nvim_win_get_cursor(panel.win)[1]]
end

local function focus_thread_under_panel_cursor()
  clear_focus()
  local thread = thread_under_panel_cursor()
  local st = state_by_buf[panel.source]
  if not (thread and st) then return end

  -- Only the text the thread is about: lighting up the comments as well buries
  -- the text under a block of color.  A thread with no mark is about a point,
  -- so it gets a marker there instead.
  local anchor = thread.anchor
  local sr, sc = to_pos(st.line_starts, anchor and anchor.body_start or thread.start)
  local er, ec = to_pos(st.line_starts, anchor and anchor.body_stop or thread.start)
  local focus = anchor
    and { end_row = er, end_col = ec, hl_group = "CriticFocus" }
    or { virt_text = { { "◆", "CriticFocus" } }, virt_text_pos = "inline" }
  focus.priority = PRIORITY + 1
  vim.api.nvim_buf_set_extmark(panel.source, focus_ns, sr, sc, focus)

  local win = source_win()
  if not win then return end
  vim.api.nvim_win_call(win, function()
    local out_of_view = sr + 1 < vim.fn.line("w0") or er + 1 > vim.fn.line("w$")
    if out_of_view then
      vim.fn.winrestview({ topline = math.max(1, sr + 1 - math.floor(vim.api.nvim_win_get_height(0) / 3)) })
    end
  end)
end

local function jump_to_thread_under_panel_cursor()
  local thread = thread_under_panel_cursor()
  local st = state_by_buf[panel.source]
  local win = source_win()
  if not (thread and st and win) then return end
  local row, col = to_pos(st.line_starts, thread.start)
  vim.api.nvim_set_current_win(win)
  vim.api.nvim_win_set_cursor(win, { row + 1, col })
end

local function close_panel()
  if panel_is_open() then vim.api.nvim_win_close(panel.win, true) end
end

local function open_panel(source)
  local return_to = vim.api.nvim_get_current_win()
  vim.cmd(("botright vertical %dnew"):format(PANEL_WIDTH))
  panel.win, panel.buf, panel.source = vim.api.nvim_get_current_win(), vim.api.nvim_get_current_buf(), source

  vim.bo[panel.buf].buftype = "nofile"
  vim.bo[panel.buf].bufhidden = "wipe"
  vim.bo[panel.buf].swapfile = false
  vim.bo[panel.buf].filetype = "criticpanel"
  vim.api.nvim_buf_set_name(panel.buf, "critic://comments")
  for option, value in pairs({
    wrap = true, linebreak = true, breakindent = true, breakindentopt = "shift:2",
    number = false, relativenumber = false, signcolumn = "no", winfixwidth = true,
    cursorline = true, list = false,
  }) do
    vim.wo[panel.win][option] = value
  end

  vim.keymap.set("n", "<cr>", jump_to_thread_under_panel_cursor,
    { buffer = panel.buf, desc = "Critic: jump to this comment" })
  vim.keymap.set("n", "q", close_panel, { buffer = panel.buf, desc = "Critic: close the panel" })

  local group = vim.api.nvim_create_augroup("critic_panel", { clear = true })
  vim.api.nvim_create_autocmd("CursorMoved", {
    group = group, buffer = panel.buf, callback = focus_thread_under_panel_cursor,
  })
  vim.api.nvim_create_autocmd("BufLeave", { group = group, buffer = panel.buf, callback = clear_focus })
  vim.api.nvim_create_autocmd("BufWipeout", {
    group = group, buffer = panel.buf,
    callback = function()
      clear_focus()
      panel.buf, panel.win, panel.thread_by_row = nil, nil, {}
    end,
  })

  draw_panel()
  vim.api.nvim_set_current_win(return_to)
end

function M.toggle_panel()
  if panel_is_open() then close_panel() else open_panel(vim.api.nvim_get_current_buf()) end
end

-- ── Keeping up with edits ────────────────────────────────────────────

local function refresh(buf)
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  local st = state_by_buf[buf]
  st.text = table.concat(lines, "\n")
  st.line_starts = line_starts_of(lines)
  st.items, st.threads = parse(st.text)
  draw(buf, st)
  if panel.source == buf then draw_panel() end
end

local REFRESH_DELAY_MS = 150

local function refresh_soon(buf)
  local st = state_by_buf[buf]
  st.refresh_tick = st.refresh_tick + 1
  local tick = st.refresh_tick
  vim.defer_fn(function()
    local still_latest = state_by_buf[buf] and state_by_buf[buf].refresh_tick == tick
    if still_latest and vim.api.nvim_buf_is_valid(buf) then refresh(buf) end
  end, REFRESH_DELAY_MS)
end

-- Whether the buffer has any CriticMarkup or Relay comment, for code that shares keys
-- with us (config.lsp hands lua/lma's comment keys over in such a buffer).
function M.has_comments(buf)
  local st = state_by_buf[buf == 0 and vim.api.nvim_get_current_buf() or buf]
  return st ~= nil and st.items ~= nil and #st.items > 0
end

function M.attach(buf)
  buf = buf == 0 and vim.api.nvim_get_current_buf() or buf
  if state_by_buf[buf] then return end
  state_by_buf[buf] = { refresh_tick = 0 }

  -- on_lines rather than TextChanged: it also sees edits made through the API,
  -- such as our own, which TextChanged reports only once nvim is back to waiting
  -- for keys.  The buffer detaches when it is unloaded; the ftplugin attaches
  -- it again when it is loaded.
  vim.api.nvim_buf_attach(buf, false, {
    on_lines = function()
      if not state_by_buf[buf] then return true end
      refresh_soon(buf)
    end,
    on_reload = function() refresh_soon(buf) end,
    on_detach = function() state_by_buf[buf] = nil end,
  })

  local group = vim.api.nvim_create_augroup("critic_buf_" .. buf, { clear = true })
  vim.api.nvim_create_autocmd("BufEnter", {
    group = group, buffer = buf,
    callback = function()
      if panel_is_open() and panel.source ~= buf then
        clear_focus()
        panel.source = buf
        draw_panel()
      end
    end,
  })
  vim.api.nvim_create_autocmd("BufWipeout", {
    group = group, buffer = buf,
    callback = function()
      state_by_buf[buf] = nil
      vim.api.nvim_del_augroup_by_id(group)
    end,
  })
  refresh(buf)
end

-- ── Writing and resolving marks ──────────────────────────────────────

local COMMENT_WINDOW_HEIGHT = 8
local COMMENT_WINDOW_MAX_WIDTH = 80

-- Opens a small markdown window under the cursor to write a comment in, of as
-- many lines as you like.  Writing the buffer (:w, :x, ZZ) or <C-s> adds the
-- comment; q in normal mode, or closing the window unwritten, drops it.
-- on_submit gets the text with trailing blank lines trimmed.
local function ask_for_comment(on_submit)
  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].buftype = "acwrite"
  vim.bo[buf].bufhidden = "wipe"
  vim.api.nvim_buf_set_name(buf, ("critic://new-comment-%d"):format(buf))
  vim.bo[buf].filetype = "markdown"
  local win = vim.api.nvim_open_win(buf, true, {
    relative = "cursor", row = 1, col = 0,
    width = math.min(COMMENT_WINDOW_MAX_WIDTH, vim.o.columns - 4),
    height = COMMENT_WINDOW_HEIGHT,
    border = "rounded", style = "minimal",
    title = " Comment · :w adds it, q drops it ", title_pos = "center",
  })
  vim.wo[win].wrap, vim.wo[win].linebreak = true, true

  local submitted = false
  local function submit()
    if submitted then return end
    submitted = true
    local text = table.concat(vim.api.nvim_buf_get_lines(buf, 0, -1, false), "\n"):gsub("%s+$", "")
    vim.bo[buf].modified = false
    -- Closing later, not here: :x and ZZ quit the current window right after
    -- the write, and if we had closed ours that would be the document's.
    vim.schedule(function()
      if vim.api.nvim_win_is_valid(win) then vim.api.nvim_win_close(win, true) end
      on_submit(text)
    end)
  end

  vim.api.nvim_create_autocmd("BufWriteCmd", { buffer = buf, callback = submit })
  vim.keymap.set({ "n", "i" }, "<C-s>", function()
    vim.cmd.stopinsert()
    submit()
  end, { buffer = buf, desc = "Critic: add this comment" })
  vim.keymap.set("n", "q", function() vim.api.nvim_win_close(win, true) end,
    { buffer = buf, desc = "Critic: drop this comment" })
  vim.cmd.startinsert()
end

-- Wraps the visual selection in {==…==} and, unless the comment is left empty,
-- puts {>>comment<<} after it.
function M.comment_selection()
  local mode = vim.fn.mode()
  if mode == "\22" then
    vim.notify("Critic: a block selection can't be commented; use v or V", vim.log.levels.WARN)
    return
  end
  vim.cmd("normal! \27") -- leaving visual mode is what sets '< and '>
  local buf = vim.api.nvim_get_current_buf()
  local sr, sc = unpack(vim.api.nvim_buf_get_mark(buf, "<"))
  local er, ec = unpack(vim.api.nvim_buf_get_mark(buf, ">"))
  sr, er = sr - 1, er - 1
  local end_line = vim.api.nvim_buf_get_lines(buf, er, er + 1, true)[1]
  if mode == "V" then
    sc, ec = 0, #end_line
  elseif ec < #end_line then
    ec = ec + 1 + vim.str_utf_end(end_line, ec + 1) -- '> is the last character's first byte
  else
    ec = #end_line
  end

  ask_for_comment(function(comment)
    local closer = comment == "" and "==}" or ("==}{>>" .. comment .. "<<}")
    -- the end first, so the start's position still holds
    vim.api.nvim_buf_set_text(buf, er, ec, er, ec, vim.split(closer, "\n"))
    vim.api.nvim_buf_set_text(buf, sr, sc, sr, sc, { "{==" })
  end)
end

local function item_under_cursor(st)
  local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  local offset = st.line_starts[row] + col
  for _, item in ipairs(st.items) do
    if item.start <= offset and offset < item.stop then return item end
  end
end

-- With the cursor in a thread, adds a reply at its end.  Anywhere else, puts a
-- comment that stands alone after the character under the cursor.
function M.comment_here()
  local buf = vim.api.nvim_get_current_buf()
  local st = state_by_buf[buf]
  if not st then return end
  refresh(buf) -- an edit may still be waiting on refresh_soon
  local item = item_under_cursor(st)
  local row, col
  if item and item.thread then
    row, col = to_pos(st.line_starts, item.thread.stop)
  else
    local cursor_row, cursor_col = unpack(vim.api.nvim_win_get_cursor(0))
    local line = vim.api.nvim_get_current_line()
    row = cursor_row - 1
    col = cursor_col < #line and cursor_col + 1 + vim.str_utf_end(line, cursor_col + 1) or #line
  end
  ask_for_comment(function(comment)
    if comment == "" then return end
    vim.api.nvim_buf_set_text(buf, row, col, row, col, vim.split("{>>" .. comment .. "<<}", "\n"))
  end)
end

-- The mark under the cursor, or the mark a comment under the cursor is about.
-- A comment with no mark stands for its whole thread.
local function target_under_cursor(st)
  local item = item_under_cursor(st)
  if not item or item.kind ~= "comment" then return item end
  return item.thread.anchor or item.thread
end

-- What the text becomes when the mark is accepted or rejected.  Resolving a
-- highlight either way just removes the markup, and a thread with no mark goes.
local function resolved_text(st, target, accept)
  if not target.kind then return "" end
  local body = body_text(st, target.body_start, target.body_stop)
  if target.kind == "addition" then return accept and body or "" end
  if target.kind == "deletion" then return accept and "" or body end
  if target.kind == "substitution" then
    return accept and body_text(st, target.sep + 2, target.body_stop) or body_text(st, target.body_start, target.sep)
  end
  return body
end

-- Resolves the mark under the cursor, and removes the thread about it with it.
local function resolve(accept)
  local buf = vim.api.nvim_get_current_buf()
  local st = state_by_buf[buf]
  if not st then return end
  refresh(buf) -- an edit may still be waiting on refresh_soon
  local target = target_under_cursor(st)
  if not target then
    vim.notify("Critic: no mark under the cursor", vim.log.levels.WARN)
    return
  end
  local stop = target.thread and target.thread.stop or target.stop
  local sr, sc = to_pos(st.line_starts, target.start)
  local er, ec = to_pos(st.line_starts, stop)
  vim.api.nvim_buf_set_text(buf, sr, sc, er, ec, vim.split(resolved_text(st, target, accept), "\n"))
  refresh(buf)
end

function M.accept() resolve(true) end
function M.reject() resolve(false) end

return M
