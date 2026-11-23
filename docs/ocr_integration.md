#OCR 모듈 통합 안내

## 실행환경
- Python 버전 : ocr_python_version.txt 참고
- 설치된 패키지 버전 : ocr_environment.txt 참고
- CPU 실행, enable_mkldnn=False
- 최초 실행 시 모델 다운로드를 위한 인터넷 연결 필요

## 호출 방법
프로젝트 루트에서 실행한다

'''python
from ocr.reader import read_text
result = read_text("samples/real_products_small/KakaoTalk_20261113_150955227_05.jpg")
print(result)
'''

## 입력과 출력
- 입력 : 로컬 이미지 파일 경로
- 상대 경로는 프로그램을 실행한 위치를 기준으로 해석한다.
- status : 글자가 있으면 ok, 없으면 no_text
- rec_texts : 인식된 글자 목록
- rec_scores : 같은 순서의 인식 신뢰도 목록
- 신뢰도는 실제 정답률을 의미하지 않는다.
- ok는 글자가 반환됐더는 뜻이며 정확한 상품 식별을 의미하지 않는다.

## 처리 방식
- 파일이 없으면 FileNotFoundError
- 이미지를 읽지 못하면 ValueError
- OCR 실행 실패 시 예외가 발생한다.
- 호출하는 쪽에서 예외를 처리하고 사용자에게 안내해야 한다.

## 확인한 내용과 한계
- 실제 촬영 사진의 OCR 실행 및 함수 호출을 확인함
- 반사, 기울기, 장식 글꼴에서 오인식이 남아있음
- CLAHE는 일부 정면 사진에서 개선되었으나 기울어진 사진에서는 효과가 제한적이었음
- 상품명, 브랜드, 용량 추출과 검색 모듈 연결은 별도 통합 작업이 필요함
