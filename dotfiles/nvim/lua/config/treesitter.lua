-- Parsers install on demand, the first time a buffer of that filetype opens.
-- nvim-treesitter's install is otherwise a command you have to remember, and
-- a fresh clone of this config is silently unhighlighted until you run it -
-- which reads as a broken colorscheme rather than a missing parser.
--
-- nvim bundles c, lua, markdown, markdown_inline, query, vim and vimdoc, and
-- language.add() finds those before we get here, so leaving them in the list
-- costs nothing: on-demand means we only ever compile what nvim does not
-- already ship.  A blanket install at startup would instead build a second
-- copy of each and shadow the bundled one, because nvim-treesitter's
-- get_installed() reads only its own install dir.
local PARSERS = { "python", "lua", "bash", "json", "yaml", "toml", "markdown",
                  "markdown_inline", "sql", "dockerfile", "diff", "gitcommit" }

local function ts_start(buf, lang)
  vim.treesitter.start(buf, lang)
  vim.bo[buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
end

-- One install per language however many buffers ask for it.  `nvim *.py`
-- fires FileType once per file, and each would otherwise start its own
-- identical compile.
local installing = {}

local function install_then_start(buf, lang)
  local task = installing[lang]
  if not task then
    vim.notify(("treesitter: installing the %s parser"):format(lang))
    task = require("nvim-treesitter").install(lang)
    installing[lang] = task
  end
  -- install() is async, so this buffer is open and long past its FileType
  -- event by the time the parser lands.  Start it from here instead of making
  -- you reopen the file.
  task:await(vim.schedule_wrap(function(err)
    installing[lang] = nil
    if err then
      vim.notify(("treesitter: could not install %s: %s"):format(lang, err), vim.log.levels.WARN)
    elseif vim.api.nvim_buf_is_valid(buf) and vim.treesitter.language.add(lang) then
      ts_start(buf, lang)
    end
  end))
end

vim.api.nvim_create_autocmd("FileType", {
  callback = function(args)
    local lang = vim.treesitter.language.get_lang(args.match)
    if not lang then return end
    if vim.treesitter.language.add(lang) then
      ts_start(args.buf, lang)
    elseif vim.list_contains(PARSERS, lang) then
      install_then_start(args.buf, lang)
    end
  end,
})

vim.api.nvim_create_user_command("TSInstallAll", function()
  require("nvim-treesitter").install(PARSERS)
end, { desc = "Install every parser up front, rather than waiting for a buffer" })
