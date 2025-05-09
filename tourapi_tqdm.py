
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from urllib.parse import unquote
from time import sleep
from multiprocessing import Pool, cpu_count
import os
from tqdm import tqdm
from dotenv import load_dotenv


# 🔑 인증 키 설정
API_KEY = unquote(ENCODED_KEY)

BASE = "https://apis.data.go.kr/B551011/KorService1"
HEADERS = {"User-Agent": "TourCollectorApp"}
SAVE_FOLDER = "interim_results"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def parse_xml(content):
    root = ET.fromstring(content)
    return {child.tag: child.text for child in root.find(".//item")} if root.find(".//item") else {}

def collect_detail_common(contentId):
    url = f"{BASE}/detailCommon1"
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "contentId": contentId,
        "defaultYN": "Y",
        "overviewYN": "Y",
        "_type": "xml"
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        return parse_xml(res.content)
    except:
        return {}

def collect_detail_intro(contentId, contentTypeId):
    url = f"{BASE}/detailIntro1"
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "contentId": contentId,
        "contentTypeId": contentTypeId,
        "_type": "xml"
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        return parse_xml(res.content)
    except:
        return {}

def collect_detail_image(contentId):
    url = f"{BASE}/detailImage1"
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "contentId": contentId,
        "_type": "xml"
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        return [item.findtext("originimgurl") for item in items[:3]]
    except:
        return []

def collect_area_list(page=1, num=100):
    url = f"{BASE}/areaBasedList1"
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "_type": "xml",
        "numOfRows": num,
        "pageNo": page
    }
    res = requests.get(url, params=params, headers=HEADERS, timeout=10)
    root = ET.fromstring(res.content)
    items = root.findall(".//item")
    return [{child.tag: child.text for child in item} for item in items]

def process_one_item(item):
    contentId = item.get("contentid")
    contentTypeId = item.get("contenttypeid")
    if not contentId or not contentTypeId:
        return None

    row = item.copy()
    try:
        row.update(collect_detail_common(contentId))
        row.update(collect_detail_intro(contentId, contentTypeId))
        images = collect_detail_image(contentId)
        for i, img in enumerate(images):
            row[f"image_{i+1}"] = img
        return row
    except Exception as e:
        print(f"❌ 실패: {contentId} - {e}")
        return None

def run_full_pipeline(start_page=1, end_page=511, per_page=100, processes=4):
    for page in tqdm(range(start_page, end_page + 1), desc="📄 페이지 진행"):
        try:
            items = collect_area_list(page=page, num=per_page)
        except Exception as e:
            print(f"❌ 페이지 {page} 로드 실패: {e}")
            continue

        with Pool(processes=processes) as pool:
            results = list(tqdm(pool.imap(process_one_item, items), total=len(items), desc=f"📦 상세 수집 p{page}"))

        df = pd.DataFrame([r for r in results if r])
        save_path = os.path.join(SAVE_FOLDER, f"page_{page:03}.xlsx")
        df.to_excel(save_path, index=False)
        print(f"✅ 저장: {save_path} ({len(df)}건)")
        sleep(1)

    all_dfs = []
    for f in sorted(os.listdir(SAVE_FOLDER)):
        if f.endswith(".xlsx"):
            all_dfs.append(pd.read_excel(os.path.join(SAVE_FOLDER, f)))
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_excel("visitkorea_full_dataset_parallel.xlsx", index=False)
    print("📦 전체 저장 완료: visitkorea_full_dataset_parallel.xlsx")

if __name__ == "__main__":
    run_full_pipeline(start_page=1, end_page=511, per_page=100, processes=4)
