-- render-markdown.nvim draws markdown in place: headings, bullets, checkboxes,
-- tables and code blocks get icons and backgrounds instead of raw syntax.  It
-- only draws in normal mode, and the line under the cursor shows its raw text,
-- so editing still happens on the source.
--
-- The plugin knows [ ] and [x] and, by default, [-].  after/ftplugin/markdown.lua
-- writes [/] for in progress and answers to a hand-typed [>] too, so both get
-- the same icon here; without these they would render as plain text.
local IN_PROGRESS = { rendered = "󰥔 ", highlight = "RenderMarkdownTodo" }

require("render-markdown").setup({
  checkbox = {
    custom = {
      in_progress       = vim.tbl_extend("force", IN_PROGRESS, { raw = "[/]" }),
      in_progress_arrow = vim.tbl_extend("force", IN_PROGRESS, { raw = "[>]" }),
    },
  },
})
