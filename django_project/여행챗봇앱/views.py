# from django.shortcuts import render
# from sentence_transformers import SentenceTransformer
# import chromadb
# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# from django.conf import settings
# from .tripadvisor_3_reviews import fetch_top3_reviews

# # 🔥 chroma_db 경로 → 프로젝트 루트 기준
# chroma_db_path = os.path.join(settings.BASE_DIR.parent, "chroma_db")

# print("🔥 지금 연결된 ChromaDB 경로:", chroma_db_path)

# # .env 파일 로드 (프로젝트 루트 기준 상대경로)
# env_path = os.path.join(settings.BASE_DIR, "..", ".env")
# load_dotenv(dotenv_path=os.path.abspath(env_path))

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# chroma_client = chromadb.PersistentClient(path=chroma_db_path)
# collection = chroma_client.get_or_create_collection(name="places")

# model = SentenceTransformer("intfloat/e5-large-v2")

# def summarize_place_and_reviews(place_name, place_desc, reviews, openai_client):
#     joined_reviews = " ".join(reviews)
#     prompt = (
#         f"다음은 여행지 '{place_name}'에 대한 설명과 실제 방문자 리뷰입니다. "
#         f"설명과 리뷰를 모두 참고하여, 핵심만 간결하게 한글로 요약해 주세요.\n\n"
#         f"[장소 설명]\n{place_desc}\n\n[리뷰]\n{joined_reviews}\n\n요약:")
#     response = openai_client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "당신은 여행지 정보 요약 전문가입니다."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=300,
#         temperature=0.5,
#     )
#     return response.choices[0].message.content.strip()

# def chatbot_view(request):
#     answer = ""
#     user_question = ""
#     region = ""
#     category = ""

#     # ⭐ 서버 새로 시작할 때마다 세션 초기화!
#     if not hasattr(request, '_session_initialized'):
#         request.session['chat_history'] = []
#         request._session_initialized = True

#     chat_history = request.session.get('chat_history', [])

#     typing = False

#     if request.method == "POST":
#         user_question = request.POST.get("question")
#         region = request.POST.get("region")
#         category = request.POST.get("category")

#         print("사용자 질문:", user_question)
#         print("선택한 지역:", region)
#         print("선택한 카테고리:", category)

#         typing = True

#         query_embedding = model.encode(["query: " + user_question])

#         filters = {}
#         if category:
#             filters["category"] = category

#         results = collection.query(
#             query_embeddings=query_embedding,
#             n_results=5,
#             where=filters
#         )

#         documents = results['documents'][0] if results['documents'][0] else []
#         metadatas = results['metadatas'][0] if results['metadatas'][0] else []

#         print("검색된 장소 개수:", len(documents))

#         if documents:
#             summaries = []
#             unique_places = {}
#             for doc, meta in zip(documents, metadatas):
#                 place_name = meta['name']
#                 if place_name not in unique_places:
#                     unique_places[place_name] = (doc, meta)

#             for place_name, (doc, meta) in list(unique_places.items())[:3]:  # 최대 3개만
#                 place_desc = doc
#                 try:
#                     reviews = fetch_top3_reviews(place_name, os.getenv("TRIPADVISOR_API_KEY"))
#                 except Exception as e:
#                     reviews = []
#                     print(f"Tripadvisor 리뷰 가져오기 실패: {e}")

#                 if reviews:
#                     try:
#                         summary = summarize_place_and_reviews(place_name, place_desc, reviews, client)
#                     except Exception as e:
#                         summary = f"요약 실패: {e}"
#                 else:
#                     summary = f"{place_desc}<br><br>(리뷰를 가져올 수 없습니다.)"

#                 summaries.append(
#                     f"<b>{place_name}</b><br>{summary}<br><br>"
#                 )

#             answer = "<hr>".join(summaries)
#         else:
#             answer = "조건에 맞는 장소를 찾을 수 없습니다."

#         chat_history.append((user_question, answer))
#         request.session['chat_history'] = chat_history

#         typing = False

#     return render(request, "index.html", {
#         "answer": answer,
#         "user_question": user_question,
#         "region": region,
#         "category": category,
#         "chat_history": chat_history,
#         "typing": typing
#     })
from django.shortcuts import render
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv
from django.conf import settings
from tavily import TavilyClient

# 경로 및 환경변수 설정
chroma_db_path = os.path.join(settings.BASE_DIR.parent, "chroma_db")
load_dotenv(dotenv_path=os.path.join(settings.BASE_DIR.parent, ".env"))

# 클라이언트 설정
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

chroma_client = chromadb.PersistentClient(path=chroma_db_path)
collection = chroma_client.get_or_create_collection(name="places")
model = SentenceTransformer("intfloat/e5-large-v2")

def is_recommendation_request(question):
    prompt = f"""
    아래 사용자 질문이 '장소 추천 요청'인지 판단해줘.
    - 맞으면 "true", 아니면 "false"만 출력해.

    사용자 질문:
    "{question}"
    """
    res = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return "true" in res.choices[0].message.content.lower()

def is_follow_up_question(question, chat_history):
    history = ""
    for q, a in chat_history[-3:]:
        history += f"사용자: {q}\n챗봇: {a}\n"

    prompt = f"""
    다음 사용자 질문은 이전 대화 내용(특히 장소 추천 결과)을 바탕으로 한 후속 질문인지 판단해줘.
    - 예: "그중에 하나 골라줘", "조용한 곳은?", "카페는 있어?" 같은 질문은 연속된 대화야.
    - 명확히 새로운 주제라면 "false", 이어지는 질문이라면 "true"만 출력해.

    이전 대화:
    {history}

    현재 질문:
    "{question}"
    """
    res = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return "true" in res.choices[0].message.content.lower()

def chatbot_view(request):
    answer = ""
    user_question = ""
    region = ""
    category = ""
    blog_reviews = []

    if not hasattr(request, '_session_initialized'):
        request.session['chat_history'] = []
        request._session_initialized = True

    chat_history = request.session.get('chat_history', [])
    typing = False

    if request.method == "POST":
        user_question = request.POST.get("question")
        region = request.POST.get("region")
        category = request.POST.get("category")
        typing = True

        is_recommend = is_recommendation_request(user_question)
        is_follow_up = is_follow_up_question(user_question, chat_history)

        # 🔄 장소 목록 재활용 여부
        use_last_places = False
        places_info = ""
        last_info = request.session.get("last_places_info")

        if not is_recommend and is_follow_up and last_info:
            places_info = last_info
            use_last_places = True
        else:
            query_embedding = model.encode(["query: " + user_question])
            filters = {}
            if category:
                filters["category"] = category

            results = collection.query(query_embeddings=query_embedding, n_results=10, where=filters)
            documents = results['documents'][0] if results['documents'][0] else []
            metadatas = results['metadatas'][0] if results['metadatas'][0] else []

            if documents:
                for doc, meta in zip(documents, metadatas):
                    places_info += f"장소명: {meta['name']}<br>카테고리: {meta['category']}<br>지역: {meta['region']}<br>설명: {doc}<br><br>"

                if is_recommend:
                    request.session["last_places_info"] = places_info
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

        # GPT 대화 컨텍스트
        recent_history = chat_history[-5:]
        chat_context = "".join([f"사용자: {q}\n챗봇: {a}\n" for q, a in recent_history])

        prompt_intro = ""
        if use_last_places:
            prompt_intro = """
            이 질문은 앞서 추천했던 장소들을 기준으로 이어지는 질문이야.
            아래 장소 목록은 그때 추천했던 장소들이고,
            이번 질문은 **반드시 이 목록 중에서만** 골라야 해.
            """

        prompt = f"""
        너는 사용자에게 여행지 장소를 추천하는 친근한 챗봇이야.

        다음은 사용자와 나눈 최근 대화야:
        {chat_context}

        사용자가 이렇게 질문했어:
        "{user_question}"

        {prompt_intro}

        사용자가 선택한 조건:
        - 지역: {region}
        - 카테고리: {category}

        참고할 장소 목록:
        {places_info}

        설명 방식:
        - 추천 개수를 명시했다면 그 수만큼!
        - 명시 없으면 3~5개 추천!
        - 카테고리에 따라 말투 변형
        - 줄바꿈은 <br> 태그 사용
        - 너무 길지 않게!

        절대 장소 목록 외 장소 추천 금지!
        """

        res = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = res.choices[0].message.content
        answer = answer.replace("1.", "<br><br>🛍 1.").replace("2.", "<br><br>🛍 2.")
        answer = answer.replace("3.", "<br><br>🛍 3.").replace("\n\n", "<br><br>").replace("\n", "<br>")

        chat_history.append((user_question, answer))
        request.session['chat_history'] = chat_history

        # 💬 Tavily 블로그 리뷰 추가
        try:
            tavily_result = tavily_client.search(query=user_question)
            sorted_results = sorted(tavily_result.get("results", []), key=lambda r: r.get("score", 0), reverse=True)
            blog_links = [
                r for r in sorted_results
                if any(site in r.get("url", "") for site in ["blog.naver.com", "tistory.com", "tripadvisor.co.kr"])
                and r.get("score", 0) >= 0.2
            ][:3]

            for res in blog_links:
                content = res.get("content", "").strip()
                url = res.get("url", "").strip()
                if content and url:
                    blog_reviews.append(f"{content}<br>👉 <a href='{url}' target='_blank'>출처 보기</a>")
        except Exception as e:
            print("Tavily 오류:", e)

        typing = False

    return render(request, "index.html", {
        "answer": answer,
        "user_question": user_question,
        "region": region,
        "category": category,
        "chat_history": chat_history,
        "typing": typing,
        "blog_reviews": blog_reviews
    })
