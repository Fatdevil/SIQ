# Back-view v1 Overview

The back-view analysis pipeline powers `/cv/back/analyze` and exposes ball speed, club speed, side angle, and carry estimates for SoccerIQ.

## Tracker adapter

* Env flag: `GOLFIQ_TRACKER={bytetrack|norfair|identity}` (`bytetrack` default).
* ByteTrack adapter keeps IDs through brief occlusion. Norfair prioritises responsiveness with lightweight smoothing. Identity assigns per detection IDs (useful for debugging).
* Synthetic unit tests cover ID stability across missed frames.

## Impact + Metrics

* Impact detection picks the frame with maximum club/ball overlap and checks separation in the next frame to build confidence.
* Ball speed uses Δs/Δt with calibrated meters-per-pixel (`ref_len_m` and `ref_len_px`).
* Club speed samples the two frames leading into impact.
* Side angle is calculated from the first and last tracked ball centers.
* Carry uses the MVP drag model: `carry = (v * α_v * (1 - drag))^2 * sin(2θ) / g` with defaults α_v=0.82, drag=0.015.
* Quality flags: fps (>=90), shutter (<=1500 µs), ref-length present, tracking (non-empty tracks).
* Accuracy regression targets (synthetic): ball speed ±3%, side angle ±1.5°, carry MAPE ≤12 m.

## Pose MVP

* Adapters: Mediapipe (default) and MoveNet fallback via `GOLFIQ_POSE` env var.
* Pose summary returns shoulder/pelvis tilt and backswing:downswing tempo ratio.
* Static pose fixtures hold tilt within ±2°.

## API contract

`POST /cv/back/analyze` expects JSON:

```json
{
  "fps": 120,
  "shutter_us": 800,
  "ref_len_m": 1.0,
  "ref_len_px": 100.0,
  "ball": [{"frame": 0, "bbox": [0,0,10,10]}],
  "club": [{"frame": 0, "bbox": [0,0,10,10]}],
  "pose": [{"frame": 0, "keypoints": [{"name": "left_shoulder", "x": 0, "y": 0}]}]
}
```

It returns:

```json
{
  "ballSpeedMps": 45.123,
  "clubSpeedMps": 32.987,
  "sideAngleDeg": 5.12,
  "carryEstM": 185.4,
  "quality": {"fps": true, "shutter": true, "ref_len": true, "tracking": true},
  "sourceHints": {
    "tracker": "bytetrack",
    "pose": "mediapipe",
    "impactFrame": "12",
    "cvSource": "mock",
    "tempoRatio": "3.00",
    "shoulderTiltDeg": "10.00",
    "pelvisTiltDeg": "9.50"
  }
}
```

`x-cv-source` header allows tagging `mock` vs `real` captures.

## UI

`web/` hosts a lightweight SPA card with a ghost overlay to preview results.
