-- Minimal - a port of ~/tools/vscode/minimal-color-theme
--
-- The palette is Gruvbox Dark (medium), but the palette is not the point.  This
-- theme colors EIGHT things and leaves everything else at the base foreground,
-- following Nikita Prokopov's "Syntax highlighting is a mess".  Installing a
-- stock gruvbox would restore the palette and lose the restraint, so the bulk
-- of what follows is deliberately linking captures back to Normal.
--
-- The eight: comments, strings, escape sequences, numeric/character constants,
-- definition names, control-flow keywords, punctuation, and errors.

vim.cmd("highlight clear")
vim.g.colors_name = "minimal"
vim.o.termguicolors = true
vim.o.background = "dark"

local c = {
  bg        = "#282828",
  bg_dim    = "#1d2021",  -- panel / sidebar / inactive tab
  fg        = "#a89984",  -- editor.foreground: the base code color
  fg_bright = "#ebdbb2",  -- markdown prose, cursor, statusline
  red       = "#fb4934",  -- comments, invalid
  green     = "#b8bb26",  -- strings, checked markdown checkboxes
  yellow    = "#fabd2f",  -- definitions, control flow
  pink      = "#d3869b",  -- numbers, constants
  gray      = "#928374",  -- punctuation, escapes
  orange    = "#d65d0e",  -- markdown list markers
  orange_hi = "#fe8019",  -- flash jump labels, the one thing louder than the code
  tan       = "#bdae93",  -- markdown inline code
  diff_meta = "#d5c4a1",
  line_nr   = "#7c6f64",
  -- alpha-blended against bg, since terminals have no alpha channel
  sel       = "#3c3a36",  -- #ebdbb2 @ 10%
  match_cur = "#91722b",  -- #fabd2f @ 50%
  match     = "#5d4d29",  -- #fabd2f @ 25%
  blue      = "#83a598",
  aqua      = "#8ec07c",
  teal      = "#689d6a",
}

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
for _, group in ipairs({ "diffFile", "diffNewFile", "diffOldFile", "diffIndexLine", "diffLine" }) do
  hl(group, { fg = c.diff_meta })
end
hl("DiffAdd",    { fg = c.aqua })
hl("DiffDelete", { fg = c.red })
hl("DiffChange", { fg = c.teal })
hl("DiffText",   { fg = c.yellow, bold = true })

-- ── Diagnostics ───────────────────────────────────────────────────────
hl("DiagnosticError", { fg = c.red })
hl("DiagnosticWarn",  { fg = c.yellow })
hl("DiagnosticInfo",  { fg = c.blue })
hl("DiagnosticHint",  { fg = c.aqua })
hl("DiagnosticUnnecessary", { fg = c.line_nr })

-- ── Flash ─────────────────────────────────────────────────────────────
-- A jump label has one job: be the brightest thing on screen for the half
-- second it exists.  Dark text on solid orange, which no other group here
-- uses, so a label can never be mistaken for code.
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
