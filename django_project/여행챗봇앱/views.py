from django.shortcuts import render
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv
from django.conf import settings
from .tripadvisor_3_reviews import fetch_top3_reviews

# 🔥 chroma_db 경로 → 프로젝트 루트 기준
chroma_db_path = os.path.join(settings.BASE_DIR.parent, "chroma_db")

print("🔥 지금 연결된 ChromaDB 경로:", chroma_db_path)

# .env 파일 로드 (프로젝트 루트 기준 상대경로)
env_path = os.path.join(settings.BASE_DIR, "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(env_path))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

chroma_client = chromadb.PersistentClient(path=chroma_db_path)
collection = chroma_client.get_or_create_collection(name="places")

model = SentenceTransformer("intfloat/e5-large-v2")

def summarize_place_and_reviews(place_name, place_desc, reviews, openai_client):
    joined_reviews = " ".join(reviews)
    prompt = (
        f"다음은 여행지 '{place_name}'에 대한 설명과 실제 방문자 리뷰입니다. "
        f"설명과 리뷰를 모두 참고하여, 핵심만 간결하게 한글로 요약해 주세요.\n\n"
        f"[장소 설명]\n{place_desc}\n\n[리뷰]\n{joined_reviews}\n\n요약:")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 여행지 정보 요약 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

def chatbot_view(request):
    answer = ""
    user_question = ""
    region = ""
    category = ""

    # ⭐ 서버 새로 시작할 때마다 세션 초기화!
    if not hasattr(request, '_session_initialized'):
        request.session['chat_history'] = []
        request._session_initialized = True

    chat_history = request.session.get('chat_history', [])

    typing = False

    if request.method == "POST":
        user_question = request.POST.get("question")
        region = request.POST.get("region")
        category = request.POST.get("category")

        print("사용자 질문:", user_question)
        print("선택한 지역:", region)
        print("선택한 카테고리:", category)

        typing = True

        query_embedding = model.encode(["query: " + user_question])

        filters = {}
        if category:
            filters["category"] = category

        query_params = {
            "query_embeddings": query_embedding,
            "n_results": 5,
        }
        
        if filters:
            query_params["where"] = filters

        results = collection.query(**query_params)

        documents = results['documents'][0] if results['documents'][0] else []
        metadatas = results['metadatas'][0] if results['metadatas'][0] else []

        print("검색된 장소 개수:", len(documents))

        if documents:
            summaries = []
            unique_places = {}
            for doc, meta in zip(documents, metadatas):
                place_name = meta['name']
                if place_name not in unique_places:
                    unique_places[place_name] = (doc, meta)

            for place_name, (doc, meta) in list(unique_places.items())[:3]:  # 최대 3개만
                place_desc = doc
                try:
                    reviews = fetch_top3_reviews(place_name, os.getenv("TRIPADVISOR_API_KEY"))
                except Exception as e:
                    reviews = []
                    print(f"Tripadvisor 리뷰 가져오기 실패: {e}")

                if reviews:
                    try:
                        summary = summarize_place_and_reviews(place_name, place_desc, reviews, client)
                    except Exception as e:
                        summary = f"요약 실패: {e}"
                else:
                    summary = f"{place_desc}<br><br>(리뷰를 가져올 수 없습니다.)"

                summaries.append(
                    f"<b>{place_name}</b><br>{summary}<br><br>"
                )

            answer = "<hr>".join(summaries)
        else:
            answer = "조건에 맞는 장소를 찾을 수 없습니다."

        chat_history.append((user_question, answer))
        request.session['chat_history'] = chat_history

        typing = False

    return render(request, "index.html", {
        "answer": answer,
        "user_question": user_question,
        "region": region,
        "category": category,
        "chat_history": chat_history,
        "typing": typing
    })
