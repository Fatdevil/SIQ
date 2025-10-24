# AR Target Mode Proof-of-Concept

The AR Target PoC lets operators drop a virtual quad target onto real-world space and capture hit telemetry during range sessions. This guide covers the three supported anchoring flows, how to print the marker, and best practices for onboarding testers.

## Feature Flags

Set these environment flags before launching the mobile client:

- `AR_TARGETS=1` – master kill-switch for the feature.
- `AR_TARGETS_MODE` – anchoring strategy: `apriltag`, `image`, or `plane`.

When disabled (`AR_TARGETS=0`), the target anchoring UI does not load and the backend refuses score submissions.

## AprilTag Anchoring (Primary Flow)

1. Print the `tag36h11` marker image at 120 mm square on matte card stock.
2. Mount the marker on a rigid backing and keep it perpendicular to the ground plane.
3. Place the marker 2–3 m in front of the hitting area. Avoid glossy surfaces and ensure even lighting.
4. In the app enable `apriltag` mode. The `TargetAnchor` component listens for pose updates and will spawn the prefab once tracking quality crosses the lock threshold (lock icon lights up).

### Printing Tips

- Use a 600+ DPI printer and disable auto-scaling so the marker stays true to size.
- Trim the white border evenly; uneven borders reduce pose accuracy.
- Keep the camera at least 0.7 m away from the tag to avoid focus issues.

## Image Tracking Fallback

If AprilTag tracking is not available on the platform build:

1. Set `AR_TARGETS_MODE=image`.
2. Deploy an `ARTrackedImageManager` with a static reference image that matches the printed marker.
3. The `TargetAnchor` component will subscribe to image tracking events and place the prefab on the first tracked image.

## Plane Raycast Fallback

When neither marker flow is available:

1. Set `AR_TARGETS_MODE=plane`.
2. Ask the tester to scan the hitting area to collect plane data.
3. Tap once on a detected plane to place the target. The “Re-center” button will reposition the target at the last successful pose.

## Hit Detection and Telemetry

The `HitDetector` projects the target mesh into screen space and checks the incoming ball position stream for overlaps. On every hit:

- Particle and audio feedback play at the impact point.
- WebSocket telemetry emits `{ targetId, hitPoint2D, hitPoint3D, score }` for live dashboards.
- The score HUD totals the run score and updates the combo indicator.

## UX Checklist

- Keep the lock icon visible only when tracking quality ≥ 0.75.
- Provide a manual re-center affordance for quick recovery from drift.
- Test under indoor and outdoor lighting; verify the target stays stable for at least 30 seconds.

For further debugging, enable verbose logging in the Unity console and capture screen recordings during range sessions.
