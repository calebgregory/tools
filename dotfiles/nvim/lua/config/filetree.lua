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

map("n", "<leader>e", "<cmd>NvimTreeToggle<CR>",     { desc = "Toggle file tree" })
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
--
-- The request blocks the editor until the server answers, so we only ask the
-- servers that could care: the ones whose project holds the path and, for a
-- file, whose filetypes include it.  We can't rely on the server's own
-- fileOperations filter for this, because basedpyright registers '**/*'.
-- Without the narrowing, renaming a .md file waited on every basedpyright
-- open in the monorepo in turn.
local function cares_about_rename(client, path)
  if not client:supports_method("workspace/willRenameFiles") then return false end
  if not (client.root_dir and vim.fs.relpath(client.root_dir, path)) then return false end
  -- a directory has no filetype; any server rooted above it may have imports into it
  if vim.fn.isdirectory(path) == 1 then return true end
  local filetype = vim.filetype.match({ filename = path })
  return filetype ~= nil and vim.tbl_contains(client.config.filetypes or {}, filetype)
end

local api = require("nvim-tree.api")
api.events.subscribe(api.events.Event.WillRenameNode, function(data)
  local params = { files = { {
    oldUri = vim.uri_from_fname(data.old_name),
    newUri = vim.uri_from_fname(data.new_name),
  } } }
  for _, client in ipairs(vim.lsp.get_clients()) do
    if cares_about_rename(client, data.old_name) then
      local res = client:request_sync("workspace/willRenameFiles", params, 2000)
      if res and res.result then
        vim.lsp.util.apply_workspace_edit(res.result, client.offset_encoding)
      end
    end
  end
end)
