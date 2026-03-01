# call-recordings

iOS 18 introduced native call recording. Recordings are saved into the Notes app. The problem: iOS will not let you share or export call recordings that exceed a certain length. The share sheet simply fails or never appears. This is a [known issue](https://apple.stackexchange.com/questions/477767/unable-to-share-export-call-recordings-from-notes-app) with no fix from Apple.

The workaround: back up your iPhone locally to your Mac, then extract the recordings from the backup.

## how it works

An iPhone backup stores every file under a content-addressed hash in `Manifest.db`. The call recordings live in the Notes domain (`AppDomainGroup-group.com.apple.notes`), but not as the `.m4a` files you might expect — those are 0-duration stubs. The actual audio is stored as `moments_*-audio.MOV` files typed as `public.mpeg-4-audio`.

`extract.py` queries `NoteStore.sqlite` (the Notes database inside the backup) to find audio attachments with real duration, resolves them back to files in the backup via `Manifest.db`, and copies them out with friendly names derived from the note title and creation date.

## multi-track audio

The extracted files contain two separate audio streams — one per speaker. Media players mix them for playback, so they sound fine. But tools like transcription APIs typically only read the first stream (your mic), silently dropping the other speaker.

To merge both streams into a single mono track before transcribing:

```bash
merge-audio-tracks recording.m4a recording_merged.m4a
```

(see [`merge-audio-tracks`](../../bin/merge-audio-tracks))

## usage

1. Back up your iPhone to your Mac (Finder > iPhone > "Back up all data").
2. Update `.secret` with the path to your backup if needed.
3. Run: `./run.sh ~/Documents/call-recordings`
