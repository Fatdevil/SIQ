# Android Edge Benchmark Harness

This module houses a minimal CameraX replay benchmark tailored for evaluating
SIQ's edge runtimes. The implementation is intentionally lightweight and avoids
runtime dependencies so that developers can plug in the actual media pipeline as
needed.

## Project Layout

```
mobile/android/bench/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle.properties
└── app/
    ├── build.gradle.kts
    └── src/main/java/com/siq/bench/
        ├── BenchActivity.kt
        ├── BenchmarkRunner.kt
        ├── FrameSource.kt
        └── metrics/MetricLogger.kt
```

The harness replays a short camera clip, executing inference across TFLite
(CPU/GPU/NNAPI) and NCNN (CPU/Vulkan) backends. Metrics are aggregated via a
pluggable `MetricLogger` that can later be replaced with production telemetry.

## Usage

1. Open the module in Android Studio (Giraffe+ recommended).
2. Replace `FrameSource` with an implementation that streams recorded frames
   (e.g. `MediaCodec` surface or `ImageReader` buffers).
3. Hook up the actual detector/pose pipelines inside `BenchmarkRunner`.
4. Deploy to a device and inspect the logcat output for latency, FPS, cold start,
   memory, and synthetic battery drain estimates.

The included Kotlin sources should compile without modification once the proper
runtime dependencies (TFLite and NCNN AARs) are added to the `app` module.
