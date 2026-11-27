# OCR 팀 인터페이스 연결 (초안 기준)

제공된 팀 표의 `extract_product_info(image_path) -> {brand, product_name, model, price_text}`에 맞춘 추가 모듈이다.
확정된 `docs/interface.md`는 제공되지 않았으므로 변경하지 않는다. 호출 경로와 None 규칙은 팀 검토가 필요하다.

## 팀원이 사용할 함수

```python
from ocr.team_interface import extract_product_info

fields = extract_product_info(image_path)
# 정확히 네 키를 반환한다. 값은 문자열 또는 None이다.
```

- brand: 등록된 별칭 사전과 일치한 단일 브랜드. 사전 밖 브랜드나 복수 브랜드는 None.
- product_name: `商品名:`, `제품명:`, `product name:` 등 명시적 표기가 있는 단일 이름.
  일반 포장에서는 표기가 없을 수 있으며 그 경우 None이다. 후보를 자동 확정하지 않는다.
- model: `型番:`, `품번:`, `model:` 등 명시적 표기가 있는 단일 모델명/품번. OCR 모델명이 아니다.
- price_text: 통화 표기가 포함된 단일 가격의 원래 OCR 줄. 금액 변환이나 통화 해석은 가격 모듈이 담당한다.
  숫자만 있는 줄은 가격으로 취급하지 않는다. 복수 가격은 None으로 남긴다.

가격/모델을 포함한 결과는 OCR로부터 나온 값이며 정확성이 보장되지 않는다. UI 검토를 권장한다.
사진을 읽지 못하거나 OCR이 실패하면 기존 reader의 예외를 그대로 전달한다.
호출하는 쪽에서 예외 안내를 하고, None을 빈 검색어 또는 금액 0으로 처리하지 않는다.

## 화면 수정 → 검색 연결 (권장)

```python
from ocr.team_interface import inspect_product_info, apply_user_confirmation

review = inspect_product_info(image_path)  # OCR은 한 번 실행
# review['fields']: 네 가지 필드
# review['product_name_candidates']: 상품명 제안 (오인식/광고 문구일 수 있음)
# review['ocr_lines']: 인식 원문과 신뢰도
# UI에서 내용을 보여주고 사용자가 입력/수정 후 확인하도록 한다.

# 아래 호출은 사용자가 확인 버튼을 누른 뒤 수행한다.
fields = apply_user_confirmation(
    review['fields'], product_name=user_entered_product_name
)
# 검색 담당 함수와 연결: search_products(fields['product_name'])
# 가격 문구가 있을 때만 가격 담당 함수와 연결: extract_price(fields['price_text'])
```

`user_entered_product_name`은 UI 입력값이며 예제에서 자동으로 생성하지 않는다.
검색어에 브랜드/맛/용량이 필요하면 사용자가 확인하는 검색 입력창에 포함한다.
apply_user_confirmation에 brand, model, price_text를 전달하여 수정하거나 None으로 지울 수도 있다.
함수 호출 자체가 실제 사용자의 확인을 검증하지는 않으므로, UI에서 확인 절차를 연결해야 한다.
네 필드 함수와 상세 함수를 연속 호출하면 OCR이 두 번 실행되니 UI에서는 상세 함수만 사용한다.

## 기존 함수와의 구분

- 기존 `ocr.product_info.extract_product_info(ocr_result)`는 변경하지 않았다.
- 팀 인터페이스는 `ocr.team_interface.extract_product_info(image_path)`이다.
- 실제 인식률 개선, 새로운 모델 설치, OCR 엔진 교체는 이번 작업 범위가 아니다.

## 우분투 검증

프로젝트 루트와 기존 가상환경에서:

```bash
python -m unittest discover -s tests -p test_ocr_team_interface.py -v
python -m ocr.check_team_interface results/real_baseline_small results/team_interface_v1
```

두 번째 명령은 저장된 JSON만 읽으므로 모델을 다시 실행하지 않는다.
생성 JSON에는 fields와 후보, 미확인/복수 항목이 함께 들어 있다.

사진 입력 경로를 실제로 점검하려면:

```bash
python -c "from ocr.team_interface import extract_product_info; print(extract_product_info('samples/real_products_small/KakaoTalk_20261113_150955227_05.jpg'))"
```

일본어를 입력할 필요 없이 실행할 수 있다. 전체 값이 None이어도 예외가 없다면 반환 형식은 정상이다.
그것은 자동 추출의 성능 성공을 뜻하지 않는다. 사용자에게 제품명 입력을 요청해야 한다.

## 한계와 검증 기록

규칙은 신뢰도 0.7 이상인 줄에 적용한다. 이 값은 정답률이나 검증된 최적값이 아니다.
모델/가격/상품명이 여러 OCR 줄로 갈라진 경우 자동 연결하지 않는다.
상품명 표기가 없는 일반 포장에서는 사용자 확인이 필요하다.
브랜드 사전과 일본어 중심 후보 규칙은 기존 모듈의 한계를 따른다.
가격에서 통화-숫자 형식만 확인하며, 복잡한 할인/단가/세금의 의미 해석은 하지 않는다.

Windows 로컬에서 합성 예제와 사용자가 제공한 _05 OCR 텍스트를 활용한 15개 테스트를 수행한다.
사진 입력 함수는 모의 OCR로 전달 구조를 테스트한다. 실제 Ubuntu PaddleOCR 실행은 설치 후 확인해야 한다.
이 테스트 수는 실제 사진 인식률이 아니다. 기존 _03/_04 전체 JSON은 작업 환경에서 직접 읽지 못했다.
