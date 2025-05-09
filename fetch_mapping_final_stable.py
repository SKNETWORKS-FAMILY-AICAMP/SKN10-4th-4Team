
import requests
import pandas as pd

# 직접 입력한 디코딩된 TourAPI 서비스 키
API_KEY = "P46xMfmcBoZGoSoejE1CG9Q3JMoe+cCeVRcpnbsRSRgly0kvx3mqZ8xGxVc7MC9zjofjQRydPfihGWN7/Sm4Fg=="
BASE_URL = "https://apis.data.go.kr/B551011/KorService1"
HEADERS = {"User-Agent": "TourCollectorApp"}

def fetch_category_codes():
    print("🔍 카테고리 코드 수집 중...")
    codes = []
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "_type": "json"
    }

    # cat1
    r1 = requests.get(f"{BASE_URL}/categoryCode1", params=params, headers=HEADERS)
    if r1.status_code != 200:
        print("❌ cat1 요청 실패:", r1.text)
        return
    cat1_items = r1.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
    for c1 in cat1_items:
        codes.append({"cat1": c1["code"], "cat1_name": c1["name"]})
        # cat2
        params2 = {**params, "cat1": c1["code"]}
        r2 = requests.get(f"{BASE_URL}/categoryCode2", params=params2, headers=HEADERS)
        if r2.status_code != 200: continue
        cat2_items = r2.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
        for c2 in cat2_items:
            codes.append({
                "cat1": c1["code"], "cat1_name": c1["name"],
                "cat2": c2["code"], "cat2_name": c2["name"]
            })
            # cat3
            params3 = {**params2, "cat2": c2["code"]}
            r3 = requests.get(f"{BASE_URL}/categoryCode3", params=params3, headers=HEADERS)
            if r3.status_code != 200: continue
            cat3_items = r3.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
            for c3 in cat3_items:
                codes.append({
                    "cat1": c1["code"], "cat1_name": c1["name"],
                    "cat2": c2["code"], "cat2_name": c2["name"],
                    "cat3": c3["code"], "cat3_name": c3["name"]
                })

    df = pd.DataFrame(codes)
    df.to_excel("category_code_mapping_fixed.xlsx", index=False)
    print("✅ category_code_mapping_fixed.xlsx 저장 완료")

def fetch_sigungu_codes():
    print("📍 지역 코드 수집 중...")
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "_type": "json"
    }
    result = []
    r1 = requests.get(f"{BASE_URL}/areaCode1", params=params, headers=HEADERS)
    if r1.status_code != 200:
        print("❌ areaCode1 요청 실패:", r1.text)
        return
    area_items = r1.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
    for area in area_items:
        areaCode = area["code"]
        areaName = area["name"]
        r2 = requests.get(f"{BASE_URL}/areaCode2", params={**params, "areaCode": areaCode}, headers=HEADERS)
        if r2.status_code != 200: continue
        sub_items = r2.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
        for sub in sub_items:
            result.append({
                "지역코드": areaCode,
                "지역명": areaName,
                "시군구코드": sub["code"],
                "시군구명": sub["name"]
            })

    df = pd.DataFrame(result)
    df.to_excel("sigungu_code_mapping_fixed.xlsx", index=False)
    print("✅ sigungu_code_mapping_fixed.xlsx 저장 완료")

if __name__ == "__main__":
    fetch_category_codes()
    fetch_sigungu_codes()
