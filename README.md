# 해외 여행 상품 가격 비교 시스템

> OSBD 12팀
>
> 여행지에서 상품 사진을 찍으면 OCR로 상품 정보와 가격을 인식하고,
> 현지 가격을 원화로 환산해 국내 판매가와 비교한 뒤 **구매 / 보류**를 근거와 함께 알려줍니다.

## 주요 흐름

```
사진 업로드 → OCR 인식 → 사용자 확인·수정 → 원화 환산 → 국내가 검색 → 구매/보류 판단
```

## 폴더 구조

| 폴더 | 역할 | 담당 |
|---|---|---|
| `ocr/` | 상품 사진에서 브랜드·상품명·모델명·가격 인식 (PaddleOCR, OpenCV 전처리) | A |
| `price/` | 가격 문자열에서 통화·금액 추출, 환율 API로 원화 환산 | B |
| `judge/` | 환산가와 국내가를 비교해 차액과 구매/보류 근거 산출 | B |
| `search/` | 국내 판매가 검색, RapidFuzz로 상품명 보정 및 동일·대체상품 분류 | C |
| `app/` | Streamlit 사용자 화면, 전체 모듈 연결 | D |
| `samples/` | 테스트·검증용 상품 사진, 정답표 | 전원 |
| `docs/` | 인터페이스 명세, 조사 결과, 실패 사례 등 문서 | 전원 |

## 모듈 인터페이스 (초안)

> 10주차 회의 후 `docs/interface.md`에서 확정합니다.

| 모듈 | 함수 | 반환 |
|---|---|---|
| ocr | `extract_product_info(image_path)` | `{brand, product_name, model, price_text}` |
| price | `extract_price(text)` | 통화, 금액 |
| price | `convert_to_krw(amount, currency)` | 환산 금액, 환율 출처, 조회 시각 |
| search | `search_products(product_name)` | `[{name, price, link, source}, ...]` |
| judge | (10주차 확정) | 차액(원·%), 구매/보류 근거 문구 |

## 설치 및 실행

**요구 사항:** Python 3.10 ~ 3.12

```bash
# 1. 저장소 받기
git clone https://github.com/choihh38/OSBD_team_12.git
cd OSBD_team_12

# 2. 가상환경 만들고 켜기
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. 라이브러리 설치
pip install -r requirements.txt

# 4. API 키 설정 (.env에 실제 키 입력)
cp .env.example .env

# 5. 실행
streamlit run app/main.py
```

> 실행 파일 이름은 10주차 app 뼈대 제작 후 확정합니다.

## 협업 규칙

- `main`에 직접 push하지 않고, **내 브랜치 → PR → 리뷰 후 머지**
- 브랜치 이름: `feature/모듈명` (예: `feature/ocr`, `feature/price`)
- 작업 시작 전 `git pull`, 작업 후 **작게 자주** 커밋
- 할 일은 GitHub Issues에 등록하고 끝나면 닫기
- API 키는 `.env`에만 저장하고 **절대 커밋하지 않기**
- AI가 만든 코드는 반드시 직접 실행해서 확인

## 일정

| 주차 | 단계 | 목표 |
|---|---|---|
| 9~10주 | 재현 | 환경 구축, PaddleOCR 데모 재현, 모듈별 최소 기능, 인터페이스 확정 |
| 11~12주 | 개선·통합 | "사진 → 인식 → 환산 → 국내가 비교" 전체 흐름 완성 |
| 13주 | 검증 | 인식률, 검색 정확도, 수동 대비 소요 시간 측정, 실패 사례 기록 |
| 14~15주 | 문서화·발표 | Docker, README, 라이선스 정리, 데모 안정화, 보고서와 발표 |

## 팀원

| 담당 | 이름 | GitHub | 역할 |
|---|---|---|---|
| A | | | 인식(OCR) — `ocr` |
| B | | | 가격·판단 — `price`, `judge` |
| C | | | 검색·매칭 — `search` |
| D | | | 통합·인프라 — `app`, 저장소 관리 |

## 라이선스

추후 결정 (사용 오픈소스: PaddleOCR·PaddlePaddle — Apache-2.0, RapidFuzz — MIT, OpenCV — Apache-2.0 등)
