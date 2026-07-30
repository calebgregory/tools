# swift-scribe

On-device audio transcription for macOS 26+, built on Apple's [`SpeechAnalyzer` /
`SpeechTranscriber`](https://developer.apple.com/documentation/speech/speechanalyzer) API — the
same engine behind Voice Memos / Notes transcription. Fully offline, no API key, no per-call cost.
It's the local counterpart to the OpenAI-backed `cc transcribe`.

## Requirements

- macOS 26+ on Apple Silicon, with the Command Line Tools (`xcode-select --install`)
- [`ffmpeg`](https://ffmpeg.org) on `PATH` — used to decode formats CoreAudio can't read directly
  (notably Opus-in-`.m4a`, which is what the voice-memo recorder produces). Compatible inputs
  (WAV, AAC/`.m4a`, etc.) skip this step. `brew install ffmpeg`.

## Build & install

```sh
./build.sh
ln -sf "$PWD/.build/swift-scribe" ~/.local/bin/swift-scribe
```

`build.sh` compiles with `swiftc` directly rather than `swift build` — see the comment in that file
for why (SwiftPM manifest linking is broken under Command Line Tools without full Xcode).

## Usage

```sh
swift-scribe path/to/audio.m4a                 # transcript to stdout
swift-scribe path/to/audio.m4a -o out.txt      # transcript to a file
swift-scribe path/to/audio.m4a --locale en-US  # override locale (default en-US)
swift-scribe path/to/audio.m4a -v              # verbose progress on stderr
```

The first run for a given locale downloads that locale's on-device model once (then cached by the
system).
