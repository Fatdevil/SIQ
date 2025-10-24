# Edge Benchmark Report

This document tracks the latest export sweep and accompanying mobile benchmark
results. Numbers are illustrative placeholders that should be replaced once the
bench harnesses are executed against physical devices.

| Device            | Runtime          | p50 (ms) | p95 (ms) | FPS | Cold Start (ms) | Memory (MB) | 15-min Battery Drain (%) |
|-------------------|------------------|---------:|---------:|----:|----------------:|------------:|-------------------------:|
| Pixel 8 Pro       | TFLite CPU       | 12.3     | 18.4     | 45  | 120             | 210         | 4.2                      |
| Pixel 8 Pro       | TFLite GPU       | 8.9      | 12.1     | 55  | 150             | 240         | 4.7                      |
| Pixel 8 Pro       | TFLite NNAPI     | 7.4      | 10.2     | 58  | 180             | 250         | 4.9                      |
| Pixel 8 Pro       | NCNN CPU         | 15.2     | 21.8     | 39  | 100             | 220         | 4.0                      |
| Pixel 8 Pro       | NCNN Vulkan      | 9.1      | 13.5     | 52  | 160             | 235         | 4.5                      |
| iPhone 15 Pro     | CoreML (ANE)     | 6.8      | 9.5      | 60  | 90              | 205         | 3.8                      |
| iPhone 15 Pro     | TFLite CPU       | 11.1     | 16.7     | 47  | 130             | 215         | 4.1                      |

## Recommendation

Based on the current synthetic results, the recommended default runtimes are:

- **Android**: TFLite (delegate selected dynamically between GPU and NNAPI based
  on availability).
- **iOS**: CoreML leveraging the Apple Neural Engine.

These selections balance accuracy with predictable performance envelopes. If
future measurements diverge materially, update this report alongside the export
artifacts.
