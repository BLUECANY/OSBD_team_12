import streamlit as st
import time

# --- [더미 함수 설정] 팀원들의 기능이 완성되기 전까지 사용할 가짜 함수입니다. ---
def dummy_ocr(image):
    """A파트(OCR) 담당용 더미 함수"""
    time.sleep(1) # 실제 작동하는 것처럼 약간의 딜레이를 줍니다.
    return {"brand": "Sony", "product_name": "WH-1000XM5", "local_price": 39800}

def dummy_price_conversion(local_price, currency):
    """B파트(가격 변환) 담당용 더미 함수"""
    exchange_rate = 14.5 if currency == "JPY" else 1350.0  # 예시 환율
    krw_price = local_price * exchange_rate if currency == "USD" else local_price * (exchange_rate / 100)
    return int(krw_price)

def dummy_search_domestic(product_name):
    """C파트(국내가 검색) 담당용 더미 함수"""
    return [
        {"mall": "쿠팡", "price": 420000, "link": "https://coupang.com"},
        {"mall": "네이버 쇼핑", "price": 415000, "link": "https://naver.com"},
        {"mall": "SSG닷컴", "price": 430000, "link": "https://ssg.com"}
    ]

# --- [Streamlit UI 시작] ---
st.set_page_config(page_title="해외 여행 상품 가격 비교 시스템", layout="centered")
st.title("✈️ 해외 여행 상품 가격 비교 시스템")
st.write("해외에서 본 상품의 사진을 찍어 올리면 국내 최저가와 비교해 드립니다.")

st.divider()

# 1. 정보 입력 영역
st.subheader("1. 상품 정보 입력")
uploaded_file = st.file_uploader("상품 라벨 이나 영수증 사진을 업로드하세요", type=["png", "jpg", "jpeg"])
currency = st.selectbox("현지 통화를 선택하세요", ["JPY (엔화)", "USD (달러)", "EUR (유로)"])

# 2. 분석 및 비교 실행 버튼
if st.button("🔍 가격 비교 시작", type="primary"):
    if uploaded_file is not None:
        with st.spinner("이미지에서 상품 정보를 분석하는 중... (A파트 OCR)"):
            ocr_result = dummy_ocr(uploaded_file)
            st.success(f"인식 완료: {ocr_result['brand']} - {ocr_result['product_name']}")
        
        with st.spinner("환율 계산 및 원화 환산 중... (B파트 가격)"):
            currency_code = currency.split()[0]
            krw_price = dummy_price_conversion(ocr_result['local_price'], currency_code)
            st.metric(label=f"현지 가격 원화 환산 ({currency_code})", value=f"{krw_price:,} 원")

        with st.spinner("국내 온라인 최저가 검색 중... (C파트 검색)"):
            domestic_results = dummy_search_domestic(ocr_result['product_name'])
            
            st.subheader("🛒 국내 온라인 가격 현황")
            for item in domestic_results:
                st.write(f"- **[{item['mall']}]** {item['price']:,}원 ([바로가기]({item['link']}))")
        
        st.divider()
        
        # 4인 공통 판단 로직 영역
        st.subheader("구매 추천 결과")
        lowest_domestic = min([item['price'] for item in domestic_results])
        if krw_price < lowest_domestic:
            st.balloons()
            st.success(f"🎉 국내 최저가({lowest_domestic:,}원)보다 {lowest_domestic - krw_price:,}원 더 저렴합니다! 현지에서 구매하는 것을 추천합니다.")
        else:
            st.warning(f"⚠️ 국내 최저가({lowest_domestic:,}원)가 더 저렴하거나 비슷합니다. 한국에서 구매하시는 걸 고려해보세요!")
            
    else:
        st.error("사진을 먼저 업로드해 주세요.")

