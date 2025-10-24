# Android Local Detector

The Android benchmark harness can execute a local TensorFlow Lite detector on
CameraX frames. This document describes how to enable the feature, configure
hardware delegates, and collect telemetry.

## Model Placement

1. Download the `detector.tflite` binary that implements the YOLO-style model.
2. Place the file at `mobile/android/bench/app/src/main/assets/models/detector.tflite`.
   The repository includes a `README.md` placeholder in that directory; the
   binary itself must not be committed to source control.

The detector expects RGB frames letterboxed into a 320×320 tensor. The runtime
scales the live camera feed and maps bounding boxes back into source space.

## Feature Flags

Feature flags are resolved from environment variables first and then fall back to
Gradle `BuildConfig` defaults.

- `ANDROID_LOCAL_DETECTOR=1` – enables the local TensorFlow Lite pipeline.
  Set to `0` to keep using the existing remote/mock benchmark runner.
- `ANDROID_DELEGATE={cpu|gpu|nnapi}` – selects the delegate used when creating
  the TensorFlow Lite interpreter. The default is `cpu`. GPU initialization
  failures automatically fall back to CPU execution.
- `ANDROID_PERF_OVERLAY={0|1}` – toggles the in-app performance overlay
  (default `1`).
- `ANDROID_TELEMETRY_BASE_URL=https://example.siq.dev` – optional base URL for
  telemetry uploads. When non-empty, the client will POST JSON payloads to
  `<baseUrl>/telemetry`.

## Runtime Behavior

When the local detector is enabled and a model asset is present, `BenchActivity`
initializes `TfLiteDetector` and drives CameraX using `CameraXAnalyzer`. Frames
are converted from YUV to RGB, letterboxed to 320×320, and passed through the
model. Lightweight non-max suppression filters the detections, which are logged
and emitted via telemetry.

If initialization fails or the feature flag is disabled, the activity falls back
to the original remote/mock benchmark workflow (`BenchmarkRunner` +
`FrameSource`).

## Performance Overlay

The overlay is rendered by `PerfOverlayView` and summarizes the current FPS,
p50, and p95 frame latencies for the last 120 frames. It is visible only when
`ANDROID_PERF_OVERLAY` resolves to `true`.

## Telemetry Payload

Each processed frame emits a compact telemetry JSON document:

```json
{
  "timestampMs": 0,
  "device": "android",
  "buildId": "0.1",
  "localDetector": true,
  "delegate": "cpu",
  "frameLatencyMs": 12.3,
  "fps": 28.4
}
```

The payload is posted asynchronously to `<baseUrl>/telemetry` if a base URL is
configured.

## Switching Delegates

To experiment with GPU or NNAPI delegates, set `ANDROID_DELEGATE=gpu` or
`ANDROID_DELEGATE=nnapi` before launching the app. GPU delegate creation is
wrapped in a try/catch so the pipeline will continue on CPU if initialization
fails.

## Expected Performance

With a correctly provisioned `detector.tflite` model on a Pixel 7, the release
build should sustain at least 24 FPS according to the overlay metrics and logcat
output. Adjust thread counts or delegate selection as needed when profiling on
other devices.
