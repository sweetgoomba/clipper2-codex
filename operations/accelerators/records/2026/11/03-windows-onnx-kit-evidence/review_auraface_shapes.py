"""Inspect ONNX shape consistency only; never execute or save a model."""
import argparse
import hashlib
import json
from pathlib import Path

import onnx


def inspect(model_path: Path) -> list[dict]:
    results = []
    for batch in (1, 8):
        for dynamic_output in (False, True):
            model = onnx.load(str(model_path), load_external_data=False)
            model.graph.input[0].type.tensor_type.shape.dim[0].dim_value = batch
            if dynamic_output:
                model.graph.output[0].type.tensor_type.shape.dim[0].dim_param = "batch"
            row = {"batch": batch, "output_metadata_dynamic": dynamic_output}
            try:
                inferred = onnx.shape_inference.infer_shapes(model, strict_mode=True)
                row.update(success=True, output_dims=[
                    d.dim_value if d.HasField("dim_value") else d.dim_param
                    for d in inferred.graph.output[0].type.tensor_type.shape.dim
                ])
            except onnx.shape_inference.InferenceError as exc:
                row.update(success=False, error=str(exc))
            results.append(row)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--check-results", type=Path)
    args = parser.parse_args()
    digest = hashlib.file_digest(args.model.open("rb"), "sha256").hexdigest()
    assert digest == "a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60"
    results = inspect(args.model)
    if args.check_results:
        assert results == json.loads(args.check_results.read_text())
    print(json.dumps({"onnx_version": onnx.__version__, "model_sha256": digest,
                      "model_inference_executed": False, "results": results}, indent=2))
