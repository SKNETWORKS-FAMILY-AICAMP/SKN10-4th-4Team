from sentence_transformers import SentenceTransformer
import chromadb

# 🔥 ChromaDB 연결
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="places")



# 🔥 e5-large-v2 모델
model = SentenceTransformer("intfloat/e5-large-v2")

# 🔥 데이터 미리보기 (peek 추가)
print("===== VectorDB 미리보기 (peek) =====")
print(collection.peek())
print("===================================")

# 🔥 사용자 질문 & 필터
user_question = "쇼핑몰 추천해줘"
region_filter = "서울특별시"
category_filter = "쇼핑"

# 🔥 질문 임베딩 (e5 형식 → "query: ..." 로 해야 성능 최고!)
query_embedding = model.encode(["query: " + user_question])

# 🔥 VectorDB 검색
# 🔥 필터 제거 → 의미 비슷한 장소 n_results 가져오기
results = collection.query(
    query_embeddings=query_embedding,
    n_results=10
)

# 🔥 결과 출력
if results['ids'][0]:
    print("🔎 추천 장소:")
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        print(f"▶ 장소명: {meta['name']}")
        print(f"   주소: {meta['region']}")
        print(f"   카테고리: {meta['category']}")
        print(f"   영업시간: {meta['open_time']}")
        print(f"   설명: {results['documents'][0][i]}")
        print("------------------------------------------------")
else:
    print("❗ 관련 장소를 찾을 수 없습니다.")
