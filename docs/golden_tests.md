# Golden Tests

A lightweight set of goldens catches silent CV regressions in CI without requiring
full frame replays.

## Assets

Golden fixtures live in `tests/goldens/`:

- `back_analyze_metrics.json` stores the canonical scalar outputs from a
  representative `/cv/back/analyze` payload.
- `ball_path.pgm` holds an 8×8 grayscale heatmap of the tracked ball positions for
  the same payload. The ASCII PGM format keeps diffs readable.

## Validation Rules

`server/tests/test_back_analyze_endpoint.py::test_back_analyze_matches_goldens` is the
entry point. The test fails if:

- Any of the scalar metrics diverge by more than `1e-3` from the golden values.
- Any pixel in the rendered heatmap differs from the golden image. The current
  tolerance is exact equality so even one deviating pixel indicates a regression.

When the CV logic intentionally changes, update the goldens by running the helper
snippets in the test (or by re-running the script under `tests/goldens/` generation)
and commit the refreshed assets alongside the change.
