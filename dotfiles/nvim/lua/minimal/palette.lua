-- The two palettes the minimal colorscheme picks between, keyed by the value of
-- 'background'.  Both are Gruvbox medium.
--
-- Each row is one ROLE, with its dark and light value side by side, so the two
-- palettes cannot drift apart: adding a color means adding both halves of it.
-- The names say what the color is for rather than what it looks like, because
-- several of them change sides between the palettes - light-mode red is
-- #9d0006, darker than the code it sits beside, where dark-mode red is brighter
-- than it.  Same job, opposite direction.
local roles = {
  bg        = { dark = "#282828", light = "#f6f6f6" },
  bg_dim    = { dark = "#1d2021", light = "#ececec" },  -- panel / sidebar / inactive tab
  fg        = { dark = "#a89984", light = "#665c54" },  -- the base code color
  fg_bright = { dark = "#ebdbb2", light = "#282828" },  -- markdown prose, cursor, statusline
  red       = { dark = "#fb4934", light = "#9d0006" },  -- comments, invalid
  green     = { dark = "#b8bb26", light = "#79740e" },  -- strings, checked markdown checkboxes
  yellow    = { dark = "#fabd2f", light = "#b57614" },  -- definitions, control flow
  pink      = { dark = "#d3869b", light = "#8f3f71" },  -- numbers, constants
  gray      = { dark = "#928374", light = "#7c6f64" },  -- punctuation, escapes, type references
  orange    = { dark = "#d65d0e", light = "#d65d0e" },  -- markdown list markers
  orange_hi = { dark = "#fe8019", light = "#af3a03" },  -- flash jump labels
  tan       = { dark = "#bdae93", light = "#504945" },  -- markdown inline code
  diff_meta = { dark = "#d5c4a1", light = "#3c3836" },
  line_nr   = { dark = "#7c6f64", light = "#a89984" },  -- and everything else that recedes
  blue      = { dark = "#83a598", light = "#076678" },
  aqua      = { dark = "#8ec07c", light = "#427b58" },
  teal      = { dark = "#689d6a", light = "#689d6a" },
}

-- Terminals have no alpha channel, so a color meant to read as a wash over the
-- background has to be mixed into it ahead of time.
local function blend(fg, bg, alpha)
  local channel = function(offset)
    local f = tonumber(fg:sub(offset, offset + 1), 16)
    local b = tonumber(bg:sub(offset, offset + 1), 16)
    return math.floor(alpha * f + (1 - alpha) * b + 0.5)
  end
  return string.format("#%02x%02x%02x", channel(2), channel(4), channel(6))
end

local function palette(variant)
  local p = {}
  for role, pair in pairs(roles) do
    p[role] = pair[variant]
  end
  -- The washes are the same three mixes on both sides; only what they are mixed
  -- into differs, which is the whole reason they are derived rather than listed.
  return vim.tbl_extend("error", p, {
    sel         = blend(p.fg_bright, p.bg, 0.10),  -- selection, cursorline
    match       = blend(p.yellow, p.bg, 0.25),     -- search hits
    match_cur   = blend(p.yellow, p.bg, 0.50),     -- the one under the cursor
    diff_add    = blend(p.green, p.bg, 0.14),      -- a diff view's line washes
    diff_delete = blend(p.red, p.bg, 0.14),
    diff_change = blend(p.blue, p.bg, 0.14),
    diff_text   = blend(p.blue, p.bg, 0.28),       -- the span that differs, inside a changed line
  })
end

return { dark = palette("dark"), light = palette("light") }
