-- The VS Code suggest widget: a popup menu that fills in as you type.  nvim
-- 0.12 does this itself - 'autocomplete' opens the menu on every keystroke and
-- fills it from the sources in 'complete' - so there is no completion plugin
-- here, and nothing to keep in step with the LSP config.
--
-- "o" is the 'omnifunc', which vim.lsp points at itself when a server attaches:
-- that is where python completions come from.  The rest are word scans over
-- text you already have open.  Order is priority - each source gets a slice of
-- a decaying timeout in the order listed, so the server answers first and the
-- word scans take what is left.  The ^N caps how many candidates a source may
-- contribute, which is what stops a big file's words from burying the server's
-- answer.
--
-- A buffer with a source of its own overrides this locally, as markdown does
-- with link destinations - see after/ftplugin/markdown.lua.
vim.o.autocomplete = true
vim.o.complete = "o,.^10,w^5,b^5"

-- "popup" is the detail window beside the menu, holding the signature and
-- docstring of the selected item, which the server fills in when you select it
-- (completionItem/resolve).
--
-- "noselect" is the one that matters for typing.  The docs for 'completeopt'
-- say 'autocomplete' turns it on for you, and it does not: without it spelled
-- out here the first item comes up selected, so pressing <Tab> at the end of a
-- word takes the completion instead of indenting.  Written out, the menu opens
-- with nothing selected and <Tab> stays a tab until you step into the list.
vim.o.completeopt = "menu,popup,fuzzy,noselect"

local map = vim.keymap.set

-- <C-n> and <C-p> step through the menu, <C-y> accepts and <C-e> dismisses,
-- all built in; <Tab> below is the second spelling of accept.  <CR> is left
-- alone: with an item selected its text is already in the buffer, so a newline
-- after it is the right thing.
map("i", "<Tab>", function()
  -- selected is -1 both when the menu is closed and when it is open with
  -- nothing highlighted, which are the two cases that want a real tab
  return vim.fn.complete_info({ "selected" }).selected ~= -1 and "<C-y>" or "<Tab>"
end, { expr = true, desc = "Accept the selected completion, else a tab" })

vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("complete", { clear = true }),
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if not client or not client:supports_method("textDocument/completion") then return end
    -- Not autotrigger: 'autocomplete' is already asking on every keystroke,
    -- through the omnifunc.  What enable() adds is the other half of an item -
    -- accepting one applies its text edits, which is how the import line for a
    -- name basedpyright completed gets written at the top of the file.
    vim.lsp.completion.enable(true, client.id, args.buf)
  end,
})
