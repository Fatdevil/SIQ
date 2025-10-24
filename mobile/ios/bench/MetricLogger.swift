import Foundation

protocol MetricLogger {
    func log(config: RuntimeConfig, metrics: Metrics)
}

final class ConsoleMetricLogger: MetricLogger {
    func log(config: RuntimeConfig, metrics: Metrics) {
        print("[SIQBench] \(config.runtime)-\(config.accelerator) frames=\(metrics.frames) " +
              "p50=\(metrics.p50 * 1000)ms p95=\(metrics.p95 * 1000)ms fps=\(metrics.fps) " +
              "coldStart=\(metrics.coldStart * 1000)ms mem=\(metrics.peakMemory)MB drain=\(metrics.batteryDrain)%")
    }
}

func runBenchHarness(logger: MetricLogger = ConsoleMetricLogger(), frameSource: FrameSource = InMemoryFrameSource()) {
    let runner = BenchmarkRunner(logger: logger, frameSource: frameSource)
    runner.runSweep()
}
