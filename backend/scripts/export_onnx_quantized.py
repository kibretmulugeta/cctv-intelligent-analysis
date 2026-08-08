"""
Model Optimization Utility Script.
Converts PyTorch YOLO model weights (.pt) to ONNX format with INT8 / FP16 quantization for production speedups.

Usage:
    python backend/scripts/export_onnx_quantized.py --model yolo11n.pt --format onnx --quantize int8
"""
import argparse
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def export_and_quantize(model_name: str = "yolo11n.pt", quant_type: str = "int8") -> str:
    """Exports PyTorch YOLO weights to ONNX and applies quantization."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("Ultralytics is required. Install with: pip install ultralytics")
        sys.exit(1)

    logger.info(f"Loading PyTorch YOLO model: {model_name}...")
    model = YOLO(model_name)

    # Step 1: Export PyTorch to ONNX
    logger.info("Exporting model to ONNX format...")
    onnx_path = model.export(format="onnx", dynamic=True, simplify=True)
    logger.info(f"PyTorch model successfully exported to ONNX: {onnx_path}")

    # Step 2: Apply INT8 Quantization if ONNX Runtime is installed
    if quant_type.lower() == "int8":
        try:
            import onnx
            from onnxruntime.quantization import quantize_dynamic, QuantType

            quantized_path = str(Path(onnx_path).with_name(f"{Path(model_name).stem}_int8.onnx"))
            logger.info(f"Applying INT8 quantization to ONNX model -> {quantized_path}...")

            quantize_dynamic(
                model_input=onnx_path,
                model_output=quantized_path,
                weight_type=QuantType.QUInt8,
            )
            logger.info(f"INT8 Quantized ONNX model created successfully: {quantized_path}")
            return quantized_path

        except ImportError:
            logger.warning("onnxruntime.quantization not available. Skipping INT8 quantization step.")
            return str(onnx_path)

    return str(onnx_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PyTorch YOLO weights to Quantized ONNX format.")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="Path to PyTorch model weights")
    parser.add_argument("--quantize", type=str, choices=["none", "int8"], default="int8", help="Quantization type")
    args = parser.parse_args()

    out_file = export_and_quantize(args.model, args.quantize)
    print(f"\nFinal Optimized Model: {out_file}")
