from paddleocr import PaddleOCR

ocr = PaddleOCR(
    device="cpu",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

results = ocr.predict("samples/general_ocr_002.png")

for result in results:
    result.print()
    result.save_to_img("results/ocr_demo")
    result.save_to_json("results/ocr_demo")

print("완료 : results/ocr_demo 폴더를 확인하세요.")
