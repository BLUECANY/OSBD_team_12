"""
국내 상품 검색 모듈
SerpApi의 Naver 검색 결과(쇼핑 영역)를 이용한다.
링크와 가격은 API가 준 값을 그대로 사용한다.

사용:
    from search_products import search_products
    items = search_products("로지텍 MX Master 3S")
    # [{name, price, link, source, type, ...}, ...]  (최대 5개)
"""

import os
import re
import json
import time
import html
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
SERPAPI_URL = "https://serpapi.com/search.json"

MAX_RESULTS = 5
CACHE_TTL = 3600  # 1시간
CACHE_DIR = Path(os.getenv("SEARCH_CACHE_DIR", ".search_cache"))
# SerpApi 무료 플랜은 월 250회. 여유를 두고 기본 200회로 제한한다.
MONTHLY_LIMIT = int(os.getenv("SERPAPI_MONTHLY_LIMIT", "200"))
# 상품명 유사도(0~100)가 이 값 이상이면 동일 상품으로 본다 (Gemini 분류 실패 시 대체용)
SAME_THRESHOLD = int(os.getenv("SAME_THRESHOLD", "70"))


def _cache_path(name):
    safe = re.sub(r"[^\w가-힣]+", "_", name.strip().lower())[:80]
    return CACHE_DIR / f"{safe}.json"


def _quota_path():
    return CACHE_DIR / f"serpapi_quota_{date.today().strftime('%Y-%m')}.txt"


def _use_quota():
    """SerpApi 호출 1회를 기록한다. 한도를 넘으면 False."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _quota_path()
    try:
        used = int(path.read_text())
    except Exception:
        used = 0
    if used >= MONTHLY_LIMIT:
        return False
    path.write_text(str(used + 1))
    return True


def _valid_url(url):
    """검색 API에서 반환된 URL 형식 확인"""
    if not isinstance(url, str):
        return False

    parsed = urlparse(url)

    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
    )


def _to_price(value):
    """가격을 정수로 변환"""
    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        numbers = re.sub(r"[^\d]", "", value)
        return int(numbers) if numbers else 0

    return 0


def _clean_source(value):
    """판매처 문자열 정리. '판매처 64', 광고 문구만 있으면 '네이버 쇼핑'으로 대체."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"광고\s*(안내)?", "", text)
    text = text.strip(" :·|-\n\t")
    if not text or re.fullmatch(r"판매처\s*\d*\s*(곳|개)?", text):
        return "네이버 쇼핑"
    return text


def _fetch_products(keyword):
    """SerpApi를 통해 네이버 쇼핑 상품 검색"""

    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_API_KEY가 설정되지 않았습니다.")

    if not _use_quota():
        raise RuntimeError(
            f"SerpApi 월 호출 한도({MONTHLY_LIMIT}회)를 넘었습니다."
        )

    params = {
        "engine": "naver",
        "where": "nexearch",
        "query": keyword,
        "device": "desktop",
        "api_key": SERPAPI_KEY
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if data.get("error"):
        raise RuntimeError(data["error"])

    results = data.get("shopping_results", [])

    products = []
    seen = set()

    for item in results:

        name = html.unescape(
            re.sub(r"<[^>]+>", "", str(item.get("title", "")))
        ).strip()

        price = _to_price(
            item.get("price") or item.get("coupon_price")
        )

        link = item.get("link", "")

        source = _clean_source(item.get("stores"))

        # 상품명, 가격, 링크가 없는 항목은 제외
        if not name or price <= 0 or not _valid_url(link):
            continue

        # 중복 상품 제거
        key = (name, price, source)

        if key in seen:
            continue

        seen.add(key)

        products.append({
            "name": name,
            "price": price,
            "link": link,  # API가 반환한 URL 그대로 사용
            "source": source,
            "type": "unknown",
            "image": item.get("thumbnail"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews"),
            "shipping": item.get("shipping"),
            "sponsored": item.get("sponsored", False)
        })

        if len(products) >= MAX_RESULTS:
            break

    return products


def _fuzzy_classify(products, keyword):
    """RapidFuzz 유사도로 동일/대체 분류 (Gemini 분류를 못 쓸 때의 대체 수단)."""
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return products

    result = []
    for p in products:
        if p.get("type") in ("same", "alternative"):
            result.append(p)
            continue
        score = fuzz.token_set_ratio(keyword.lower(), p["name"].lower())
        result.append({
            **p,
            "type": "same" if score >= SAME_THRESHOLD else "alternative"
        })
    return result


def _classify(products, keyword):
    """Gemini 분류 후, 분류되지 않은 항목은 RapidFuzz로 보완"""

    try:
        try:
            from .ai_search_test import classify_products
        except ImportError:
            from ai_search_test import classify_products

        products = classify_products(keyword, products)
    except Exception as e:
        print(f"[search] Gemini 분류를 건너뜁니다: {e}")

    return _fuzzy_classify(products, keyword)


def _needs_classify(products):
    return any(p.get("type") not in ("same", "alternative") for p in products)


def _save_cache(path, products):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(products, ensure_ascii=False),
        encoding="utf-8"
    )


def search_products(product_name, use_cache=True, retries=1,
                    classify=True):

    product_name = (product_name or "").strip()

    if not product_name:
        return []

    path = _cache_path(product_name)

    # 캐시 확인 (분류까지 끝난 결과를 저장해 두므로 Gemini를 다시 부르지 않는다)
    if use_cache and path.exists():
        if time.time() - path.stat().st_mtime < CACHE_TTL:
            try:
                products = json.loads(
                    path.read_text(encoding="utf-8")
                )

                if classify and _needs_classify(products):
                    products = _classify(products, product_name)
                    _save_cache(path, products)

                return products

            except Exception:
                pass

    # 검색 API 호출
    for attempt in range(retries + 1):

        try:
            products = _fetch_products(product_name)

            if classify and products:
                products = _classify(products, product_name)

            if use_cache and products:
                _save_cache(path, products)

            return products

        except Exception as e:
            print(
                f"[search] 오류 ({attempt + 1}회차): {e}"
            )

            # 한도 초과나 키 누락은 재시도해도 같으므로 바로 종료
            if "한도" in str(e) or "SERPAPI_API_KEY" in str(e):
                break

            time.sleep(1.5)

    return []


if __name__ == "__main__":

    import sys

    keyword = " ".join(sys.argv[1:]) or "무선 키보드"

    start = time.time()

    results = search_products(keyword)

    for i, item in enumerate(results, 1):

        print(f"\n{i}. {item['name']}")
        print(f"   가격: {item['price']:,}원")
        print(f"   판매처: {item['source']}")
        print(f"   구분: {item['type']}")
        print(f"   링크: {item['link']}")

    print(f"\n검색 결과: {len(results)}개")
    print(f"소요 시간: {time.time() - start:.1f}초")
