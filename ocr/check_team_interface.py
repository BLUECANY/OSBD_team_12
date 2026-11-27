"""Offline inspection: python -m ocr.check_team_interface INPUT OUTPUT_DIR"""
import argparse
import json
from pathlib import Path

from .team_interface import inspect_ocr_result


def main():
    parser = argparse.ArgumentParser(description="Convert saved OCR JSON to the team draft contract")
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    paths = sorted(args.input.glob("*_res.json")) if args.input.is_dir() else [args.input]
    if not paths or any(not path.is_file() for path in paths):
        parser.error("No saved OCR JSON found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        result = inspect_ocr_result(data)
        output = args.output_dir / (path.stem + "_team.json")
        if output.resolve() == path.resolve():
            raise ValueError("Output cannot replace input")
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path.name)
        print(json.dumps(result["fields"], ensure_ascii=False))
        print("review:", result["product_name_candidates"])


if __name__ == "__main__":
    main()
