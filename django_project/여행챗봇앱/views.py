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

def is_recommendation_request(question):
    check_prompt = f"""
    아래 사용자 질문이 '장소 추천 요청'인지 판단해줘.
    - 맞으면 "true", 아니면 "false"만 출력해.
    
    사용자 질문:
    "{question}"
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": check_prompt}]
    )

    return "true" in response.choices[0].message.content.lower()

def is_follow_up_question(question, chat_history):
    history = ""
    for q, a in chat_history[-3:]:  # 최근 3개만 참조
        history += f"사용자: {q}\n챗봇: {a}\n"

    check_prompt = f"""
    다음 사용자 질문은 이전 대화의 연장선인지 판단해줘.
    - 연속된 주제라면 "true", 아니면 "false"만 출력해.

    이전 대화:
    {history}

    현재 질문:
    "{question}"
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": check_prompt}]
    )

    return "true" in response.choices[0].message.content.lower()


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

        is_recommend = is_recommendation_request(user_question)
        is_follow_up = is_follow_up_question(user_question, chat_history)

        # 🔄 이전 장소 재활용 판단
        use_last_places = False
        places_info = ""
        last_info = request.session.get("last_places_info")

        if not is_recommend and is_follow_up and last_info:
                places_info = last_info
                use_last_places = True
                print("🔄 이전 장소 목록 재활용 중!")
        else:
            print("🧠 새 쿼리 실행 중!")
            use_last_places = False

        if not use_last_places:
            print("🧠 새 쿼리 실행 중!")
            query_embedding = model.encode(["query: " + user_question])
            filters = {}
            if category:
                filters["category"] = category  # 🧼 이게 가장 직관적이고 깔끔함

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=10,
                where=filters
            )

            documents = results['documents'][0] if results['documents'][0] else []
            metadatas = results['metadatas'][0] if results['metadatas'][0] else []

            print("검색된 장소 개수:", len(documents))

            if documents:
                for doc, meta in zip(documents, metadatas):
                    places_info += f"장소명: {meta['name']}<br>카테고리: {meta['category']}<br>지역: {meta['region']}<br>설명: {doc}<br><br>"

                if is_recommend:
                    request.session["last_places_info"] = places_info
                    print("✅ 장소 추천 질문으로 인식됨 → 장소 목록 세션 저장됨!")
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
        else:
            print("🔄 이전 장소 목록 재활용 중!")
            places_info = last_info

        # 💬 GPT 프롬프트 준비
        recent_history = chat_history[-5:]

        chat_context = ""
        for past_q, past_a in recent_history:
            chat_context += f"사용자: {past_q}\n챗봇: {past_a}\n"

        prompt_intro = ""
        if use_last_places:
            prompt_intro = """
            이 질문은 앞서 추천했던 장소들을 기준으로 이어지는 질문이야.
            아래 장소 목록은 그때 추천했던 장소들이고,
            이번 질문은 **반드시 이 목록 중에서만** 골라야 해.
            절대 새 장소를 추천하지 마!
            """

        prompt = f"""
        너는 사용자에게 여행지 장소를 추천하는 친근한 챗봇이야.

        다음은 지금까지 사용자와 나눈 대화 기록이야:
        {chat_context}

        사용자가 지금 이렇게 질문했어:
        "{user_question}"

        {prompt_intro}

        이 질문은 위의 대화 맥락을 바탕으로 이어지는 내용일 수도 있어.
        → 그러니까 꼭 이전 대화 내용을 참고해서 답변해줘!

        사용자가 설정한 조건:
        - 지역: {region}
        - 카테고리: {category}

        아래는 추천에 참고할 수 있는 장소 목록이야:

        {places_info}

        **설명 방식**:
        - 추천 개수를 명시했다면 해당 개수만큼!
        - 명시 안 했다면 3~5개만!
        - 카테고리에 따라 말투도 다르게!
        - 쇼핑: 친구처럼 발랄하게
        - 카페: 감성적으로
        - 문화시설: 재밌게, 농담도 좀 섞어서!
        - 줄바꿈은 <br> 태그로!
        - 너무 길지 않게, 가독성 있게!

        **⚠️ 주의사항**:
        - 반드시 위의 장소 목록 중에서만 골라야 해!
        - 목록에 없는 장소는 절대 추천하지 마!
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        print("GPT 응답:", response)

        answer = response.choices[0].message.content
        answer = answer.replace("1.", "<br><br>🛍 1.").replace("2.", "<br><br>🛍 2.")
        answer = answer.replace("3.", "<br><br>🛍 3.").replace("4.", "<br><br>🛍 4.")
        answer = answer.replace("\n\n", "<br><br>").replace("\n", "<br>")

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
