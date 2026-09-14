-- The colorscheme, and following the macOS system appearance into it.
--
-- macOS reports the appearance through one global default, and only when it is
-- Dark: in Light mode the key does not exist at all and `defaults` exits 1.
--
-- Setting 'background' here is also what stops nvim from guessing it.  Nvim
-- asks the terminal for its background color at startup (OSC 11) and sets
-- 'background' from the answer, then drops that autocommand at VimEnter if the
-- config set 'background' itself.  Asking macOS is the better question: it is
-- the same one wezterm answers when it picks its own scheme (dotfiles/.wezterm.lua)
-- and the same one the tmux status bar reads, so the three cannot disagree, and
-- none of it rests on an OSC 11 reply surviving the trip out through tmux.

local query = { "defaults", "read", "-g", "AppleInterfaceStyle" }

local function background_of(defaults)
  return vim.trim(defaults.stdout or "") == "Dark" and "dark" or "light"
end

local is_mac = vim.fn.has("mac") == 1

-- Elsewhere nvim's OSC 11 guess is the best available answer, so leave
-- 'background' alone and let the OptionSet handler below pick it up.  This one
-- read blocks, unlike the refresh below, so that the first frame drawn is
-- already the right one.
if is_mac then
  vim.o.background = background_of(vim.system(query, { text = true }):wait())
end

vim.cmd.colorscheme("minimal")

local group = vim.api.nvim_create_augroup("appearance", { clear = true })

-- Changing 'background' resets every highlight group to nvim's built-in
-- defaults for the new value, and does NOT re-run the colorscheme.  Without
-- this, a switch lands you on stock nvim colors rather than on the other half
-- of the palette.
--
-- The reset lands AFTER this autocommand returns, so the re-run has to wait a
-- tick.  Reapplying inline looks like it works - the colorscheme file's own
-- highlights survive, because nvim re-sources it as part of the reset - but
-- every group a PLUGIN derives on the ColorScheme event is set before the reset
-- and wiped by it, leaving the diff view and the staged gitsigns with no colors
-- at all until the next :colorscheme.  Scheduling puts the whole chain, plugins
-- included, after the reset.
vim.api.nvim_create_autocmd("OptionSet", {
  group = group,
  pattern = "background",
  callback = function()
    vim.schedule(function() vim.cmd.colorscheme("minimal") end)
  end,
})

-- Asynchronously, unlike the read at startup: these fire often enough that a
-- few blocking milliseconds each time would be felt.
local function refresh()
  vim.system(query, { text = true }, vim.schedule_wrap(function(defaults)
    local background = background_of(defaults)
    if background ~= vim.o.background then
      vim.o.background = background
    end
  end))
end

-- macOS cannot tell a terminal program that the appearance changed, so the best
-- we get is to re-read it when the window comes back to us.  tmux only forwards
-- the focus event with `set -g focus-events on`, which ~/.tmux.conf sets.
vim.api.nvim_create_autocmd({ "FocusGained", "VimResume" }, {
  group = group,
  desc = "Follow the macOS light/dark setting",
  callback = function()
    if is_mac then
      refresh()
    end
  end,
})

-- Focus alone misses the case that matters most: toggling the appearance from
-- the menu bar with nvim already in front, where nothing is ever focused or
-- unfocused and the editor sits in the wrong theme until you tab away and back.
-- So also look on a clock, at the same interval the tmux status bar uses for
-- the same reason (status-interval in ~/.tmux.conf), so the two never disagree
-- for longer than one tick.
local POLL_MS = 15000

if is_mac then
  local timer = assert(vim.uv.new_timer())
  timer:start(POLL_MS, POLL_MS, function() vim.schedule(refresh) end)

  vim.api.nvim_create_autocmd("VimLeavePre", {
    group = group,
    callback = function() timer:stop() end,
  })
end
