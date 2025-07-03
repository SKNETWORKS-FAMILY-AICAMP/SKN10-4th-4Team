---
marp: true
theme: default
paginate: true
title: 여행지 추천 챗봇 발표
---

# ✨ 여행지 추천 챗봇  
_TripAdvisor 리뷰 기반 LLM 요약 서비스_

---

## 🏆 프로젝트 개요

- 자연어 질문에 맞는 여행지 추천
- 실제 방문자 리뷰 + LLM 요약으로 신뢰성 강화
- 챗봇 UI, 지역/카테고리 필터, 대화 이력 제공

---

## 🛠️ 기술 스택

- **Backend**: Django, Python
- **AI/Embedding**: OpenAI GPT-3.5, Sentence Transformers
- **DB/Vector Search**: ChromaDB
- **Frontend**: HTML5, CSS3
- **API**: TripAdvisor, OpenAI

---

## 🗂️ 폴더 구조

```
django_project/
├── 여행챗봇앱/
│   ├── templates/
│   │   └── index.html
│   ├── views.py
│   ├── tripadvisor_3_reviews.py
│   └── ...
├── manage.py
├── requirements.txt
└── ...
```

---

## ⚙️ 설치 및 실행 가이드

1. **프로젝트 세팅**
   ```bash
git clone <레포주소>
cd <프로젝트폴더>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
   ```

2. **환경 변수 구성**
   - `.env` 파일 생성 (OPENAI_API_KEY, TRIPADVISOR_API_KEY 등)
---
3. **ChromaDB 준비**
   - 루트에 `chroma_db` 폴더 필요

4. **서버 실행**
   ```bash
python manage.py runserver
   ```

---

## 🎤 시연 시나리오 ①  
자연어 질문 → 여행지 추천

- 사용자가 입력:  
  "서울에서 볼거리 추천해줘!"
- 지역 / 카테고리 필터 설정 
` 서울 / 문화시설 `
- 챗봇이 질문을 이해하고  
  관련 여행지 + 요약 정보 제공

---

## 🎤 시연 시나리오 ②  
TripAdvisor 리뷰 요약 강조

- 각 여행지마다 TripAdvisor 리뷰 3건 수집
- LLM으로 실제 경험 기반 요약
- 단순 정보 제공과 차별화된 신뢰성

---

<img src="chatbot_ui.png" alt="챗봇 시연 이미지" width="750" style="display:block; margin:0 auto;" />

---

## 💡 핵심 포인트

- **실제 리뷰 기반 요약**  
  단순 정보가 아닌, 실제 방문자 리뷰를 LLM이 요약  
  → 신뢰도와 차별성 확보

- **자연어 질문 처리**  
  자유로운 질문에도 유연하게 대응

- **확장성/코드 품질**  
  실무 수준의 설계, 다양한 추천 로직 확장 가능

---

## 📎 참고 사항

- 사용 API:  
  OpenAI, TripAdvisor

- 필수 파일/디렉토리:  
  `.env`, `chroma_db/`

---

# 감사합니다 🙌  
질문 있으신가요?
