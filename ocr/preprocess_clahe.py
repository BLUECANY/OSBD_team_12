
from pathlib import Path
import cv2
root = Path(__file__).resolve().parent.parent
src = root / "samples/real_products_small"
dst = root / "samples/real_products_clahe"
dst.mkdir(parents=True, exist_ok=True)
paths = [
    p for p in src.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
]
if not paths:
    raise SystemExit("입력 사진이 없습니다.")
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
for path in sorted(paths):
    image = cv2.imread(str(path))
    if image is None:
        raise RuntimeError(f"읽기 실패:{path.name}")
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    light, a, b = cv2.split(lab)
    light = clahe.apply(light)
    corrected = cv2.merge((light, a, b))
    result = cv2.cvtColor(corrected, cv2.COLOR_LAB2BGR)
    output = dst / f"{path.stem}.png"
    if not cv2.imwrite(str(output), result):
        raise RuntimeError(f"저장 실패: {output}")
    print("저장 완료:", output.name)
