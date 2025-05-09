import requests
import ssl
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

# 최신 방식: 안전한 기본 TLS 설정 사용
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)

# 세션 구성
session = requests.Session()
session.mount("https://", TLSAdapter())

# 테스트 요청 (지역코드: 1, 관광지 contentTypeId: 12)
params = {
    "serviceKey": "P46xMfmcBoZGoSoejE1CG9Q3JMoe+cCeVRcpnbsRSRgly0kvx3mqZ8xGxVc7MC9zjofjQRydPfihGWN7/Sm4Fg==",
    "numOfRows": 1000,
    "pageNo": 1,
    "MobileOS": "ETC",
    "MobileApp": "TourCollectorApp",
    "_type": "json",
    "areaCode": 1,
    "lang": "KOR",
    "contentTypeId": 12
}

url = "https://apis.data.go.kr/B551011/KorService/areaBasedList1"

try:
    res = session.get(url, params=params, timeout=10)
    print(res.status_code)
    print(res.json())
except requests.exceptions.SSLError as e:
    print("SSL 오류:", e)
except Exception as e:
    print("기타 오류:", e)
