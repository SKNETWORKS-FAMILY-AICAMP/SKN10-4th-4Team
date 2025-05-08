from django.shortcuts import render
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv
from django.conf import settings

# 🔥 chroma_db 경로 → 프로젝트 루트 기준
chroma_db_path = os.path.join(settings.BASE_DIR.parent, "chroma_db")

print("🔥 지금 연결된 ChromaDB 경로:", chroma_db_path)

# .env 파일 로드
load_dotenv(dotenv_path=os.path.join(settings.BASE_DIR.parent, ".env"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

chroma_client = chromadb.PersistentClient(path=chroma_db_path)
collection = chroma_client.get_or_create_collection(name="places")

model = SentenceTransformer("intfloat/e5-large-v2")

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

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=10
        )

        documents = results['documents'][0] if results['documents'][0] else []
        metadatas = results['metadatas'][0] if results['metadatas'][0] else []

        print("검색된 장소 개수:", len(documents))

        if documents:
            places_info = ""
            for doc, meta in zip(documents, metadatas):
                places_info += f"장소명: {meta['name']}<br>카테고리: {meta['category']}<br>지역: {meta['region']}<br>설명: {doc}<br><br>"

            prompt = f"""
            너는 사용자에게 여행지 장소를 추천하는 친근한 챗봇이야.

            사용자가 다음과 같은 질문을 했어:
            "{user_question}"

            사용자가 선택한 필터:
            - 지역: {region}
            - 카테고리: {category}

            아래 장소 목록을 참고해서, 의미적으로 맞는 곳만 골라서 설명해줘.

            **카테고리에 따라 말투를 다르게 해줘**:
            - 쇼핑 → 친구한테 소개하듯이 신나고 활발하게.
            - 카페 → 감성적이고 부드러운 말투로.
            - 볼거리 → 흥미롭고 재미있는 느낌으로, 가벼운 농담도 넣어줘.

            **출력 형식**:
            - 장소마다 **제목(굵게)** + **1~2문단 설명**.
            - 장소마다 **줄바꿈을 <br> 태그로 처리**해서 HTML에서도 보기 좋게.
            - 너무 긴 설명은 피하고, 가독성 좋게.

            장소 목록:<br><br>
            {places_info}
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            print("GPT 응답:", response)

            answer = response.choices[0].message.content
            answer = answer.replace("1.", "<br><br>🛍 1.").replace("2.", "<br><br>🛍 2.").replace("3.", "<br><br>🛍 3.").replace("4.", "<br><br>🛍 4.")

            # 추가 줄바꿈 처리 (혹시 GPT가 <br> 빼먹었을 경우 대비)
            answer = answer.replace("\n\n", "<br><br>").replace("\n", "<br>")

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
