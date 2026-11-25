"""
Gemini 상품 분류 모듈

역할:
    동일 상품(same) / 유사 상품(alternative) 분류

사용:
    from ai_search_test import classify_products
"""

import os
import json
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest"
)


def classify_products(keyword, products):

    if not products:
        return []

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[Gemini] API 키가 없어 분류를 건너뜁니다.")

        return [
            {**item, "type": "unknown"}
            for item in products
        ]

    # Gemini에게 전달할 정보
    # URL은 전달하지 않는다.
    product_data = []

    for i, item in enumerate(products):

        product_data.append({
            "index": i,
            "name": item["name"],
            "price": item["price"],
            "source": item["source"]
        })

    prompt = f"""
다음은 사용자가 검색한 상품과 검색 결과 목록이다.

검색어: {keyword}

상품 목록:
{json.dumps(product_data, ensure_ascii=False)}

각 상품을 다음 두 가지로 분류해.

1. same:
   검색어와 동일한 상품 또는 동일한 모델의 상품

2. alternative:
   검색어와 비슷한 기능이나 용도를 가진 대체 상품

반드시 다음 JSON 형식만 출력해.

{{
    "classifications": [
        {{"index": 0, "type": "same"}},
        {{"index": 1, "type": "alternative"}}
    ]
}}

주의:
- 모든 상품의 index를 빠짐없이 분류해.
- index는 입력된 상품 목록의 번호를 그대로 사용해.
- 상품명이나 가격을 수정하지 마.
- same과 alternative 이외의 유형은 사용하지 마.
"""

    try:

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        raw = response.text or ""

        match = re.search(r"\{.*\}", raw, re.S)

        if not match:
            raise ValueError("Gemini JSON 응답을 찾지 못했습니다.")

        data = json.loads(match.group(0))

        classifications = data.get(
            "classifications", []
        )

        # 분류 결과를 원본 상품에 적용
        type_map = {}

        for item in classifications:

            index = item.get("index")
            category = item.get("type")

            if (
                isinstance(index, int)
                and 0 <= index < len(products)
                and category in ("same", "alternative")
            ):
                type_map[index] = category

        result = []

        for i, product in enumerate(products):

            result.append({
                **product,
                "type": type_map.get(i, "unknown")
            })

        return result

    except Exception as e:

        print(f"[Gemini] 분류 오류: {e}")

        return [
            {**item, "type": "unknown"}
            for item in products
        ]


if __name__ == "__main__":

    import sys

    try:
        from .search_products import search_products
    except ImportError:
        from search_products import search_products

    keyword = " ".join(sys.argv[1:]) or "무선 키보드"

    # 검색 API로 상품 검색
    products = search_products(
        keyword,
        classify=False
    )

    # Gemini로 상품 분류
    results = classify_products(
        keyword,
        products
    )

    print("\n===== 상품 검색 결과 =====")

    for i, item in enumerate(results, 1):

        print(f"\n{i}. {item['name']}")
        print(f"가격: {item['price']:,}원")
        print(f"판매처: {item['source']}")
        print(f"분류: {item['type']}")
        print(f"링크: {item['link']}")
