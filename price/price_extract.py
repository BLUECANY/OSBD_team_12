import re
from decimal import Decimal, InvalidOperation

# 지원하는 통화와 통화 기호
currencies = {
    "JPY": r"[¥￥]",
    "CNY": r"[¥￥]",
    "USD": r"[$＄]",
    "EUR": r"€"
}

# 가격 추출 함수
def extract_price(text, currency):

    currency = currency.upper()

    # 지원 통화 확인
    if currency not in currencies:
        return None

    # 통화 기호 뒤의 숫자 추출
    pattern = currencies[currency] + r"\s*([0-9][0-9.,]*)"

    match = re.search(pattern, text)

    if not match:
        return None

    price_text = match.group(1)

    # 유럽식 숫자 표기 처리
    if currency == "EUR":
        price_text = price_text.replace(".", "")
        price_text = price_text.replace(",", ".")

    # 그 외 통화의 숫자 표기 처리
    else:
        price_text = price_text.replace(",", "")

    try:
        price = Decimal(price_text)
    except InvalidOperation:
        return None

    return {
        "currency": currency,
        "amount": price
    }


# 프로그램 시작
print("===== 해외 상품 가격 추출 =====")
print("지원 통화: JPY, CNY, USD, EUR")

currency = input("통화 코드를 입력하세요: ").upper().strip()

text = input("OCR로 인식한 가격을 입력하세요: ")

result = extract_price(text, currency)

if result:
    print("\n===== 추출 결과 =====")
    print("통화:", result["currency"])
    print("가격:", result["amount"])

else:
    print("가격을 추출할 수 없습니다.")
