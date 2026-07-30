// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "swift-scribe",
    platforms: [.macOS("26.0")],
    targets: [
        .executableTarget(
            name: "SwiftScribe",
            path: "Sources/SwiftScribe"
        )
    ]
)
