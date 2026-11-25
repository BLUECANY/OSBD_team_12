import sys
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    device="cpu",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)


input_path = sys.argv[1] if len(sys.argv) > 1 else "samples/general_ocr_002.png"
output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/ocr_demo"

for result in ocr.predict(input_path):
    result.print()
    result.save_to_img(output_dir)
    result.save_to_json(output_dir)

print(f"완료: {output_dir}")
