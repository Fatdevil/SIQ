# Observability

The CV pipeline now emits OpenTelemetry spans and metrics to make it easier to spot
regressions from CI or production dashboards.

## Tracing

Every `/cv/back/analyze` invocation produces a root span named `cv.pipeline`. The
following child spans map to the major computer-vision stages and include useful
attributes on the outputs they produce:

- `cv.detect` – raw detections built from the input payload. Attributes capture how
  many ball and club boxes were provided.
- `cv.track` – tracker-specific association of detections. Attributes record the
  number of tracks generated for each object type.
- `cv.impact` – impact detection stage. Attributes include the best frame candidate
  and the confidence score for that frame.
- `cv.metrics` – downstream metric calculations. Attributes store the exact numeric
  values before rounding so downstream consumers can validate business logic.

The spans can be scraped from the existing Prometheus exporter and correlated with
request metadata via `cv.pipeline` attributes (`fps`, tracker/pose selection, etc.).

## Metrics

A histogram named `frame_inference_ms` records the per-frame processing time for the
pipeline. Each record stores the frame count that was processed to help separate
shots with truncated inputs from full swings.

Exporters that read `siq.observability.FRAME_INFERENCE_HISTOGRAM` will automatically
pick up the new instrument; no extra registration is required in the app.
