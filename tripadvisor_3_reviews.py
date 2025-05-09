import requests
import openai
import os
from typing import List, Optional
from dotenv import load_dotenv

# ====== 환경변수 로드 ======
load_dotenv()  # .env 파일에서 환경변수 읽기

# ====== 1. 트립어드바이저 리뷰 3개 가져오기 ======
def fetch_top3_reviews(place_name: str, api_key: str) -> List[str]:
    BASE_URL = 'https://api.content.tripadvisor.com/api/v1'
    # 1) 장소 검색
    search_url = f"{BASE_URL}/location/search"
    search_params = {'searchQuery': place_name, 'key': api_key, 'language': 'ko', 'category': 'attractions'}
    search_resp = requests.get(search_url, params=search_params)
    search_resp.raise_for_status()
    search_data = search_resp.json()
    if not search_data.get('data'):
        raise ValueError("No location found for the given place name.")
    location_id = search_data['data'][0]['location_id']
    # 2) 리뷰 3개 추출
    review_url = f"{BASE_URL}/location/{location_id}/reviews"
    review_params = {'limit': 3, 'key': api_key}
    review_resp = requests.get(review_url, params=review_params)
    review_resp.raise_for_status()
    review_data = review_resp.json()
    reviews = [r['text'] for r in review_data.get('data', [])[:3]]
    if not reviews:
        raise ValueError("No reviews found for the given location.")
    return reviews

# ====== 2. OpenAI API로 요약 (openai>=1.0.0) ======
def summarize_reviews_openai(reviews: List[str], openai_api_key: str, language: str = "ko") -> str:
    client = openai.OpenAI(api_key=openai_api_key)
    joined = "\n".join(reviews)
    prompt = (
        f"다음은 여행지에 대한 실제 리뷰 3개입니다. 핵심만 간결하게 한글로 요약해 주세요.\n\n"
        f"{joined}\n\n"
        f"요약:"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 또는 "gpt-4"
        messages=[
            {"role": "system", "content": "당신은 여행 리뷰 요약 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

# ====== 3. 메인 실행 ======
if __name__ == "__main__":
    # .env에서 API 키 읽기
    API_KEY = os.getenv("TRIPADVISOR_API_KEY")
    place = "롯데타워"

    if API_KEY and place:
        try:
            reviews = fetch_top3_reviews(place, API_KEY)
        except Exception as e:
            print(f"리뷰 가져오기 실패: {e}")
            exit(1)

    print("=== 원본 리뷰 3개 ===")
    for i, r in enumerate(reviews, 1):
        print(f"[{i}] {r}")

    print("\n=== 리뷰 합친 결과 (하나의 텍스트) ===")
    joined_reviews = " ".join(reviews)
    print(joined_reviews)