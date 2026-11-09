"""AI 웹검색으로 국내 판매가를 찾는 실험용 스크립트 (9주차, 담당 강민지).

사용법:
    pip install google-genai python-dotenv
    python search/ai_search_test.py "상품 검색어"
"""
import json
import os
import re
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # .env 파일에서 키를 읽는다 (코드에 키를 직접 쓰지 않는다)

PROMPT = """한국 온라인 쇼핑몰에서 아래 상품의 국내 판매가를 찾아줘.
상품: {name}

반드시 아래 JSON 배열만 출력해줘. 설명 문장은 쓰지 마.
각 항목: {{"name": 상품명, "price": 숫자(원, 쉼표 없이), "link": 실제 상품 페이지 주소, "source": 쇼핑몰 이름}}
같은 상품 최대 3개, 비슷한 대체상품 최대 2개를 찾고, 항목마다 "type" 에 "same" 또는 "alternative"를 적어줘.
찾을 수 없으면 빈 배열 []을 출력해줘. 가격이나 링크를 지어내지 마."""


def search_products(name: str) -> list[dict]:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
        contents=PROMPT.format(name=name),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )
    text = response.text or ""
    match = re.search(r"\[.*\]", text, re.DOTALL)  # 응답에서 JSON 배열 부분만 꺼낸다
    if not match:
        print("JSON을 찾지 못했습니다. 원본 응답:\n", text)
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        print("JSON 해석 실패. 원본 응답:\n", text)
        return []


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "로지텍 MX Master 3S"
    start = time.time()
    items = search_products(query)
    elapsed = time.time() - start
    print(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"\n소요 시간: {elapsed:.1f}초 / 결과 {len(items)}건")
