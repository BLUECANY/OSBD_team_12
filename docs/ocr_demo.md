<환경 구축 단계>
실행 환경 : Ubuntu, Python 3.12.16

사용한 설치 명령어 : uv python install 3.12

python --version 실행 결과 : Python 3.12.16

발생한 오류와 해결 방법 : curl 명령이 없어서 설치한 뒤 uv 설치를 다시 진행

다음 할 일  : PaddleOCR 설치와 공식 예제 실행

<PaddleOCR 공식 예제 실핼>
Python 3.12 가상환경에서 PaddlePAddle과 PaddleOCR 설치
공식 예제 이미지 general_ocr_002.png 다운로드
ocr/ocr_demo.py 작성 및 CPU 환경에서 실행

발생한 오류와 해결방법 : 
철 실행에서 ConvertPirAttribute2RuntimeAttribute 오류 발생
인식 단계에서 실행이 중단되어 결과 폴더에 파일이 생성되지 않음
PaddleOCR() 설정에 enable_mkldnn=False를 추가하여 CPU 가속 기능을 비활성화
설정 변경 후 결과 파일 생성 확인

실행명령 : python -u ocr/ocr_demo.py

실행결과 :
results/ocr_demo/에 다음 파일이 생성됨
general_ocr_002_ocr_res_img.png: 인식 결과 이미지
general_ocr_002_res.json: 인식 텍스트, 좌표, 신뢰도 등의 결과 데이터

다음 할 일 : 실제 상품 사진 5장으로 OCR 실행
