import re
import requests
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# 지원 국가 및 통화
currencies = {
    "JPY": "일본",
    "CNY": "중국",
    "USD": "미국",
    "EUR": "유럽(유로존)"
}

# 통화 기호
symbols = {
    "JPY": r"[¥￥]",
    "CNY": r"[¥￥]",
    "USD": r"[$＄]",
    "EUR": r"€"
}


# 1. 가격 추출 함수
def extract_price(text, currency):

    pattern = symbols[currency] + r"\s*([0-9][0-9.,]*)"

    match = re.search(pattern, text)

    if not match:
        return None

    price_text = match.group(1)

    # 유럽식 숫자 표기 처리
    if currency == "EUR":
        price_text = price_text.replace(".", "")
        price_text = price_text.replace(",", ".")

    else:
        price_text = price_text.replace(",", "")

    try:
        return Decimal(price_text)

    except InvalidOperation:
        return None


# 2. 원화 환산 함수
def convert_to_krw(amount, currency):

    url = f"https://api.frankfurter.dev/v2/rate/{currency}/KRW"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json(parse_float=Decimal)

    rate = Decimal(str(data["rate"]))

    krw = amount * rate

    krw = krw.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    return {
        "amount": amount,
        "currency": currency,
        "rate": rate,
        "krw": krw,
        "date": data["date"]
    }


# 3. 메인 프로그램
print("===== 해외 상품 가격 비교 시스템 =====")

print("\n지원 국가")

for code, country in currencies.items():
    print(f"{country}: {code}")

currency = input("\n통화 코드를 입력하세요: ").upper().strip()

if currency not in currencies:
    print("지원하지 않는 통화입니다.")

else:
    text = input("해외 상품 가격을 입력하세요: ")

    amount = extract_price(text, currency)

    if amount is None:
        print("가격을 추출할 수 없습니다.")

    else:
        try:
            result = convert_to_krw(amount, currency)

            print("\n===== 환율 변환 결과 =====")
            print("국가:", currencies[currency])
            print("해외 가격:", result["amount"], currency)
            print("적용 환율:", result["rate"])
            print(f"원화 환산 가격: {result['krw']:,.0f}원")
            print("환율 기준일:", result["date"])
            print("환율 출처: Frankfurter")

        except requests.RequestException as e:
            print("환율 API 연결 오류:", e)

        except (KeyError, ValueError) as e:
            print("환율 데이터 오류:", e)
