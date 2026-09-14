-- Minimal - a port of ~/tools/vscode/minimal-color-theme
--
-- The palette is Gruvbox medium, but the palette is not the point.  This theme
-- colors EIGHT things and leaves everything else at the base foreground,
-- following Nikita Prokopov's "Syntax highlighting is a mess".  Installing a
-- stock gruvbox would restore the palette and lose the restraint, so the bulk
-- of what follows is deliberately linking captures back to Normal.
--
-- The eight: comments, strings, escape sequences, numeric/character constants,
-- definition names, control-flow keywords, punctuation, and errors.
--
-- This file says WHAT gets colored; lua/minimal/palette.lua says what color it
-- is on each background.  It reads 'background' rather than setting it, so
-- whoever sets that has to re-run this file afterwards - see
-- lua/config/appearance.lua, which is what follows the macOS system appearance.

vim.cmd("highlight clear")
vim.g.colors_name = "minimal"
vim.o.termguicolors = true

local c = require("minimal.palette")[vim.o.background]

local hl = function(group, opts) vim.api.nvim_set_hl(0, group, opts) end

-- ── Base ──────────────────────────────────────────────────────────────
hl("Normal",       { fg = c.fg, bg = c.bg })
hl("NormalFloat",  { fg = c.fg, bg = c.bg_dim })
hl("FloatBorder",  { fg = c.gray, bg = c.bg_dim })
hl("Cursor",       { fg = c.bg, bg = c.fg_bright })
hl("CursorLine",   { bg = c.sel })
hl("CursorLineNr", { fg = c.fg_bright })
hl("LineNr",       { fg = c.line_nr })
hl("Visual",       { bg = c.sel })
hl("Search",       { bg = c.match })
hl("CurSearch",    { bg = c.match_cur })
hl("IncSearch",    { bg = c.match_cur })
hl("StatusLine",   { fg = c.fg_bright, bg = c.bg })
hl("StatusLineNC", { fg = c.line_nr, bg = c.bg_dim })
hl("WinSeparator", { fg = c.bg_dim })
hl("Pmenu",        { fg = c.fg, bg = c.bg_dim })
hl("PmenuSel",     { fg = c.fg_bright, bg = c.sel })
hl("SignColumn",   { bg = c.bg })
hl("ColorColumn",  { bg = c.bg_dim })
hl("MatchParen",   { fg = c.yellow, bold = true })
hl("NonText",      { fg = c.line_nr })
hl("SpecialKey",   { fg = c.red })   -- .vimrc.after highlighted tabs red

-- ── The eight that get color ──────────────────────────────────────────
hl("Comment",            { fg = c.red })
hl("@comment",           { link = "Comment" })
hl("String",             { fg = c.green })
hl("@string",            { link = "String" })
hl("@string.regexp",     { link = "String" })
hl("@string.escape",     { fg = c.gray })
hl("Constant",           { fg = c.pink })
hl("@constant",          { link = "Constant" })
hl("@constant.builtin",  { link = "Constant" })
hl("@number",            { link = "Constant" })
hl("@number.float",      { link = "Constant" })
hl("@character",         { link = "Constant" })
hl("@boolean",           { link = "Constant" })
-- "Global definitions" (entity.name): the name where a thing is DEFINED.  A
-- reference to a type is not a definition, so annotations, constructor calls and
-- the builtins (int, str, Path) stay out of this and go gray below - otherwise
-- every `x: Path` reads as loudly as `def build`.
hl("@function",          { fg = c.yellow })
hl("@function.method",   { fg = c.yellow })
hl("@type.definition",   { fg = c.yellow })   -- see after/queries/python/highlights.scm
-- type references, at annotations and call sites
hl("@type",              { fg = c.gray })
hl("@type.builtin",      { fg = c.gray })
hl("@constructor",       { fg = c.gray })
hl("@lsp.type.class",    { fg = c.gray })
-- keyword.control.flow only; `def`, `class`, `import` stay at base
hl("@keyword.return",      { fg = c.yellow })
hl("@keyword.conditional", { fg = c.yellow })
hl("@keyword.repeat",      { fg = c.yellow })
hl("@keyword.exception",   { fg = c.yellow })
hl("Delimiter",              { fg = c.gray })
hl("@punctuation.delimiter", { fg = c.gray })
hl("@punctuation.bracket",   { fg = c.gray })
hl("@punctuation.special",   { fg = c.gray })
hl("Error",  { fg = c.red })
hl("@error", { fg = c.red })

-- ── Everything else falls back to Normal ──────────────────────────────
-- This is the theme.  Each line here is a token category that virtually every
-- other colorscheme paints and this one deliberately does not.
for _, group in ipairs({
  "Identifier", "Function", "Statement", "Conditional", "Repeat", "Label",
  "Operator", "Keyword", "Exception", "PreProc", "Include", "Define", "Macro",
  "PreCondit", "Type", "StorageClass", "Structure", "Typedef", "Special",
  "SpecialChar", "Tag", "Debug", "Title",
  "@variable", "@variable.builtin", "@variable.parameter", "@variable.member",
  "@property", "@field", "@function.call", "@function.method.call",
  "@function.builtin", "@function.macro", "@keyword", "@keyword.function",
  "@keyword.operator", "@keyword.import", "@keyword.type", "@keyword.modifier",
  "@keyword.coroutine", "@operator", "@type.qualifier", "@attribute", "@module", "@namespace", "@label", "@tag",
  "@tag.attribute", "@tag.delimiter", "@parameter", "@method", "@field.key",
}) do
  hl(group, { link = "Normal" })
end

-- ── Markdown ──────────────────────────────────────────────────────────
hl("@markup",             { fg = c.fg_bright })   -- prose reads brighter than code
hl("@markup.strong",      { bold = true })
hl("@markup.italic",      { italic = true })
hl("@markup.list",        { fg = c.orange })
-- a checked box is the one thing here that reports a state rather than marking
-- up text, so it gets the green.  Without this it inherits @markup.list and
-- reads as just another list marker; the unchecked box still does, which is
-- what we want - the color is carrying "done", not "this is a checkbox".
hl("@markup.list.checked", { fg = c.green })
hl("@markup.raw",         { fg = c.tan })
hl("@markup.raw.block",   { fg = c.tan })
hl("@markup.heading",     { fg = c.fg_bright, bold = true })
hl("@markup.link",        { fg = c.blue, underline = true })
hl("@markup.link.url",    { fg = c.gray })
hl("@markup.quote",       { fg = c.gray, italic = true })

-- ── Diff ──────────────────────────────────────────────────────────────
-- Three different things ask for colors here.  The `diff*` groups color a patch
-- READ AS TEXT, so they color the text.  Added / Changed / Removed are the mark
-- that STANDS IN for a change somewhere there is no room to show it - a gutter
-- sign, a +12/-3 count - so they are a foreground too.  DiffAdd and friends are
-- what a diff VIEW paints under whole lines, so those are background only - the
-- syntax highlighting inside a changed line has to survive the wash, and a line
-- that differs only in whitespace still has to show that it differs.
--
-- Keeping a background on these is also what keeps codediff.nvim in the right
-- half of the palette: it reads DiffAdd / DiffDelete (and DiffChange, for moved
-- blocks) for its own colors and, finding no background there, falls back to a
-- hardcoded dark navy/maroon pair that stays dark in light mode.  It derives
-- its character-level colors from these by scaling the channels, using a factor
-- it picks from 'background', so both strengths follow from these three lines.
for _, group in ipairs({ "diffFile", "diffNewFile", "diffOldFile", "diffIndexLine", "diffLine" }) do
  hl(group, { fg = c.diff_meta })
end
-- Nvim ships its own Added / Changed / Removed, and every consumer reaches them
-- before it reaches anything here: gitsigns resolves each gutter sign through
-- them, and codediff colors the explorer's insertion and deletion counts with
-- them.  Left alone they are nvim's stock pastels, which is the one place this
-- theme leaks a color it never chose.
hl("Added",   { fg = c.green })
hl("Changed", { fg = c.blue })
hl("Removed", { fg = c.red })

hl("DiffAdd",    { bg = c.diff_add })
hl("DiffDelete", { bg = c.diff_delete })
hl("DiffChange", { bg = c.diff_change })
hl("DiffText",   { bg = c.diff_text })
-- The slashes codediff draws over the filler rows that pad one pane out to the
-- other's length.  Its own default is a hardcoded #444444, which is barely
-- there against a dark background and near-black against a light one.
hl("CodeDiffFiller", { fg = c.line_nr })

-- ── Diagnostics ───────────────────────────────────────────────────────
hl("DiagnosticError", { fg = c.red })
hl("DiagnosticWarn",  { fg = c.yellow })
hl("DiagnosticInfo",  { fg = c.blue })
hl("DiagnosticHint",  { fg = c.aqua })
hl("DiagnosticUnnecessary", { fg = c.line_nr })

-- ── Flash ─────────────────────────────────────────────────────────────
-- A jump label has one job: be the loudest thing on screen for the half second
-- it exists.  Bold, in the one color nothing else in this file uses, so a label
-- can never be mistaken for code.  On a light background loud means darker and
-- more saturated, not brighter, which is why the light `orange_hi` is the
-- deeper of the two oranges rather than the lighter one.
hl("FlashLabel", { fg = c.orange_hi, bg = c.bg, bold = true })
-- The backdrop dims every character that is not a match, and flash links it to
-- Comment by default - which in this theme is red, so the whole buffer turns
-- red while you pick a label.  Gray is what "dimmed" is supposed to look like.
hl("FlashBackdrop", { fg = c.line_nr })

-- ── Terminal ──────────────────────────────────────────────────────────
vim.g.terminal_color_0,  vim.g.terminal_color_8  = c.bg,      c.gray
vim.g.terminal_color_1,  vim.g.terminal_color_9  = "#cc241d", c.red
vim.g.terminal_color_2,  vim.g.terminal_color_10 = "#98971a", c.green
vim.g.terminal_color_3,  vim.g.terminal_color_11 = "#d79921", c.yellow
vim.g.terminal_color_4,  vim.g.terminal_color_12 = "#458588", c.blue
vim.g.terminal_color_5,  vim.g.terminal_color_13 = "#b16286", c.pink
vim.g.terminal_color_6,  vim.g.terminal_color_14 = c.teal,    c.aqua
vim.g.terminal_color_7,  vim.g.terminal_color_15 = c.fg,      c.fg_bright
