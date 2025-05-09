
import requests
import pandas as pd

# ✅ 여기에 디코딩된 서비스키 직접 삽입
API_KEY = "46xMfmcBoZGoSoejE1CG9Q3JMoe+cCeVRcpnbsRSRgly0kvx3mqZ8xGxVc7MC9zjofjQRydPfihGWN7/Sm4Fg=="

def fetch_areacodes():
    url = "https://apis.data.go.kr/B551011/KorService1/areaCode1"
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourCollectorApp",
        "_type": "xml"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ 요청 실패: {response.status_code}")
        print(response.text)
        return

    try:
        data = response.json()
        items = data["response"]["body"]["items"]["item"]
        df = pd.DataFrame(items)
        print("✅ 지역코드 수집 성공 (상위 5개):")
        print(df.head())
        df.to_excel("areacode_list.xlsx", index=False)
        print("💾 저장 완료: areacode_list.xlsx")
    except Exception as e:
        print("❌ JSON 파싱 오류:", str(e))
        print("응답 본문:")
        print(response.text)

if __name__ == "__main__":
    fetch_areacodes()
