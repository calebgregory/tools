#!/usr/bin/env bash
# Build swift-scribe with swiftc directly.
#
# We don't use `swift build`: with only the Command Line Tools installed (no full Xcode), SwiftPM's
# manifest compilation fails to link against its own PackageDescription library. Package.swift is
# kept for editor/Xcode use, but this script is the source of truth for building on CLT.
set -euo pipefail

cd "$(dirname "$0")"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
mkdir -p .build

xcrun swiftc -O \
    -parse-as-library \
    -target arm64-apple-macos26.0 \
    -sdk "$SDK" \
    Sources/SwiftScribe/*.swift \
    -o .build/swift-scribe

echo "built .build/swift-scribe"
