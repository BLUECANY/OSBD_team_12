# OCR 결과에서 상품 검색 후보 만들기

## 상태와 범위

규칙 기반 첫 버전이다. OCR 오인식을 복구하거나 상품의 정체를 확인하는 모델은 아니다.
브랜드, 상품명, 맛, 용량의 후보를 분리하고 사람이 확인한 이름을 검색 담당 모듈에 넘긴다.
기존 reader.py, OCR 모델, 전처리 코드는 변경하지 않는다. 추가 패키지 설치는 필요 없다.

## 저장된 OCR 결과로 실행

프로젝트 루트에서:

```bash
python -m ocr.extract_product_info results/real_baseline_small results/product_info_v1
python -m unittest discover -s tests -p test_product_info.py -v
```

입력은 PaddleOCR JSON 또는 reader.read_text 반환값이다. rec_texts와 rec_scores는 길이가 같아야 한다.
PaddleOCR JSON의 res 래퍼도 지원한다.

## 팀 코드에서 사용

```python
from ocr.reader import read_text
from ocr.product_info import extract_product_info

ocr_result = read_text(image_path)
info = extract_product_info(ocr_result)
# 화면에서 info['ocr_lines'], info['query_candidates']를 보여준다.
# 상품명을 사용자가 선택/수정한 후에만 다음 호출을 수행한다.
info = extract_product_info(ocr_result, confirmed_product_name=user_confirmed_name)
# 이제 info['search_query']를 검색 담당 모듈에 전달한다.
```

모든 후보는 기본적으로 확인이 필요하다. UI는 확인 전 search_query=None일 때 자동 검색을 하지 않는다.
confirmed_product_name에 후보를 자동 복사하지 않는다. 확인 문구에는 사용자가 필요한 브랜드,
제품명, 맛, 용량을 함께 넣을 수 있다. 인식이 잘못된 브랜드를 검색어에 자동으로 붙이지 않는다.

## 주요 반환값

| 항목 | 의미 |
| --- | --- |
| brand_candidate / brand_candidates | 등록된 별칭과 일치한 브랜드 후보. 복수이면 단일 후보는 null |
| product_name_candidate / product_candidates | 상품명일 가능성이 있는 글자. OCR 순서이며 정확도 순위가 아님 |
| variant_candidates | 일본어의 '…味' 패턴 후보 |
| volume_candidates | g, kg, ml, l 단위 문자열 후보. 순내용량으로 확정하지 않음 |
| query_candidates | 브랜드와 상품명 후보를 합친 화면 표시용 제안 |
| search_query | 사람이 확인한 검색어. 확인 전에는 null |
| needs_confirmation | 사용자 확인 필요 여부 |
| reason | review_candidates, no_reliable_product_candidate, user_confirmed |
| ocr_lines | 정리한 OCR 텍스트와 원래 신뢰도 |

## 제한과 검증

- 브랜드 사전은 BOURBON, ANESSA, SENKA, Hada Labo, Biore의 소수 별칭만 포함한다.
  사전에 없는 브랜드는 못 찾으며, 호출 시 brand_aliases 인수로 팀 사전을 전달할 수 있다.
- 신뢰도 0.7 기준은 초기 실험값이며 정답률이 아니다. 새로운 사진으로 조정·평가해야 한다.
- 짧은 제품명은 후보에서 빠질 수 있고, 잘못 읽힌 광고 문구가 후보로 남을 수 있다.
- 위치 정보가 없는 글자 목록을 사용한다. 여러 줄로 나뉜 제품명을 임의로 합치지 않는다.
- 일본어 맛 표기와 제한된 용량 단위만 지원한다. 가격, 수량, 규격 추출은 아직 미구현이다.
- 측면 사진 _05의 사용자가 제공한 OCR 결과로 상품명을 지어내지 않는지 검사한다.
  다른 테스트의 글자는 인위적으로 만든 예제이며 실제 사진의 성능 점수가 아니다.
- Windows 로컬 Python에서 규칙 테스트를 수행한다. Ubuntu 설치 후 동일 테스트와 저장된
  실제 JSON 실행을 추가 확인해야 한다. 실제 사진 전체에 대한 정확도 평가는 아직 없다.

## 역할 경계

OCR 담당은 텍스트와 상품 정보 후보를 제공한다. 화면 담당은 수정/확인 UI를 연결하고,
검색 담당은 확인된 search_query로 검색한다. 이 모듈은 외부 API를 호출하지 않는다.
