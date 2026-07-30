import AVFoundation
import Foundation
import Speech

// On-device audio transcription for macOS 26+, built on Apple's SpeechAnalyzer / SpeechTranscriber.
// No network, no API key, no per-call cost — the local counterpart to the OpenAI-backed `cc transcribe`.
//
// CoreAudio can't decode every container we're handed (notably Opus-in-.m4a, which is what the
// voice-memo recorder produces), so inputs that AVAudioFile can't read are first normalized to a
// 16 kHz mono WAV via ffmpeg. The transcription itself is always on-device.

private nonisolated(unsafe) var verbose = false

private func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("swift-scribe: \(message)\n".utf8))
    exit(1)
}

private func log(_ message: String) {
    guard verbose else { return }
    FileHandle.standardError.write(Data("swift-scribe: \(message)\n".utf8))
}

private enum ScribeError: Error, CustomStringConvertible {
    case noCompatibleFormat
    case bufferAllocationFailed
    case ffmpegNotFound
    case ffmpegFailed(String)
    case localeUnsupported(String)

    var description: String {
        switch self {
        case .noCompatibleFormat: "no audio format compatible with the transcriber"
        case .bufferAllocationFailed: "failed to allocate an audio buffer"
        case .ffmpegNotFound: "ffmpeg not found — install it (`brew install ffmpeg`) to transcribe this format"
        case .ffmpegFailed(let stderr): "ffmpeg failed: \(stderr)"
        case .localeUnsupported(let id): "locale not supported by SpeechTranscriber: \(id)"
        }
    }
}

// MARK: - Arguments

private struct Args {
    var input: URL
    var output: URL?
    var localeID: String
    var timeout: Double
}

private func parseArgs() -> Args {
    var input: String?
    var output: String?
    var localeID = "en-US"
    var timeout = 300.0  // wall-clock ceiling; a stalled Speech asset check would otherwise hang forever

    var iterator = CommandLine.arguments.dropFirst().makeIterator()
    while let arg = iterator.next() {
        switch arg {
        case "-o", "--out", "--output":
            guard let value = iterator.next() else { fail("\(arg) requires a value") }
            output = value
        case "-l", "--locale":
            guard let value = iterator.next() else { fail("\(arg) requires a value") }
            localeID = value
        case "-t", "--timeout":
            guard let value = iterator.next(), let seconds = Double(value) else {
                fail("\(arg) requires a number of seconds")
            }
            timeout = seconds
        case "-v", "--verbose":
            verbose = true
        case "-h", "--help":
            print("usage: swift-scribe <audio-file> [-o out.txt] [--locale en-US] [--timeout 300] [-v]")
            exit(0)
        default:
            if arg.hasPrefix("-") { fail("unknown option: \(arg)") }
            guard input == nil else { fail("unexpected argument: \(arg)") }
            input = arg
        }
    }

    guard let input else { fail("missing input audio file (see --help)") }
    return Args(
        input: URL(fileURLWithPath: input),
        output: output.map { URL(fileURLWithPath: $0) },
        localeID: localeID,
        timeout: timeout
    )
}

// MARK: - Timeout

private struct TimedOut: Error, CustomStringConvertible {
    let seconds: Double
    var description: String {
        "timed out after \(Int(seconds))s (rerun with --timeout, or -v to see where it stalls)"
    }
}

// Race `operation` against a deadline. If the deadline wins, throw TimedOut; the process then exits,
// abandoning whatever blocking framework call was stuck. Guards against indefinite hangs in the
// on-device Speech stack (asset checks, XPC to the recognition daemon) that aren't cancellable.
private func withTimeout<T: Sendable>(
    _ seconds: Double,
    _ operation: @escaping @Sendable () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask { try await operation() }
        group.addTask {
            try await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
            throw TimedOut(seconds: seconds)
        }
        defer { group.cancelAll() }
        return try await group.next()!
    }
}

// MARK: - Input normalization

private func matches(_ locale: Locale, in locales: [Locale]) -> Bool {
    locales.contains { $0.identifier(.bcp47) == locale.identifier(.bcp47) }
}

private func resolveFFmpeg() -> String? {
    let candidates = ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
        + (ProcessInfo.processInfo.environment["PATH"]?
            .split(separator: ":").map { "\($0)/ffmpeg" } ?? [])
    return candidates.first { FileManager.default.isExecutableFile(atPath: $0) }
}

// Transcode any input to a 16 kHz mono PCM WAV that CoreAudio can read.
private func transcodeToWAV(_ input: URL) throws -> URL {
    guard let ffmpeg = resolveFFmpeg() else { throw ScribeError.ffmpegNotFound }

    let output = FileManager.default.temporaryDirectory
        .appendingPathComponent("swift-scribe-\(UUID().uuidString).wav")

    let process = Process()
    process.executableURL = URL(fileURLWithPath: ffmpeg)
    process.arguments = [
        "-nostdin", "-y", "-v", "error", "-i", input.path,
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output.path,
    ]
    // Detach stdin. An inherited TTY (i.e. running interactively in a terminal) makes ffmpeg read
    // keypresses from it and hang; -nostdin plus a null stdin covers both ffmpeg builds and any
    // other child that might probe stdin. Not observable when launched with a non-TTY stdin.
    process.standardInput = FileHandle.nullDevice
    let stderr = Pipe()
    process.standardError = stderr
    try process.run()
    // Drain stderr to EOF *before* waiting: readDataToEndOfFile returns when ffmpeg closes stderr
    // (i.e. exits), consuming output as it's written. Reading only after waitUntilExit() would
    // deadlock if ffmpeg filled the ~64 KB pipe buffer and blocked before we ever read it.
    let errData = stderr.fileHandleForReading.readDataToEndOfFile()
    process.waitUntilExit()

    guard process.terminationStatus == 0 else {
        let message = String(decoding: errData, as: UTF8.self)
        throw ScribeError.ffmpegFailed(message.trimmingCharacters(in: .whitespacesAndNewlines))
    }
    return output
}

// Return an audio file CoreAudio can decode, transcoding via ffmpeg when it can't read the original
// (e.g. Opus-in-.m4a, which opens with a reported length of 0). The URL is a temp file to clean up.
private func readableAudioFile(for input: URL) throws -> (file: AVAudioFile, temp: URL?) {
    if let direct = try? AVAudioFile(forReading: input), direct.length > 0 {
        return (direct, nil)
    }
    log("input not readable by CoreAudio — transcoding with ffmpeg…")
    let wav = try transcodeToWAV(input)
    return (try AVAudioFile(forReading: wav), wav)
}

// Convert one PCM buffer into the analyzer's required format (sample-rate / channel / encoding).
private func convert(
    _ buffer: AVAudioPCMBuffer,
    using converter: AVAudioConverter,
    to format: AVAudioFormat
) throws -> AVAudioPCMBuffer {
    let ratio = format.sampleRate / buffer.format.sampleRate
    let capacity = AVAudioFrameCount((Double(buffer.frameLength) * ratio).rounded(.up)) + 1024
    guard let output = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: capacity) else {
        throw ScribeError.bufferAllocationFailed
    }

    var supplied = false
    var conversionError: NSError?
    converter.convert(to: output, error: &conversionError) { _, inputStatus in
        if supplied {
            inputStatus.pointee = .noDataNow
            return nil
        }
        supplied = true
        inputStatus.pointee = .haveData
        return buffer
    }
    if let conversionError { throw conversionError }

    return output
}

// MARK: - Transcription

private func transcribe(audioFile: AVAudioFile, transcriber: SpeechTranscriber) async throws -> String {
    log("  selecting analyzer audio format…")
    guard let analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber]) else {
        throw ScribeError.noCompatibleFormat
    }
    guard let converter = AVAudioConverter(from: audioFile.processingFormat, to: analyzerFormat) else {
        throw ScribeError.noCompatibleFormat
    }

    let analyzer = SpeechAnalyzer(modules: [transcriber])
    let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()

    let collector = Task { () -> String in
        var accumulated = AttributedString()
        for try await result in transcriber.results {
            accumulated += result.text
        }
        return NSAttributedString(accumulated).string
    }

    log("  starting analyzer…")
    try await analyzer.start(inputSequence: inputSequence)

    log("  feeding audio…")
    let chunkFrames: AVAudioFrameCount = 16384
    let totalFrames = audioFile.length
    while audioFile.framePosition < totalFrames {
        let toRead = min(chunkFrames, AVAudioFrameCount(totalFrames - audioFile.framePosition))
        guard let inBuffer = AVAudioPCMBuffer(pcmFormat: audioFile.processingFormat, frameCapacity: toRead) else {
            throw ScribeError.bufferAllocationFailed
        }
        try audioFile.read(into: inBuffer, frameCount: toRead)
        if inBuffer.frameLength == 0 { break }
        inputBuilder.yield(AnalyzerInput(buffer: try convert(inBuffer, using: converter, to: analyzerFormat)))
    }

    log("  finalizing…")
    inputBuilder.finish()
    try await analyzer.finalizeAndFinishThroughEndOfInput()

    log("  collecting results…")
    return try await collector.value.trimmingCharacters(in: .whitespacesAndNewlines)
}

// MARK: - Entry point

@main
struct SwiftScribe {
    static func main() async {
        let args = parseArgs()

        guard FileManager.default.fileExists(atPath: args.input.path) else {
            fail("input file not found: \(args.input.path)")
        }

        let locale = Locale(identifier: args.localeID)
        let transcriber = SpeechTranscriber(
            locale: locale,
            transcriptionOptions: [],
            reportingOptions: [],
            attributeOptions: []
        )

        do {
            let transcript = try await withTimeout(args.timeout) {
                log("checking locale support…")
                guard matches(locale, in: await SpeechTranscriber.supportedLocales) else {
                    throw ScribeError.localeUnsupported(args.localeID)
                }
                if !matches(locale, in: await SpeechTranscriber.installedLocales) {
                    log("downloading on-device model for \(args.localeID)…")
                    if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                        try await request.downloadAndInstall()
                    }
                }

                let (audioFile, temp) = try readableAudioFile(for: args.input)
                defer { if let temp { try? FileManager.default.removeItem(at: temp) } }

                let seconds = Double(audioFile.length) / audioFile.processingFormat.sampleRate
                log("transcribing (\(String(format: "%.0f", seconds))s of audio)…")
                return try await transcribe(audioFile: audioFile, transcriber: transcriber)
            }

            if let output = args.output {
                try (transcript + "\n").write(to: output, atomically: true, encoding: .utf8)
                log("wrote \(output.path)")
            } else {
                print(transcript)
            }
        } catch {
            fail("\(error)")
        }
    }
}
