import re
import requests
from judge.judge import judge_price
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

    # 잘못된 가격 검사
    if not amount.is_finite() or amount < 0:
        raise ValueError("해외 상품 가격이 올바르지 않습니다.")

    # Frankfurter API
    url = f"https://api.frankfurter.dev/v2/rate/{currency}/KRW"

    # 환율 요청 (최대 10초)
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    # 환율 데이터 가져오기
    data = response.json(parse_float=Decimal)

    # 응답 형식 검사
    if not isinstance(data, dict):
        raise ValueError("환율 데이터 형식이 올바르지 않습니다.")

    try:
        rate = Decimal(str(data["rate"]))
        date = data["date"]

    except (KeyError, InvalidOperation, ValueError, TypeError):
        raise ValueError("환율 정보를 확인할 수 없습니다.")

    # 환율 값 검사
    if not rate.is_finite() or rate <= 0:
        raise ValueError("환율 값이 올바르지 않습니다.")

    # 원화 환산
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
        "date": date
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
            # 4. 국내 상품 가격 비교
            try:
                domestic_text = input(
                    "\n국내 상품 가격을 입력하세요(원): "
                )

                domestic_price = Decimal(
                    domestic_text.replace(",", "").strip()
                )

                if domestic_price < 0:
                    print("가격은 0 이상이어야 합니다.")

                else:
                    # 해외 상품 원화 환산 가격
                    foreign_price = result["krw"]

                    # 국내 가격 - 해외 가격
                    difference = domestic_price - foreign_price

                    print("\n===== 해외 상품 가격 비교 =====")
                    print(f"해외 상품 환산 가격: {foreign_price:,.0f}원")
                    print(f"국내 상품 판매가격: {domestic_price:,.0f}원")

                    # 가격 비교
                    if difference > 0:
                        print(f"가격 차이: {difference:,.0f}원")

                        if domestic_price > 0:
                            saving_rate = (
                                difference / domestic_price * 100
                            )
                            print(f"절약 비율: {saving_rate:.2f}%")

                        print("비교 결과: 해외 상품이 더 저렴합니다.")

                    elif difference < 0:
                        print(f"가격 차이: {abs(difference):,.0f}원")
                        print("비교 결과: 국내 상품이 더 저렴합니다.")

                    else:
                        print("가격 차이: 0원")
                        print("비교 결과: 두 상품의 가격이 같습니다.")

                    print("* 배송비와 세금은 포함되지 않았습니다.")
 # 구매 판단 함수 실행
                    judge_result = judge_price(
                           foreign_price,
                           domestic_price
                    )

                    print("\n===== 최종 구매 판단 =====")
                    print("판단:", judge_result["decision"])
                    print("근거:", judge_result["reason"])

            except InvalidOperation:
                print("국내 가격을 올바르게 입력하세요.")

        except requests.RequestException as e:
            print("환율 API 연결 오류:", e)

        except (KeyError, ValueError) as e:
            print("환율 데이터 오류:", e)
