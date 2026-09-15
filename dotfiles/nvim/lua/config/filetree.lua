local map = vim.keymap.set

require("nvim-tree").setup({
  view = { width = 36, signcolumn = "auto" },
  renderer = {
    group_empty = true,
    indent_markers = { enable = true },
    icons = { git_placement = "signcolumn" },
  },
  filters = { dotfiles = false, custom = { "^\\.git$", "^\\.venv$", "__pycache__" } },
  git = { enable = true, ignore = false },
  update_focused_file = { enable = true },  -- follow the buffer you are in
})

map("n", "<C-n>",     "<cmd>NvimTreeToggle<CR>",     { desc = "Toggle file tree" })
map("n", "<leader>n", "<cmd>NvimTreeFindFile<CR>",   { desc = "Reveal current file in tree" })

-- nvim-tree renames the file itself and tells no one.  Before it does, ask any
-- server that implements workspace/willRenameFiles (basedpyright does; upstream
-- pyright does not) for the import edits and apply them.  The edited buffers
-- are left modified, not written - follow a rename with :wa.
--
-- basedpyright's finder only rewrites the last dotted component of a module
-- path, so this covers renaming a module or a package directory in place.
-- Moving either to a different directory produces no edits, and renaming
-- __init__.py is skipped by the server (DetachHead/basedpyright#1888, #498).
local api = require("nvim-tree.api")
api.events.subscribe(api.events.Event.WillRenameNode, function(data)
  local params = { files = { {
    oldUri = vim.uri_from_fname(data.old_name),
    newUri = vim.uri_from_fname(data.new_name),
  } } }
  for _, client in ipairs(vim.lsp.get_clients()) do
    if client:supports_method("workspace/willRenameFiles") then
      local res = client:request_sync("workspace/willRenameFiles", params, 2000)
      if res and res.result then
        vim.lsp.util.apply_workspace_edit(res.result, client.offset_encoding)
      end
    end
  end
end)
