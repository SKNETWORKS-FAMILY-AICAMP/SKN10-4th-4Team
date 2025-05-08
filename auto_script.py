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

# API 연딩포인트
BASE_LIST_URL = "https://apis.data.go.kr/B551011/KorService1/areaBasedList1"
DETAIL_COMMON_URL = "https://apis.data.go.kr/B551011/KorService1/detailCommon1"

TOTAL_COUNT = 51034
PAGE_SIZE = 100

# 수집 결과 저장 리스트
all_items = []

# 지역 기반 목록 조회
for page in tqdm(range(1, (TOTAL_COUNT // PAGE_SIZE) + 2)):
    params = {
        'serviceKey': API_KEY,
        'numOfRows': PAGE_SIZE,
        'pageNo': page,
        'MobileOS': 'ETC',
        'MobileApp': 'TourCollectorApp',
        '_type': 'json'
    }

    try:
        res = requests.get(BASE_LIST_URL, params=params, timeout=10)
        res.raise_for_status()

        if "application/json" not in res.headers.get('Content-Type', ''):
            print(f"[{page}페이지] JSON 아닌: {res.headers.get('Content-Type')}")
            sleep(5)
            continue

        json_data = res.json()
        items = json_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

        for item in items:
            contentid = item.get("contentid")
            if not contentid:
                continue

            # 상세 정보 추가 호출
            detail_params = {
                'serviceKey': API_KEY,
                'contentId': contentid,
                'MobileOS': 'ETC',
                'MobileApp': 'TourCollectorApp',
                '_type': 'json',
                'defaultYN': 'Y',
                'overviewYN': 'Y'
            }

            try:
                detail_res = requests.get(DETAIL_COMMON_URL, params=detail_params, timeout=10)
                if "application/json" in detail_res.headers.get('Content-Type', ''):
                    detail_json = detail_res.json()
                    detail_items = detail_json.get("response", {}).get("body", {}).get("items", {}).get("item")

                    if isinstance(detail_items, dict):
                        item.update(detail_items)
                    elif isinstance(detail_items, list) and len(detail_items) > 0 and isinstance(detail_items[0], dict):
                        item.update(detail_items[0])
                    else:
                        print(f"[contentid={contentid}] 예외 상세 데이터 형식: {type(detail_items)}")
                else:
                    print(f"[contentid={contentid}] 상세 JSON 아닌: {detail_res.headers.get('Content-Type')}")
            except Exception as de:
                print(f"[contentid={contentid}] 상세 조회 에러: {de}")
                continue

            all_items.append(item)
        sleep(1.5)

    except Exception as e:
        print(f"[{page}페이지 에러]: {e}")
        sleep(5)
        continue

# ✅ 결과 저장
if all_items:
    df = pd.DataFrame(all_items)
    df.to_excel("visitkorea_areaBasedList1_full.xlsx", index=False)
    print("✅ 저장 완료: visitkorea_areaBasedList1_full.xlsx")
else:
    print("❌ 수집된 데이터가 없습니다. 응답 확인 필요.")
