from django.shortcuts import render
from sentence_transformers import SentenceTransformer  # 문장 임베딩을 위한 라이브러리
import chromadb  # ChromaDB 라이브러리: 벡터 저장소에 연결하기 위해 사용
from openai import OpenAI  # OpenAI API 호출을 위한 라이브러리
import os
from dotenv import load_dotenv  # .env 파일에서 환경변수를 로드하기 위해 사용
from django.conf import settings
from .tripadvisor_3_reviews import fetch_top3_reviews, summarize_reviews_openai  # TripAdvisor 관련 함수 임포트

# =============================================================================
# 1. ChromaDB 경로 설정 및 초기화
# =============================================================================
# 프로젝트의 상위 디렉토리 기준으로 "chroma_db2" 디렉토리 경로를 지정합니다.
chroma_db_path = os.path.join(settings.BASE_DIR.parent, "chroma_db2")
print("🔥 지금 연결된 ChromaDB 경로:", chroma_db_path)

# =============================================================================
# 2. 환경변수 로드
# =============================================================================
# .env 파일을 로드하여 OPENAI_API_KEY 등 민감 정보를 환경변수로 불러옵니다.
# 이는 코드 상에 API 키를 직접 노출하지 않기 위한 중요한 보안 조치입니다.
load_dotenv(dotenv_path=os.path.join(settings.BASE_DIR.parent, ".env"))

# =============================================================================
# 3. OpenAI 클라이언트 생성
# =============================================================================
# 환경변수에서 OPENAI_API_KEY를 가져와 OpenAI 클라이언트를 초기화합니다.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# =============================================================================
# 4. ChromaDB 연결 및 컬렉션 설정
# =============================================================================
# ChromaDB의 PersistentClient를 생성하여 지정된 경로에 연결합니다.
# 'places'라는 이름의 컬렉션을 가져오거나(해당 컬렉션이 없으면 생성) 연결합니다.
chroma_client = chromadb.PersistentClient(path=chroma_db_path)
collection = chroma_client.get_or_create_collection(name="places")

# =============================================================================
# 5. 문장 임베딩 모델 초기화
# =============================================================================
# 사용자 질문과 장소 설명 간의 유사도 측정을 위해 SentenceTransformer 모델을 로드합니다.
model = SentenceTransformer("intfloat/e5-large-v2")


def summarize_place_and_reviews(place_name, place_desc, reviews, openai_client):
    """
    장소 이름(place_name), 장소 설명(place_desc) 및 해당 장소에 대한 리뷰 목록(reviews)을
    GPT 모델을 통해 간결하고 핵심적인 한글 요약문으로 변환합니다.
    
    매개변수:
      - place_name: 추천할 여행지의 이름
      - place_desc: 해당 여행지에 대한 텍스트 설명
      - reviews: 장소에 대한 리뷰가 담긴 문자열 리스트
      - openai_client: OpenAI API 클라이언트 객체
      
    처리 과정:
      1. 리뷰 리스트를 하나의 문자열로 결합합니다.
      2. 장소 설명과 리뷰들을 포함하는 프롬프트를 생성합니다.
      3. GPT 모델(gpt-3.5-turbo)을 호출하여 해당 프롬프트에 따른 요약문을 생성합니다.
      4. 생성된 텍스트(요약문)를 반환합니다.
    """
    # 리스트형태의 리뷰들을 개행 문자로 결합
    joined_reviews = "\n".join(reviews)
    prompt = (
        f"다음은 여행지 '{place_name}'에 대한 설명과 실제 방문자 리뷰입니다.\n\n"
        f"[장소 설명]\n{place_desc}\n\n"
        f"[리뷰]\n{joined_reviews}\n\n"
        f"설명과 리뷰를 모두 참고해서 핵심만 간결하게 한글로 요약해줘."
    )
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",  # 요약 생성을 위한 모델 선택
        messages=[
            # 시스템 메세지: 프롬프트를 받는 역할을 명확히 합니다.
            {"role": "system", "content": "당신은 여행지 정보 요약 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,          # 반환될 최대 토큰 수 설정
        temperature=0.5,         # 생성 결과의 다양성을 조정 (낮을수록 예측에 가깝게 생성)
    )
    # 응답 메시지의 첫 번째 내용을 추출 후 공백 제거하여 반환
    return response.choices[0].message.content.strip()


def is_recommendation_request(question):
    """
    사용자가 입력한 질문이 새로운 장소 추천 요청인지 확인합니다.
    
    처리 과정:
      1. 질문 내용을 포함한 판단 요청 프롬프트를 생성합니다.
      2. GPT 모델(gpt-4o)을 사용하여 "true" 또는 "false"만 출력하도록 요청합니다.
      3. 응답 받은 문자열에 "true"가 포함되어 있으면 추천 요청(True)를 반환하고,
         그렇지 않으면 False를 반환합니다.
    """
    check_prompt = f"""
    아래 사용자 질문이 '장소 추천 요청'인지 판단해줘.
    - 맞으면 "true", 아니면 "false"만 출력해.
    
    사용자 질문:
    "{question}"
    """

    response = client.chat.completions.create(
        model="gpt-4o",  # 추천 요청 여부 판단에 적합한 모델 호출
        messages=[{"role": "user", "content": check_prompt}]
    )

    # 결과 문자열에 "true" 포함 여부를 소문자로 비교하여 반환
    return "true" in response.choices[0].message.content.lower()


def is_follow_up_question(question, chat_history):
    """
    현재 사용자 질문이 이전 대화(최근 3개 기록)를 기반으로 한 후속 질문인지 판단합니다.
    
    처리 과정:
      1. 최근 3개 대화 기록(사용자 질문 + 챗봇 응답)을 결합하여 대화 맥락을 구성합니다.
      2. 해당 대화 맥락과 현재 질문을 포함한 판단 요청 프롬프트 메시지를 생성합니다.
      3. GPT 모델(gpt-4o)을 호출하여 "true" 혹은 "false"로 판단한 결과를 반환받습니다.
    """
    history = ""
    # 최근 3개의 대화 기록만 활용하여 대화 맥락 문자열 생성
    for q, a in chat_history[-3:]:
        history += f"사용자: {q}\n챗봇: {a}\n"

    check_prompt = f"""
    다음 사용자 질문은 이전 대화 내용(특히 장소 추천 결과)을 바탕으로 한 후속 질문인지 판단해줘.
    - 예: "그중에 하나 골라줘", "조용한 곳은?", "카페는 있어?" 같은 질문은 연속된 대화야.
    - 만약 명확히 새로운 주제라면 "false", 이어지는 질문이라면 "true"만 출력해.

    이전 대화:
    {history}

    현재 질문:
    "{question}"
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": check_prompt}]
    )
    # 응답 결과에서 "true" 포함 여부로 후속 질문이면 True 반환
    return "true" in response.choices[0].message.content.lower()


def chatbot_view(request):
    """
    Django의 HTTP 요청을 처리하는 뷰 함수로, 여행 챗봇의 주요 로직을 담당합니다.
    
    동작 순서:
      1. ChromaDB에서 장소 메타데이터를 읽어와 사용자가 선택 가능한 "지역"과 "카테고리" 목록을 구성합니다.
      2. 사용자 세션에서 대화 이력을 초기화(또는 불러오기)하여 대화 내용을 유지합니다.
      3. POST 요청인 경우, 사용자가 보낸 질문과 선택 조건(지역, 카테고리)을 추출합니다.
      4. 사용자 질문이 신규 추천 요청인지 아니면 후속 질문인지를 판단합니다.
         - 신규 요청이면 ChromaDB에서 관련 장소들을 검색하고,
         - 후속 질문이면 세션에 저장된 이전 추천 목록을 재활용합니다.
      5. 신규 요청의 경우:
         a. 문장 임베딩을 통해 사용자의 질문을 벡터화합니다.
         b. 선택된 카테고리에 따라 필터를 적용하여 ChromaDB에서 최대 20개 결과를 검색합니다.
         c. 중복된 장소를 제거한 후 최대 5개의 고유한 장소를 선택합니다.
         d. 각 장소에 대해 TripAdvisor API를 호출하여 상위 3개 리뷰를 가져오고,
            GPT를 호출하여 장소 설명과 리뷰의 요약문을 생성합니다.
         e. 생성된 추천 정보를 HTML 형식(줄바꿈 태그 포함)으로 누적 저장합니다.
      6. 전체 대화 이력(최대 5개 기록)과 추천 장소 목록 등 정보를 포함하는 최종 프롬프트를 만들어
         GPT 모델(gpt-4o)에 전달하고 최종 답변을 생성합니다.
      7. 생성된 답변을 HTML 포맷으로 가공 후, 대화 이력에 추가하고 최종 템플릿을 렌더링합니다.
      
    최종적으로 index.html 템플릿에는 다음 정보가 전달됩니다:
      - answer: 최종 생성된 답변 (HTML 포맷 적용)
      - user_question: 사용자가 입력한 질문
      - location, category: 사용자가 선택한 지역 및 카테고리
      - chat_history: 누적된 대화 기록 (후속 질문 판단용)
      - typing: 로딩 중임을 나타내는 상태 값
      - location_list, category_list: 선택 가능한 지역 및 카테고리 목록
    """
    # ChromaDB 컬렉션에서 모든 장소의 메타데이터 불러오기
    all_places = collection.get(include=["metadatas"])
    # 메타데이터로부터 장소의 "location" 값을 추출 후 중복 제거 및 정렬
    all_locations = sorted(set(meta["location"] for meta in all_places["metadatas"] if "location" in meta))
    # "category" 값도 동일하게 추출하여 정렬합니다.
    all_categories = sorted(set(meta["category"] for meta in all_places["metadatas"] if "category" in meta))

    answer = ""
    user_question = ""
    location = ""
    category = ""

    # 세션에 대화 기록이 없다면, 초기화합니다.
    if not hasattr(request, '_session_initialized'):
        request.session['chat_history'] = []
        request._session_initialized = True

    # 세션에 저장된 대화 이력을 가져옵니다. (없으면 빈 리스트 사용)
    chat_history = request.session.get('chat_history', [])
    typing = False

    if request.method == "POST":
        # POST 요청에서 사용자 입력(질문, 지역, 카테고리)을 추출합니다.
        user_question = request.POST.get("question")
        location = request.POST.get("location")
        category = request.POST.get("category")

        print("사용자 질문:", user_question)
        print("선택한 지역:", location)
        print("선택한 카테고리:", category)

        # 응답 처리 중임을 나타내는 플래그 설정 (예: 로딩 애니메이션)
        typing = True

        # 사용자의 질문이 "신규 장소 추천"인지 확인하기 위해 GPT 모델 호출.
        is_recommend = is_recommendation_request(user_question)
        # 최근 대화 기록(최대 3개) 기반으로 후속 질문 여부도 판단합니다.
        is_follow_up = is_follow_up_question(user_question, chat_history)

        # 이전에 계산된 추천 장소 정보가 세션에 저장되어 있는지 확인
        use_last_places = False
        places_info = ""
        last_info = request.session.get("last_places_info")

        if not is_recommend and is_follow_up and last_info:
            # 후속 질문이고 이전 추천 정보가 있다면, 재활용합니다.
            places_info = last_info
            use_last_places = True
            print("🔄 이전 장소 목록 재활용 중!")
        else:
            print("🧠 새 쿼리 실행 중!")
            use_last_places = False

        if not use_last_places:
            # 사용자 질문을 벡터로 변환하기 위해 문장 임베딩 수행.
            query_embedding = model.encode(["query: " + user_question])
            filters = {}
            if category:
                filters["category"] = category  # 입력된 카테고리에 따른 필터 적용

            # ChromaDB 컬렉션에서 관련 장소를 최대 20개 검색합니다.
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=20,
                where=filters
            )
            # 결과에서 문서와 관련 메타데이터를 각각 추출
            documents = results['documents'][0] if results['documents'][0] else []
            metadatas = results['metadatas'][0] if results['metadatas'][0] else []
            print("검색된 장소 개수:", len(documents))

            if documents:
                # 중복된 장소명을 제거 후, 최대 5개의 고유한 장소 선택
                unique_places = {}
                for doc, meta in zip(documents, metadatas):
                    place_name = meta['name']
                    if place_name not in unique_places:
                        unique_places[place_name] = (doc, meta)
                selected_places = list(unique_places.items())[:5]

                # 검색 결과가 3개 미만이면, 추천 결과 부족 메시지를 전달하고 종료
                if len(selected_places) < 3:
                    answer = "추천할 만한 장소가 충분히 검색되지 않았어요. 다른 조건으로 다시 시도해 주세요!"
                    chat_history.append((user_question, answer))
                    request.session['chat_history'] = chat_history
                    typing = False
                    return render(request, "index.html", {
                        "answer": answer,
                        "user_question": user_question,
                        "location": location,
                        "category": category,
                        "chat_history": chat_history,
                        "typing": typing,
                        "location_list": all_locations,
                        "category_list": all_categories,
                    })

                # 각 고유 장소에 대해 TripAdvisor API를 호출하여 리뷰를 가져오고, 요약 생성
                for place_name, (doc, meta) in list(unique_places.items())[:5]:
                    review_text = ""
                    try:
                        # fetch_top3_reviews 함수: 해당 장소의 상위 3개 리뷰를 반환
                        trip_reviews = fetch_top3_reviews(place_name, os.getenv("TRIPADVISOR_API_KEY"))
                        # 장소 설명과 리뷰들을 합쳐 GPT 모델을 통해 요약문 생성
                        review_summary = summarize_place_and_reviews(place_name, doc, trip_reviews, client)
                        review_text = f"🌍 요약: {review_summary}"  # 요약문 포맷 적용
                    except Exception as e:
                        print(f"리뷰 요약 실패 - {place_name}: {e}")
                        # 예외 발생 시, 리뷰 정보는 없음을 명시하면서 장소 설명만 출력하도록 함
                        review_text = f"설명: {doc}<br>🌍 리뷰 요약: (리뷰 정보 없음)"
                    
                    # 각 장소의 상세 정보를 HTML 형식(줄바꿈 태그 포함)으로 누적
                    places_info += (
                        f"장소명: {place_name}<br>"
                        f"카테고리: {meta['category']}<br>"
                        f"지역: {meta['location']}<br>"
                        f"{review_text}<br><br>"
                    )

                # 신규 장소 추천 요청인 경우, 생성된 추천 결과를 세션에 저장
                if is_recommend:
                    request.session["last_places_info"] = places_info
                    print("✅ 장소 추천 질문으로 인식됨 → 장소 목록 세션 저장됨!")
            else:
                # 검색 결과가 없을 경우 처리: 사용자에게 알림을 보내고 대화 이력에 추가
                answer = "조건에 맞는 장소를 찾을 수 없습니다."
                chat_history.append((user_question, answer))
                request.session['chat_history'] = chat_history
                typing = False
                return render(request, "index.html", {
                    "answer": answer,
                    "user_question": user_question,
                    "location": location,
                    "category": category,
                    "chat_history": chat_history,
                    "typing": typing
                })
        else:
            print("🔄 이전 장소 목록 재활용 중!")
            places_info = last_info

        # ---------------------------------------------------------------------------
        # 최근 대화 이력을 기반으로 GPT 모델에 전달할 대화 맥락(chat_context)을 구성합니다.
        # 여기서는 최대 최근 5개 대화 기록을 사용합니다.
        # ---------------------------------------------------------------------------
        recent_history = chat_history[-5:]
        chat_context = ""
        for past_q, past_a in recent_history:
            chat_context += f"사용자: {past_q}\n챗봇: {past_a}\n"

        # 후속 질문인 경우, GPT에게 이전 추천 목록을 반드시 재활용하도록 지시하는 메시지를 추가합니다.
        prompt_intro = ""
        if use_last_places:
            prompt_intro = """
            이 질문은 앞서 추천했던 장소들을 기준으로 이어지는 질문이야.
            아래 장소 목록은 그때 추천했던 장소들이고,
            이번 질문은 **반드시 이 목록 중에서만** 골라야 해.
            절대 새 장소를 추천하지 마!
            """

        # ---------------------------------------------------------------------------
        # 최종 GPT 프롬프트 구성:
        # - 대화 기록(chat_context), 사용자 질문, 선택 조건, 추천 장소 목록 등 모든 정보를 포함합니다.
        # ---------------------------------------------------------------------------
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
        - 지역: {location}
        - 카테고리: {category}

        아래는 추천에 참고할 수 있는 장소 목록이야:

        {places_info}

        **설명 방식**:
        - 추천 개수를 명시했다면 해당 개수만큼!
        - 명시 안 했다면 3~5개만!
        - 카테고리에 따라 말투도 다르게!
        - 쇼핑: 친구처럼 발랄하게
        - 카페: 감성적으로
        - 문화시설: 재밌게, 농담도 섞어서!
        - 줄바꿈은 <br> 태그로!
        - 너무 길지 않게, 가독성 있게!

        **⚠️ 주의사항**:
        - 아래 장소 목록은 이전 질문에 기반해서 추천된 장소들이야.
        - 이번 질문은 이 목록을 기반으로 한 후속 질문이야.
        - 반드시 이 목록 안에서만 고르고, 목록 밖 장소는 절대 추천하지 마!
        """

        # ---------------------------------------------------------------------------
        # GPT 모델(gpt-4o)을 호출하여 최종 답변 생성
        # ---------------------------------------------------------------------------
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        print("GPT 응답:", response)

        # ---------------------------------------------------------------------------
        # GPT 응답 후처리:
        # - 번호 앞에 이모지를 추가하고,
        # - 여러 줄바꿈 문자를 HTML 태그(<br>)로 변환하여 가독성을 높임.
        # ---------------------------------------------------------------------------
        answer = response.choices[0].message.content
        answer = answer.replace("1.", "<br><br>🛍 1.").replace("2.", "<br><br>🛍 2.")
        answer = answer.replace("3.", "<br><br>🛍 3.").replace("4.", "<br><br>🛍 4.")
        answer = answer.replace("\n\n", "<br><br>").replace("\n", "<br>")

        # ---------------------------------------------------------------------------
        # 대화 이력 업데이트:
        # - 사용자 질문과 GPT 답변을 쌍으로 저장하여 이후 후속 질문 판단 및 대화 기록에 활용.
        # ---------------------------------------------------------------------------
        chat_history.append((user_question, answer))
        request.session['chat_history'] = chat_history
        typing = False

    # =====================================================================
    # GET 요청 혹은 POST 응답 후 최종 HTML 템플릿(index.html) 렌더링
    # =====================================================================
    return render(request, "index.html", {
        "answer": answer,
        "user_question": user_question,
        "location": location,
        "category": category,
        "chat_history": chat_history,
        "typing": typing,
        "location_list": all_locations,
        "category_list": all_categories,
    })
