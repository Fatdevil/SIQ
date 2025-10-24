# iOS Edge Benchmark Harness

The Swift harness mirrors the Android implementation by replaying a sequence of
frames and executing CoreML (ANE) and TFLite delegates. Runtime integration is
stubbed so developers can plug in the real pipelines without impacting the main
codebase.

## Structure

- `BenchHarness.swift` – entry point that drives the metric collection loop.
- `MetricLogger.swift` – lightweight protocol and console logger.

The harness keeps state in-process to remain tooling agnostic. To run it:

1. Open the folder in Xcode 15 or newer.
2. Embed the file inside a new iOS App project.
3. Wire in the exported models and replace the placeholder predictors with the
   production implementations.
4. Observe metrics in the Xcode console or hook up a custom logger.

All runtime-specific logic is behind protocol boundaries to simplify testing and
future expansion.
