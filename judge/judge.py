from decimal import Decimal

# 구매 판단 함수
def judge_price(foreign_krw, domestic_krw):

    # 가격을 Decimal 형식으로 변환
    foreign = Decimal(str(foreign_krw))
    domestic = Decimal(str(domestic_krw))

    # 잘못된 가격 검사
    if foreign < 0 or domestic < 0:
        raise ValueError("가격은 0 이상이어야 합니다.")

    # 가격 차이 계산
    difference = domestic - foreign

    # 해외 상품이 저렴한 경우
    if difference > 0:

        saving_rate = (difference / domestic) * 100

        decision = "해외 구매 고려"

        reason = (
            f"해외 상품이 국내 상품보다 "
            f"{difference:,.0f}원 저렴합니다. "
            f"상품 가격 기준으로 해외 구매가 유리합니다."
        )

    # 국내 상품이 저렴한 경우
    elif difference < 0:

        saving_rate = Decimal("0")

        decision = "해외 구매 보류"

        reason = (
            f"국내 상품이 해외 상품보다 "
            f"{abs(difference):,.0f}원 저렴합니다. "
            f"상품 가격 기준으로 국내 구매가 유리합니다."
        )

    # 가격이 같은 경우
    else:

        saving_rate = Decimal("0")

        decision = "가격 동일"

        reason = (
            "해외 상품과 국내 상품의 가격이 같습니다."
        )

    return {
        "decision": decision,
        "difference": abs(difference),
        "saving_rate": saving_rate,
        "reason": reason
    }


# 프로그램 테스트
if __name__ == "__main__":

    foreign_price = Decimal(
        input("해외 상품 환산 가격을 입력하세요: ")
    )

    domestic_price = Decimal(
        input("국내 상품 가격을 입력하세요: ")
    )

    result = judge_price(foreign_price, domestic_price)

    print("\n===== 구매 판단 결과 =====")

    print("판단:", result["decision"])

    print(
        f"가격 차이: {result['difference']:,.0f}원"
    )

    print(
        f"절약 비율: {result['saving_rate']:.2f}%"
    )

    print("판단 근거:", result["reason"])

    print(
        "* 배송비, 세금, 결제 수수료는 "
        "포함되지 않았습니다."
    )
