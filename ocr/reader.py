from functools import lru_cache
from pathlib import Path
import cv2
from paddleocr import PaddleOCR
@lru_cache(maxsize=1)
def _get_ocr():
    return PaddleOCR(
        device="cpu",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
   )
def read_text(image_path):
    """Read one image and return recognized texts and scores."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    height, width = image.shape[:2]
    if max(height, width) > 1280:
        scale = 1280 / max(height, width)
        image = cv2.resize(
            image,
            (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    results = _get_ocr().predict(image)
    if not results:
        raise RuntimeError("OCR returned no result.")
    texts = []
    scores = []
    for result in results:
        payload = result.json
        data = payload.get("res", payload)
        texts.extend(data["rec_texts"])
        scores.extend(float(score) for score in data["rec_scores"])
    return {
        "status": "ok" if texts else "no_text",
        "rec_texts": texts,
        "rec_scores": scores,
    }
