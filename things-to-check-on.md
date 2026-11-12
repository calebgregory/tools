# Things to check on

Workarounds we carry for bugs that are fixed upstream but not yet in a release we use. Check each one from
time to time, and when the fix ships, remove the workaround and its entry here.

## nvim drops pyrefly's file-watch events

Added 2026-11-11, on nvim 0.12.6.

pyrefly registers its file watchers with a `baseUri` that ends in `/`. nvim 0.12 matches each path against
`baseUri .. "/" .. pattern`, so no path matches and pyrefly never hears about new modules. We strip the
trailing slash in the pyrefly config — [workaround](dotfiles/nvim/lua/config/lsp.lua).

Upstream master fixed this in a rewrite of
[`runtime/lua/vim/lsp/_watchfiles.lua`](https://github.com/neovim/neovim/blob/master/runtime/lua/vim/lsp/_watchfiles.lua),
which now strips the slash with `gsub('/$', '')`.

To check: after upgrading nvim, look for that `gsub` in the installed copy:

```sh
grep -nF "gsub('/\$', '')" "$(nvim --headless -c 'echo $VIMRUNTIME' -c q 2>&1)/lua/vim/lsp/_watchfiles.lua"
```

When it is there, delete `_strip_base_uri_trailing_slash` and the `handlers` line from the pyrefly config.
