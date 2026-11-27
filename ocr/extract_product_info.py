"""Run from project root: python -m ocr.extract_product_info INPUT OUTPUT_DIR"""
import argparse
import json
from pathlib import Path

from .product_info import extract_product_info


def main():
    parser = argparse.ArgumentParser(description="Prepare product search candidates from saved OCR JSON")
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    paths = sorted(args.input.glob("*_res.json")) if args.input.is_dir() else [args.input]
    if not paths or any(not p.is_file() for p in paths):
        parser.error("No OCR JSON file found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or "rec_texts" not in data.get("res", data):
            raise ValueError(f"Not an OCR result: {path}")
        info = extract_product_info(data)
        output = args.output_dir / (path.stem + "_product_info.json")
        if output.resolve() == path.resolve():
            raise ValueError("Output must not replace input")
        output.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.name}: {info['reason']}; candidates={info['query_candidates']}")


if __name__ == "__main__":
    main()
