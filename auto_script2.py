import requests
import pandas as pd
from time import sleep
from tqdm import tqdm
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from dotenv import load_dotenv
import os

# 🔑 인증 키 설정
load_dotenv()
ENCODED_KEY = os.getenv("ENCODED_KEY")
if not ENCODED_KEY:
    raise ValueError("❌ 환경변수 'ENCODED_KEY'가 설정되어 있지 않습니다.")
API_KEY = unquote(ENCODED_KEY)

# ✅ API URL
BASE_LIST_URL = "https://apis.data.go.kr/B551011/KorService1/areaBasedList1"
DETAIL_URL = "https://apis.data.go.kr/B551011/KorService1/detailCommon1"

# ✅ 수집 설정
TOTAL_COUNT = 51034
PAGE_SIZE = 100
all_items = []
contentid_list = []

# ✅ 수집 루프
try:
    for page in tqdm(range(1, (TOTAL_COUNT // PAGE_SIZE) + 2)):
        params = {
            'serviceKey': API_KEY,
            'numOfRows': PAGE_SIZE,
            'pageNo': page,
            'MobileOS': 'ETC',
            'MobileApp': 'TourCollectorApp',
            '_type': '',
        }

        try:
            res = requests.get(BASE_LIST_URL, params=params, timeout=10)
            res.raise_for_status()

            root = ET.fromstring(res.content)
            items = root.findall(".//item")

            if not items:
                print(f"⚠️ [{page}페이지] 항목 없음")
                continue

            for item in items:
                data = {child.tag: child.text for child in item}
                contentid = data.get("contentid")

                if not contentid:
                    print(f"❗ [page={page}] contentid 누락 → {data.get('title', '제목 없음')}")
                    continue

                contentid_list.append(contentid)

                # ✅ 상세조회
                detail_params = {
                    'serviceKey': API_KEY,
                    'contentId': contentid,
                    'MobileOS': 'ETC',
                    'MobileApp': 'TourCollectorApp',
                    '_type': 'xml',
                    'defaultYN': 'Y',
                    'overviewYN': 'Y',
                }

                try:
                    detail_res = requests.get(DETAIL_URL, params=detail_params, timeout=10)
                    detail_res.raise_for_status()

                    if "xml" in detail_res.headers.get("Content-Type", ""):
                        detail_root = ET.fromstring(detail_res.content)
                        detail_item = detail_root.find(".//item")
                        if detail_item is not None:
                            for child in detail_item:
                                data[child.tag] = child.text
                    else:
                        print(f"[contentid={contentid}] XML 응답 아님 → {detail_res.headers.get('Content-Type')}")

                except Exception as de:
                    print(f"[contentid={contentid}] 상세조회 실패: {de}")

                all_items.append(data)

            sleep(1.2)

        except Exception as e:
            print(f"[page={page}] 목록 조회 에러: {e}")
            sleep(3)
            continue

except KeyboardInterrupt:
    print("⛔ 사용자 중단 감지됨. 데이터 저장 중...")

# ✅ 저장
if all_items:
    try:
        df = pd.DataFrame(all_items)
        df.to_excel("visitkorea_areaBasedList1_with_detail.xlsx", index=False)
        print("✅ 저장 완료: visitkorea_areaBasedList1_with_detail.xlsx")
        print(f"🔎 수집된 전체 항목 수: {len(all_items)}")
        print(f"🆔 contentid 수: {len(contentid_list)}")
    except Exception as save_err:
        print(f"❌ 저장 실패: {type(save_err).__name__} - {save_err}")
else:
    print("❌ 수집된 데이터가 없습니다. API 또는 파싱 오류 확인 필요.")
