#

use `fd` instead of `find`

```bash
fd -t d -u <pattern>
  # -t d = directories only
  # -u (or --unrestricted) = don't skip hidden/gitignored paths (otherwise fd respects .gitignore by default, which might skip some dirs)
```

pipe to `du` to get size of found directories

```bash
fd -t d -u -d <depth> <pattern> | xargs du -sh
```
