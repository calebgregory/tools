-- :CodeDiff is the VS Code source-control view: a file panel of changed files
-- with status, a side-by-side diff whose right pane is the editable working
-- tree, and staging from the panel (- toggles a file, S / U stage or unstage
-- everything).
local map = vim.keymap.set

require("gitsigns").setup({
  signs = {
    add = { text = "+" }, change = { text = "~" },
    delete = { text = "_" }, topdelete = { text = "‾" }, changedelete = { text = "~" },
  },
  on_attach = function(buf)
    local gs = require("gitsigns")
    local function m(lhs, rhs, desc)
      map("n", lhs, rhs, { buffer = buf, desc = desc })
    end
    m("]h", function() gs.nav_hunk("next") end, "Next hunk")
    m("[h", function() gs.nav_hunk("prev") end, "Previous hunk")
    m("<leader>hs", gs.stage_hunk,        "Stage hunk")
    m("<leader>hr", gs.reset_hunk,        "Reset hunk")
    m("<leader>hp", gs.preview_hunk,      "Preview hunk")
    m("<leader>hb", gs.blame_line,        "Blame line")
    m("<leader>hd", gs.diffthis,          "Diff this file")
  end,
})

-- one command with subcommands; `:CodeDiff <Tab>` also completes git revs and
-- ranges, so `:CodeDiff main...` reviews just this branch's work
map("n", "<leader>gs", "<cmd>CodeDiff<CR>",         { desc = "Source control (changed files)" })
map("n", "<leader>gh", "<cmd>CodeDiff history<CR>", { desc = "File history" })
map("n", "<leader>gm", "<cmd>CodeDiff main...<CR>", { desc = "Review this branch against main" })
map("n", "<leader>gp", "<cmd>CodeDiff pr<CR>",      { desc = "Review a pull request" })
