import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import json

import pytest

from scripts import export_models
from siq.models import create_default_models


def test_export_all_creates_expected_files(tmp_path: Path) -> None:
    results = export_models.export_all(tmp_path)

    expected_files = {
        "detector.onnx",
        "detector.tflite",
        "detector.mlmodel",
        "detector.ncnn.param",
        "detector.ncnn.bin",
        "pose.onnx",
        "pose.tflite",
        "pose.mlmodel",
        "pose.ncnn.param",
        "pose.ncnn.bin",
    }

    produced_files = {p.name for p in tmp_path.iterdir()}
    assert expected_files == produced_files

    for exports in results.values():
        assert {entry.format_name for entry in exports} == set(export_models.EXPORT_FORMATS)
        for entry in exports:
            for path in entry.paths:
                assert path.exists()


def test_sanity_check_detects_modified_artifact(tmp_path: Path) -> None:
    export_models.export_all(tmp_path)

    target = tmp_path / "detector.tflite"
    data = json.loads(target.read_text())
    data["payload"]["weight"][0][0] += 0.5
    target.write_text(json.dumps(data))

    models = create_default_models()
    dummy_input = export_models.create_dummy_input(seed=1)

    with pytest.raises(export_models.ExportError):
        export_models.run_sanity_check(
            "detector",
            models["detector"],
            [target],
            "tflite",
            dummy_input,
        )


def test_compare_model_outputs_missing_key_raises() -> None:
    original = {"boxes": [[1.0, 0.5, 0.5, 0.1]]}
    exported = {"scores": [0.1]}
    with pytest.raises(export_models.ExportError):
        export_models.compare_model_outputs("detector", "onnx", original, exported)
