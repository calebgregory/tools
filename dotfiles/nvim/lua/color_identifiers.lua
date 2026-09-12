-- Color identifiers by name, the way the VS Code and Emacs color-identifiers
-- modes do: every occurrence of `patient_id` is one color, every occurrence of
-- `claim_id` another, so you track a value by hue instead of by reading.
--
-- Written rather than installed.  markid is the neovim plugin for this, but it
-- is a nvim-treesitter *module* (`require'nvim-treesitter.configs'.setup`), and
-- the module system is gone in nvim-treesitter's main branch.  None of its five
-- forks fixed that.
--
-- This pairs with colors/minimal.lua by design.  That theme leaves @variable at
-- the base foreground because coloring by *kind* is noise; this colors by
-- *identity*, which is the part worth seeing.  So it fills a slot the theme
-- deliberately left empty instead of fighting it.

local M = {}

local ns = vim.api.nvim_create_namespace("color_identifiers")

-- Hues evenly spaced at S=0.58 L=0.69, chosen so that the minimum pairwise
-- CIELAB deltaE is 19.4 (comfortably distinguishable) while every entry stays
-- at least 10.3 from the colors minimal.lua already assigns to comments,
-- strings, definitions, constants and punctuation - an identifier should never
-- read as a string.  Contrast against #282828 is >= 4.5:1 throughout.
local PALETTE = {
  "#de9382", "#deca82", "#bbde82", "#84de82", "#82deb7",
  "#82cdde", "#8296de", "#a582de", "#dc82de", "#de82a9",
}

local GROUPS = {}
for i, hex in ipairs(PALETTE) do
  GROUPS[i] = "ColorIdent" .. i
  vim.api.nvim_set_hl(0, GROUPS[i], { fg = hex })
end

-- FNV-1a, so a name maps to the same color in every buffer and every session.
--
-- The prime is split as 16777619 == 2^24 + 403 rather than multiplied directly.
-- Lua numbers are doubles, and `hash * 16777619` runs past 2^53 and silently
-- drops the low bits, which wrecks the distribution - measured over 66k real
-- identifiers from this monorepo, the direct form put 1,893 names in the
-- thinnest bucket and 11,510 in the fattest (chi2 33,517).  Multiplying by a
-- power of two only moves the exponent, so it stays exact at any magnitude, and
-- `hash * 403` never exceeds 2^41.  Split this way: 6,550 to 6,745, chi2 5.3.
local function group_for(name)
  local hash = 2166136261
  for i = 1, #name do
    hash = bit.bxor(hash, name:byte(i)) % 4294967296
    hash = (hash * 403 + (hash * 16777216) % 4294967296) % 4294967296
  end
  return GROUPS[(hash % #PALETTE) + 1]
end

-- Which identifiers get an identity color.
--
-- The language's own highlights query has already classified every node, so we
-- read that rather than keeping a table of node types in sync by hand.  In
-- python it separates `Widget` the class (type), `Widget()` the construction
-- (constructor), `helper` the definition (function), `normalize()` the call
-- (function.call), `self.render()` (function.method.call) and `@decorator`
-- (attribute) from the plain variables - none of which should take an identity
-- color, because a name that denotes a function is not a value you track.
local COLOR_CAPTURES = {
  ["variable"] = true,
  ["variable.parameter"] = true,
  ["variable.member"] = true,
  -- variable.builtin is deliberately absent: `self` appears in every method and
  -- carries no identity worth tracking
}

local enabled = true

-- marks placed on the last redraw; `:lua =require('color_identifiers').marks`
-- is the quickest way to tell whether this is actually running
M.marks = 0

-- A decoration provider runs per visible line, so cost scales with the window
-- rather than with the file.  That matters in this monorepo: some modules are
-- thousands of lines and we only ever pay for what is on screen.
local function on_win(_, _, bufnr, toprow, botrow)
  -- reset before the early returns, so the count reads 0 when this is off
  -- rather than keeping the last number it happened to reach
  M.marks = 0
  if not enabled or not vim.b[bufnr].color_identifiers then return false end
  local ok, parser = pcall(vim.treesitter.get_parser, bufnr)
  if not ok or not parser then return false end

  parser:for_each_tree(function(tree, ltree)
    local query = vim.treesitter.query.get(ltree:lang(), "highlights")
    if not query then return end
    -- A highlights query captures the same range more than once: a broad
    -- `(identifier) @variable` pattern matches first, then narrower patterns
    -- refine it - `build` arrives as variable, then function, then
    -- function.method.  Later captures win in treesitter's own highlighter, so
    -- only the last one per range says what the node really is.  Testing the
    -- first would color every function and class name, since everything starts
    -- out as @variable.
    local final = {}
    for id, node in query:iter_captures(tree:root(), bufnr, toprow, botrow + 1) do
      local srow, scol, erow, ecol = node:range()
      if srow == erow then
        final[srow .. ":" .. scol .. ":" .. ecol] = { query.captures[id], srow, scol, ecol }
      end
    end

    for _, e in pairs(final) do
      if COLOR_CAPTURES[e[1]] then
        local name = vim.api.nvim_buf_get_text(bufnr, e[2], e[3], e[2], e[4], {})[1]
        if name and #name > 0 then
          vim.api.nvim_buf_set_extmark(bufnr, ns, e[2], e[3], {
            end_col = e[4],
            hl_group = group_for(name),
            priority = 200,  -- above treesitter's default 100
            ephemeral = true,
          })
          M.marks = M.marks + 1
        end
      end
    end
  end)
  return false
end

function M.setup(opts)
  opts = opts or {}
  local filetypes = opts.filetypes or { "python", "lua" }

  vim.api.nvim_set_decoration_provider(ns, { on_win = on_win })

  vim.api.nvim_create_autocmd("FileType", {
    pattern = filetypes,
    callback = function(args) vim.b[args.buf].color_identifiers = true end,
  })

  vim.api.nvim_create_user_command("ColorIdentifiersToggle", function()
    enabled = not enabled
    vim.cmd.redraw({ bang = true })
    vim.notify("color identifiers: " .. (enabled and "on" or "off"))
  end, { desc = "Toggle per-name identifier colors" })
end

return M
