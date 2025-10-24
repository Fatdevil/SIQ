import Foundation

struct RuntimeConfig {
    let runtime: String
    let accelerator: String
}

struct Frame {
    let timestamp: TimeInterval
}

protocol FrameSource: AnyObject {
    func reset()
    func next() -> Frame?
}

final class InMemoryFrameSource: FrameSource {
    private var frames: [Frame]
    private var index: Int = 0

    init(frameCount: Int = 300) {
        let start = Date().timeIntervalSince1970
        frames = (0..<frameCount).map { idx in
            Frame(timestamp: start + Double(idx) * 0.033)
        }
    }

    func reset() {
        index = 0
    }

    func next() -> Frame? {
        guard index < frames.count else { return nil }
        defer { index += 1 }
        return frames[index]
    }
}

final class BenchmarkRunner {
    private let logger: MetricLogger
    private let frameSource: FrameSource

    init(logger: MetricLogger, frameSource: FrameSource) {
        self.logger = logger
        self.frameSource = frameSource
    }

    func runSweep() {
        let configs = [
            RuntimeConfig(runtime: "CoreML", accelerator: "ANE"),
            RuntimeConfig(runtime: "TFLite", accelerator: "CPU"),
        ]

        configs.forEach(run)
    }

    private func run(config: RuntimeConfig) {
        frameSource.reset()
        var latencies: [Double] = []
        var memorySamples: [Double] = []
        var frames = 0

        let start = Date()
        while let _ = frameSource.next() {
            let frameStart = Date()
            Thread.sleep(forTimeInterval: 0.010) // placeholder inference cost
            latencies.append(Date().timeIntervalSince(frameStart))
            memorySamples.append(210 + Double(frames))
            frames += 1
        }

        let elapsed = Date().timeIntervalSince(start)
        let metrics = Metrics(latencies: latencies, memory: memorySamples, frames: frames, elapsed: elapsed)
        logger.log(config: config, metrics: metrics)
    }
}

struct Metrics {
    let latencies: [Double]
    let memory: [Double]
    let frames: Int
    let elapsed: TimeInterval

    var p50: Double { percentile(0.5) }
    var p95: Double { percentile(0.95) }
    var fps: Double { elapsed > 0 ? Double(frames) / elapsed : 0 }
    var coldStart: Double { 0.120 }
    var batteryDrain: Double { max(elapsed / (15 * 60.0) * 4.0, 0.1) }
    var peakMemory: Double { memory.max() ?? 0 }

    private func percentile(_ value: Double) -> Double {
        guard !latencies.isEmpty else { return 0 }
        let sorted = latencies.sorted()
        let index = Int(Double(sorted.count - 1) * value)
        return sorted[index]
    }
}

// Convenience entry point for manual testing.
// runBenchHarness()
