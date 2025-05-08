import requests
import pandas as pd
from time import sleep
from tqdm import tqdm
from dotenv import load_dotenv
import os
from urllib.parse import unquote

# 🔑 인증 키 설정 (반드시 디코딩된 값 사용)
load_dotenv()
ENCODED_KEY = os.getenv("ENCODED_KEY")
API_KEY = unquote(ENCODED_KEY)

# API 엔드포인트
BASE_LIST_URL = "https://apis.data.go.kr/B551011/KorService/areaBasedList1"

TOTAL_COUNT = 51034
PAGE_SIZE = 100

# 수집 결과 저장 리스트
all_items = []

# 지역 기반 목록 조회
try:
    for page in tqdm(range(1, (TOTAL_COUNT // PAGE_SIZE) + 2)):
        params = {
            'serviceKey': API_KEY,
            'numOfRows': PAGE_SIZE,
            'pageNo': page,
            'MobileOS': 'ETC',
            'MobileApp': 'TourCollectorApp',
            '_type': 'json',
            'arrange': 'A'
        }

        try:
            res = requests.get(BASE_LIST_URL, params=params, timeout=10)
            res.raise_for_status()

            content_type = res.headers.get('Content-Type', '')
            if "application/json" not in content_type:
                print(f"[{page}페이지] JSON 아닌 응답: {content_type}\n본문: {res.text[:200]}...")
                continue

            json_data = res.json()
            items = json_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            for item in items:
                all_items.append(item)

            sleep(1.2)

        except Exception as e:
            print(f"[{page}페이지 에러]: {type(e).__name__} - {e}")
            sleep(3)
            continue
except KeyboardInterrupt:
    print("⛔ 사용자 중단 감지됨, 부분 저장 진행 중...")
finally:
    if all_items:
        try:
            df = pd.DataFrame(all_items)
            df.to_excel("visitkorea_areaBasedList1_partial.xlsx", index=False)
            print("💾 중간 저장 완료: visitkorea_areaBasedList1_partial.xlsx")
        except Exception as save_err:
            print(f"❌ 저장 중 오류 발생: {type(save_err).__name__} - {save_err}")
    else:
        print("❌ 수집된 데이터가 없습니다. 응답 확인 필요.")
