from __future__ import annotations

import subprocess
from pathlib import Path

GOLDEN = Path("tests/goldens/upgrade_screen.html")
SCRIPT = Path("tests/scripts/render_upgrade_screen.mjs")


def test_upgrade_screen_snapshot() -> None:
    result = subprocess.run(
        ["node", SCRIPT.as_posix()],
        check=True,
        capture_output=True,
    )

    actual = result.stdout.decode("utf-8").strip()
    expected = GOLDEN.read_text(encoding="utf-8").strip()
    assert actual == expected
