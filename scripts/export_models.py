"""Export lightweight SIQ models to multiple edge runtimes.

The export routine serializes pure-Python reference models into predictable file
layouts that mimic ONNX, TFLite, CoreML, and NCNN artefacts. While the outputs
are JSON placeholders, the module performs deterministic inference sanity checks
so format regressions surface immediately.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from siq.models import create_default_models, load_model_from_payload

EXPORT_FORMATS: Sequence[str] = ("onnx", "tflite", "coreml", "ncnn")
DEFAULT_OUTPUT_DIR = Path("build/edge_exports")
DUMMY_INPUT_SHAPE = (1, 32, 32, 3)


@dataclass
class ModelExportResult:
    model_name: str
    format_name: str
    paths: List[Path]


class ExportError(RuntimeError):
    """Raised when an export sanity check fails."""


def create_dummy_input(seed: int = 2024) -> List[List[List[List[float]]]]:
    rng = random.Random(seed)
    batch, height, width, channels = DUMMY_INPUT_SHAPE
    tensor: List[List[List[List[float]]]] = []
    for _ in range(batch):
        rows: List[List[List[float]]] = []
        for _ in range(height):
            row: List[List[float]] = []
            for _ in range(width):
                row.append([rng.random() for _ in range(channels)])
            rows.append(row)
        tensor.append(rows)
    return tensor


def _write_json(path: Path, payload: MutableMapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def _export_standard_format(model_name: str, format_name: str, payload: Mapping[str, object], output_dir: Path) -> List[Path]:
    extension = {
        "onnx": ".onnx",
        "tflite": ".tflite",
        "coreml": ".mlmodel",
    }[format_name]
    target = output_dir / f"{model_name}{extension}"
    _write_json(target, {"format": format_name, "model_name": model_name, "payload": payload})
    return [target]


def _export_ncnn(model_name: str, payload: Mapping[str, object], output_dir: Path) -> List[Path]:
    param_path = output_dir / f"{model_name}.ncnn.param"
    bin_path = output_dir / f"{model_name}.ncnn.bin"
    _write_json(param_path, {"magic": "ncnn", "model_name": model_name})
    _write_json(bin_path, {"format": "ncnn", "model_name": model_name, "payload": payload})
    return [param_path, bin_path]


def export_model(model_name: str, model: object, output_dir: Path, formats: Iterable[str], dummy_input: List[List[List[List[float]]]]) -> List[ModelExportResult]:
    payload = model.to_payload()  # type: ignore[attr-defined]
    results: List[ModelExportResult] = []
    for fmt in formats:
        if fmt in {"onnx", "tflite", "coreml"}:
            paths = _export_standard_format(model_name, fmt, payload, output_dir)
        elif fmt == "ncnn":
            paths = _export_ncnn(model_name, payload, output_dir)
        else:
            raise ValueError(f"Unsupported export format '{fmt}'")
        run_sanity_check(model_name, model, paths, fmt, dummy_input)
        results.append(ModelExportResult(model_name=model_name, format_name=fmt, paths=paths))
    return results


def load_exported_model(model_name: str, format_name: str, paths: Sequence[Path]):
    if format_name == "ncnn":
        bin_path = next(path for path in paths if path.suffix == ".bin")
        data = json.loads(bin_path.read_text())
    else:
        export_path = paths[0]
        data = json.loads(export_path.read_text())
    payload = data["payload"]
    return load_model_from_payload(model_name, payload)


def compare_model_outputs(model_name: str, format_name: str, original: Mapping[str, object], exported: Mapping[str, object]) -> None:
    for key, original_value in original.items():
        if key not in exported:
            raise ExportError(f"Missing output '{key}' for {model_name} ({format_name})")
        exported_value = exported[key]
        original_flat = list(_flatten(original_value))
        exported_flat = list(_flatten(exported_value))
        if len(original_flat) != len(exported_flat):
            raise ExportError(f"Shape mismatch for '{key}' in model '{model_name}' ({format_name})")
        for idx, (lhs, rhs) in enumerate(zip(original_flat, exported_flat)):
            if not _is_close(lhs, rhs):
                raise ExportError(
                    f"Value mismatch for '{key}'[{idx}] in model '{model_name}' ({format_name}): {lhs} vs {rhs}"
                )


def _flatten(value: object) -> Iterable[float]:
    if isinstance(value, list):
        for item in value:
            yield from _flatten(item)
    else:
        yield float(value)


def _is_close(lhs: float, rhs: float, *, rtol: float = 1e-5, atol: float = 1e-6) -> bool:
    diff = abs(lhs - rhs)
    return diff <= atol + rtol * max(abs(lhs), abs(rhs), 1.0)


def run_sanity_check(
    model_name: str,
    model: object,
    paths: Sequence[Path],
    format_name: str,
    dummy_input: List[List[List[List[float]]]],
) -> None:
    original_outputs = model.forward(dummy_input)  # type: ignore[attr-defined]
    exported_model = load_exported_model(model_name, format_name, paths)
    exported_outputs = exported_model.forward(dummy_input)  # type: ignore[attr-defined]
    compare_model_outputs(model_name, format_name, original_outputs, exported_outputs)


def export_all(output_dir: Path | str, formats: Sequence[str] | None = None) -> Dict[str, List[ModelExportResult]]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    selected_formats = tuple(formats) if formats else EXPORT_FORMATS
    dummy_input = create_dummy_input()

    results: Dict[str, List[ModelExportResult]] = {}
    for model_name, model in create_default_models().items():
        print(f"[export] Exporting {model_name} -> {', '.join(selected_formats)}")
        results[model_name] = export_model(model_name, model, target_dir, selected_formats, dummy_input)
    return results


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where export artifacts should be written.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=list(EXPORT_FORMATS),
        help="Subset of formats to export.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    export_all(args.output_dir, args.formats)
    print(f"[export] Artifacts written to {args.output_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
