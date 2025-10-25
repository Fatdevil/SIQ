from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


SCRIPT = Path("tests/scripts/user_access_engine.mjs")


@pytest.mark.parametrize("scenario", ["success", "error"])
def test_user_access_engine_transitions(scenario: str) -> None:
    subprocess.run(
        ["node", SCRIPT.as_posix(), scenario],
        check=True,
        capture_output=True,
    )
