import os
import random
import openai
from dotenv import load_dotenv
from django.shortcuts import render
from tavily import TavilyClient

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = TavilyClient(api_key=TAVILY_API_KEY)

def chatbot_view(request):
    answers = []  # 여러 개의 답변을 담을 리스트

    if request.method == "POST":
        user_input = request.POST.get("question")

        if user_input:
            result = client.search(query=user_input)
            print("Tavily 결과:", result)

            if result.get("answer"):
                answers.append(result["answer"])

            elif result.get("results"):
                # score 기준 정렬 후 instagram.com 도메인만 필터링
                sorted_results = sorted(result["results"], key=lambda r: r.get("score", 0), reverse=True)
                wanted_results = [
                    r for r in sorted_results
                    if "naver.com" or "tistory.com" in r.get("url", "") and r.get("score", 0) >= 0.2
                ][:5]

                for res in wanted_results:
                    content = res.get("content", "").strip()
                    url = res.get("url", "").strip()

                    if content:
                        # 링크가 있을 경우 함께 출력
                        if url:
                            answers.append(f"{content}\n👉 [출처 보기]({url})")
                        else:
                            answers.append(content)

            if not answers:
                answers = ["관련 정보를 찾지 못했습니다."]

    # GET 요청 처리
    return render(request, "chatbot/chat.html", {"answers": answers})