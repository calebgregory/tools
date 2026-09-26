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

-- permalink to the current line (or visual range) at HEAD. HEAD must be pushed
-- for the link to resolve on github.
local function git(dir, ...)
  local out = vim.system({ "git", "-C", dir, ... }, { text = true }):wait()
  if out.code ~= 0 then return nil end
  return vim.trim(out.stdout)
end

local function github_permalink(first, last)
  local file = vim.api.nvim_buf_get_name(0)
  local dir = vim.fs.dirname(file)
  local remote = git(dir, "remote", "get-url", "origin")
  local sha = git(dir, "rev-parse", "HEAD")
  local prefix = git(dir, "rev-parse", "--show-prefix")
  if not (remote and sha and prefix) then
    vim.notify("not in a git repo with an origin remote", vim.log.levels.WARN)
    return
  end
  -- git@github.com:owner/repo.git and https://github.com/owner/repo(.git)
  local repo = remote:match("github%.com[:/](.-)%.git$") or remote:match("github%.com[:/](.-)/?$")
  if not repo then
    vim.notify("origin is not a github remote: " .. remote, vim.log.levels.WARN)
    return
  end
  local lines = first == last and ("L" .. first) or ("L" .. first .. "-L" .. last)
  local url = ("https://github.com/%s/blob/%s/%s%s#%s")
    :format(repo, sha, prefix, vim.fs.basename(file), lines)
  vim.fn.setreg("+", url)
  vim.notify(url)
end

map("n", "<leader>gy", function()
  local line = vim.fn.line(".")
  github_permalink(line, line)
end, { desc = "Copy github permalink to line" })
map("x", "<leader>gy", function()
  local a, b = vim.fn.line("v"), vim.fn.line(".")
  github_permalink(math.min(a, b), math.max(a, b))
end, { desc = "Copy github permalink to selection" })
