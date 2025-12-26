# <https://immich.app>

tools for working with images imported from my camera + uploading them to our
self-hosted-on-home-network immich app.

assumes use of `mise.toml` from dotfiles, which manages python, node, pnpm versions.

in addition to those,

```sh
brew install ffmpeg
```

needs to've happened.  i tried and failed to install it using `mise`.

## workflow

```sh
mise stage                        # 1 - move to a "stage dir", look through and delete the bad ones
mise move "$album_dir"            # 2 - move the good ones to an album_dir
mise stabilize-720p "$album_dir"  # 2.5 - if videos are in play, stabilize and resize them
mise upload "$album_dir"          # 3 - upload album to immich app server
```
